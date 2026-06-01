# SPDX-License-Identifier: AGPL-3.0
"""
终末地伤害计算器 — PythonAnywhere 自动化部署脚本

一站式完成：构建前端 → 打包 zip → 上传 → 服务器部署 → 重载 Web App

配置 API Token 后，一条命令完成全部操作：
  python web/scripts/deploy_pythonanywhere.py --all

使用方法:
  python web/scripts/deploy_pythonanywhere.py --all         # 全自动：构建→打包→上传→部署→重载（需API Token）
  python web/scripts/deploy_pythonanywhere.py               # 构建 + 打包，输出 zip（手动上传部署）
  python web/scripts/deploy_pythonanywhere.py --zip-only    # 仅打包已有 dist/（跳过 npm run build）
  python web/scripts/deploy_pythonanywhere.py --help        # 查看完整帮助

首次使用:
  1. 在 PythonAnywhere 生成 API Token: Account → API Token → Create new token
  2. 在本地创建 ~/.pythonanywhere 配置文件 (见 --init-config)
  3. 或直接传参: --username wxhwwla --api-token xxxxx

注意事项:
  - 避免使用 PowerShell Compress-Archive（LZMA 不兼容 Linux unzip）
  - 脚本自动使用 Python zipfile 模块（ZIP_DEFLATED，兼容 Linux）
  - 自动处理 dist/dist/ 双层嵌套问题
"""
from __future__ import annotations

import argparse
import configparser
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
from zipfile import ZipFile, ZIP_DEFLATED

# ── 路径 ──────────────────────────────────────────────────────────────────────
_REPO_ROOT = Path(__file__).resolve().parents[2]
_FRONTEND_DIR = _REPO_ROOT / "web" / "frontend"
_DIST_DIR = _FRONTEND_DIR / "dist"
_SCRIPTS_DIR = _REPO_ROOT / "web" / "scripts"
_ZIP_PATH = _REPO_ROOT / "dist_pa.zip"
_ARKNIGHTS_PARSED_ZIP = _REPO_ROOT / "dist_arknights_parsed.zip"
_PA_UPLOAD_INTERVAL = 0.45  # Files API 限流，逐文件上传时的间隔（秒）
_CONFIG_PATH = Path.home() / ".pythonanywhere"

# ── PythonAnywhere API ────────────────────────────────────────────────────────
_PA_API = "https://www.pythonanywhere.com/api/v0/user/{username}/"
_PA_FILES_API = _PA_API + "files/path{path}"
_PA_RELOAD_API = _PA_API + "webapps/{domain}/reload/"
_PA_CONSOLE_API = _PA_API + "consoles/"

_DEFAULT_DOMAIN = "{username}.pythonanywhere.com"

# ── 配置读取 ────────────────────────────────────────────────────────────────────


def _load_config() -> dict:
    """读取 ~/.pythonanywhere 配置文件，返回 dict。"""
    config = {}
    ini = configparser.ConfigParser()
    if _CONFIG_PATH.exists():
        ini.read(str(_CONFIG_PATH), encoding="utf-8")
        section = "pythonanywhere"
        if ini.has_section(section):
            for key in ("username", "api_token", "project", "domain"):
                if ini.has_option(section, key):
                    config[key] = ini.get(section, key)
    # 环境变量覆盖
    for env_key, cfg_key in [("PA_USERNAME", "username"), ("PA_API_TOKEN", "api_token"),
                              ("PA_PROJECT", "project"), ("PA_DOMAIN", "domain")]:
        val = os.environ.get(env_key)
        if val:
            config[cfg_key] = val
    return config


# ── 阶段 1: 构建前端 ────────────────────────────────────────────────────────────


def _run_npm(args: list[str], cwd: Path) -> None:
    """跨平台执行 npm 命令。"""
    cmd = ["npm.cmd" if sys.platform == "win32" else "npm"] + args
    print(f"  $ {' '.join(cmd)}  (in {cwd.name})")
    result = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        print("  [ERR] npm 命令失败:")
        print(result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)
        print(result.stderr[-2000:] if len(result.stderr) > 2000 else result.stderr)
        sys.exit(1)


def _build_frontend() -> None:
    """执行 npm run build。"""
    print("\n[PACK] [阶段 1/4] 构建前端...")
    print(f"  目录: {_FRONTEND_DIR}")
    if not (_FRONTEND_DIR / "package.json").exists():
        print("  [ERR] 未找到 package.json，请确认路径正确")
        sys.exit(1)
    _run_npm(["install"], _FRONTEND_DIR)
    _run_npm(["run", "build"], _FRONTEND_DIR)
    if not _DIST_DIR.exists():
        print("  [ERR] 构建完成但 dist/ 目录未生成")
        sys.exit(1)
    js_files = list(_DIST_DIR.rglob("*.js"))
    print(f"  [OK] 构建完成: {len(js_files)} 个 JS 文件, {sum(f.stat().st_size for f in js_files) // 1024} KB")


# ── 阶段 2: 打包 zip ────────────────────────────────────────────────────────────


def _create_zip() -> None:
    """用 Python zipfile 创建兼容 Linux 的 zip（避免 LZMA 问题）。"""
    print("\n[PACK] [阶段 2/4] 打包 dist/...")
    if not _DIST_DIR.exists():
        print(f"  [ERR] dist/ 目录不存在: {_DIST_DIR}")
        print("  请先执行 npm run build，或使用 --zip-only 跳过构建")
        sys.exit(1)

    if _ZIP_PATH.exists():
        _ZIP_PATH.unlink()

    count = 0
    with ZipFile(str(_ZIP_PATH), "w", ZIP_DEFLATED) as zf:
        for fpath in sorted(_DIST_DIR.rglob("*")):
            if fpath.is_file():
                arcname = str(fpath.relative_to(_DIST_DIR)).replace("\\", "/")
                zf.write(str(fpath), arcname)
                count += 1
    zip_size = _ZIP_PATH.stat().st_size
    print(f"  [OK] 打包完成: {count} 个文件, {zip_size // 1024} KB")
    print(f"  [DOC] 输出: {_ZIP_PATH}")


# ── 阶段 3: 上传到 PythonAnywhere ────────────────────────────────────────────────


def _pa_file_url(username: str, remote_path: str) -> str:
    """Files API 路径须 URL 编码（干员 JSON 等中文文件名）。"""
    path = remote_path.replace("\\", "/")
    if not path.startswith("/"):
        path = "/" + path
    return _PA_FILES_API.format(username=username, path=quote(path, safe="/"))


def _upload_bytes_to_path(
    config: dict,
    remote_path: str,
    file_data: bytes,
    label: str,
    *,
    quiet: bool = False,
    max_retries: int = 6,
) -> bool:
    """通过 Files API 上传单个文件（含 429 重试）。"""
    username = config.get("username")
    token = config.get("api_token")
    if not username or not token:
        print(f"  [ERR] {label}: 未配置 API Token")
        return False

    url = _pa_file_url(username, remote_path)
    boundary = b"----pa-deploy-boundary"
    body_parts = [
        b"--" + boundary,
        b'Content-Disposition: form-data; name="content"; filename="upload.bin"',
        b"Content-Type: application/octet-stream",
        b"",
        file_data,
        b"--" + boundary + b"--",
    ]
    body_data = b"\r\n".join(body_parts)

    for attempt in range(max_retries):
        code, body = _pa_request(
            "POST", url, token,
            data=body_data,
            content_type=f"multipart/form-data; boundary={boundary.decode()}",
        )
        if code in (200, 201):
            if not quiet:
                print(f"  [OK] {label} → {remote_path}")
            return True
        if code == 429 and attempt + 1 < max_retries:
            wait = 2 + attempt
            print(f"  [WAIT] {label} 限流 (429)，{wait}s 后重试 ({attempt + 1}/{max_retries})...")
            time.sleep(wait)
            continue
        print(f"  [ERR] {label} HTTP {code}: {body[:300]}")
        return False
    return False


def _render_wsgi_content(config: dict) -> str:
    """按配置生成 WSGI 文件内容（勿使用 application = app）。"""
    username = config["username"]
    project = config.get("project", "calc-framework")
    venv = config.get("venv", project)
    src_path = _REPO_ROOT / "web" / "wsgi_pythonanywhere.py"
    if not src_path.is_file():
        raise FileNotFoundError(f"未找到 WSGI 模板: {src_path}")
    text = src_path.read_text(encoding="utf-8")
    text = re.sub(r'^PA_USERNAME = ".*"$', f'PA_USERNAME = "{username}"', text, count=1, flags=re.M)
    text = re.sub(r'^PA_PROJECT = ".*"$', f'PA_PROJECT = "{project}"', text, count=1, flags=re.M)
    text = re.sub(r'^PA_VENV = ".*"$', f'PA_VENV = "{venv}"', text, count=1, flags=re.M)
    return text


def _upload_wsgi(config: dict) -> None:
    """上传 WSGI 到 /var/www/（修复 missing argument 'send'）。"""
    print("\n[UP-WSGI] 上传 WSGI 入口（替换 application=app）...")
    username = config["username"]
    try:
        content = _render_wsgi_content(config).encode("utf-8")
    except FileNotFoundError as e:
        print(f"  [ERR] {e}")
        sys.exit(1)
    remote = f"/var/www/{username}_pythonanywhere_com_wsgi.py"
    if not _upload_bytes_to_path(config, remote, content, "WSGI"):
        print("  [WARN] WSGI 上传失败。请在 PA Bash 手动执行:")
        print(f"    cp ~/{config.get('project', 'calc-framework')}/web/wsgi_pythonanywhere.py {remote}")
        sys.exit(1)


def _upload_directory_tree(
    config: dict,
    local_root: Path,
    remote_base: str,
    *,
    suffixes: tuple[str, ...] = (".py", ".json"),
    skip_parts: frozenset[str] = frozenset({"tests", "__pycache__"}),
    label: str = "",
) -> tuple[int, int]:
    """递归上传目录下指定后缀文件。返回 (成功数, 失败数)。"""
    if not local_root.is_dir():
        print(f"  [SKIP] {label or local_root.name}: 本地目录不存在 {local_root}")
        return 0, 0

    remote_base = remote_base.rstrip("/") + "/"
    ok, err = 0, 0
    files = sorted(
        p for p in local_root.rglob("*")
        if p.is_file() and p.suffix in suffixes and not any(s in skip_parts for s in p.parts)
    )
    total = len(files)
    if label:
        print(f"  {label}: {total} 个文件 → {remote_base}")
    for i, fpath in enumerate(files, 1):
        rel = fpath.relative_to(local_root).as_posix()
        remote = remote_base + rel
        try:
            if _upload_bytes_to_path(config, remote, fpath.read_bytes(), rel, quiet=True):
                ok += 1
            else:
                err += 1
                print(f"  [ERR] 失败: {rel}")
        except Exception as e:
            err += 1
            print(f"  [ERR] 失败: {rel}: {e}")
        if total > 1:
            time.sleep(_PA_UPLOAD_INTERVAL)
        if total > 20 and i % 50 == 0:
            print(f"    ... {i}/{total}")
    print(f"  [{label or 'tree'}] {ok} 成功, {err} 失败")
    return ok, err


def _upload_arknights_parsed_zip(config: dict, home: str) -> None:
    """干员 JSON 打成 zip 一次上传（避免 422 次 API + 中文路径编码问题）。"""
    parsed = _REPO_ROOT / "tools" / "arknights_scout" / "output" / "parsed"
    if not parsed.is_dir():
        print("  [WARN] 未找到 tools/arknights_scout/output/parsed，干员列表将为空")
        return

    json_files = sorted(parsed.glob("*.json"))
    if not json_files:
        print("  [WARN] parsed/ 下无 JSON 文件")
        return

    print(f"  打包 {len(json_files)} 个干员 JSON → {_ARKNIGHTS_PARSED_ZIP.name} ...")
    if _ARKNIGHTS_PARSED_ZIP.exists():
        _ARKNIGHTS_PARSED_ZIP.unlink()
    with ZipFile(str(_ARKNIGHTS_PARSED_ZIP), "w", ZIP_DEFLATED) as zf:
        for fp in json_files:
            zf.write(str(fp), fp.name)

    remote_zip = f"{home}/tools/arknights_scout/arknights_parsed.zip"
    if not _upload_bytes_to_path(config, remote_zip, _ARKNIGHTS_PARSED_ZIP.read_bytes(), "arknights_parsed.zip"):
        print("  [ERR] 干员数据 zip 上传失败")
        return

    project = config.get("project", "calc-framework")
    print("  [DOC] 在 PA Bash 解压干员数据（更新干员库时执行一次）:")
    print(f"    cd ~/{project}/tools/arknights_scout/output")
    print("    rm -rf parsed && mkdir -p parsed && unzip -oq arknights_parsed.zip -d parsed")


def _upload_arknights_runtime(config: dict) -> None:
    """上传 games.arknights、适配器 DAG 与干员 JSON（PA 上 import 依赖）。"""
    print("\n[UP-AK] 上传明日方舟运行时...")
    username = config["username"]
    project = config.get("project", "calc-framework")
    home = f"/home/{username}/{project}"

    games_init = _REPO_ROOT / "games" / "__init__.py"
    if games_init.is_file():
        _upload_bytes_to_path(
            config, f"{home}/games/__init__.py", games_init.read_bytes(), "games/__init__.py",
        )

    _upload_directory_tree(
        config,
        _REPO_ROOT / "games" / "arknights",
        f"{home}/games/arknights",
        suffixes=(".py",),
        label="games/arknights",
    )
    _upload_directory_tree(
        config,
        _REPO_ROOT / "framework" / "adapters" / "arknights",
        f"{home}/framework/adapters/arknights",
        suffixes=(".py", ".json"),
        label="framework/adapters/arknights",
    )

    _upload_arknights_parsed_zip(config, home)


def _upload_donation_assets(config: dict) -> None:
    """上传捐赠二维码到 resources/donation/。"""
    donation_dir = _REPO_ROOT / "resources" / "donation"
    if not donation_dir.is_dir():
        return
    username = config["username"]
    project = config.get("project", "calc-framework")
    files = [p for p in donation_dir.iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")]
    if not files:
        print("\n[UP-DON] 跳过捐赠图片（resources/donation/ 无图片）")
        return
    print(f"\n[UP-DON] 上传 {len(files)} 个捐赠图片...")
    for fp in files:
        remote = f"/home/{username}/{project}/resources/donation/{fp.name}"
        _upload_bytes_to_path(config, remote, fp.read_bytes(), fp.name)


def _verify_deployment(config: dict) -> None:
    """重载后检查关键 API 是否返回 JSON（非 HTML）。"""
    domain = config.get("domain") or f"{config['username']}.pythonanywhere.com"
    print(f"\n[CHK] 验证 https://{domain} ...")
    time.sleep(4)
    checks = [
        (f"https://{domain}/api/health", '"status"'),
        (f"https://{domain}/api/layout", '"sections"'),
        (f"https://{domain}/api/arknights/operators", '"operators"'),
    ]
    ok = True
    for url, needle in checks:
        try:
            with urlopen(url, timeout=30) as resp:
                body = resp.read(800).decode("utf-8", errors="replace")
            if needle in body and not body.lstrip().startswith("<"):
                print(f"  [OK] {url}")
            else:
                print(f"  [FAIL] {url} 返回非预期内容: {body[:120]!r}")
                ok = False
        except Exception as e:
            print(f"  [FAIL] {url}: {e}")
            ok = False
    if not ok:
        print("\n  [HINT] 若仍报 missing argument 'send'，请打开 PA Web → WSGI configuration file")
        print("  确认路径为 /var/www/你的用户名_pythonanywhere_com_wsgi.py，且内容为 wsgi_pythonanywhere.py（无 application=app）")
    else:
        print("  [OK] API 正常，请 Ctrl+F5 刷新 /compute")


def _pa_request(method: str, url: str, token: str, data: bytes | None = None,
                content_type: str | None = None) -> tuple[int, str]:
    """向 PythonAnywhere API 发起请求。"""
    headers = {"Authorization": f"Token {token}"}
    if content_type:
        headers["Content-Type"] = content_type
    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req) as resp:
            return resp.status, resp.read().decode("utf-8")
    except HTTPError as e:
        body = e.read().decode("utf-8")[:500]
        return e.code, body
    except URLError as e:
        return -1, str(e)


def _upload_zip(config: dict) -> None:
    """通过 PythonAnywhere Files API 上传 dist.zip。"""
    print("\n[UP] [阶段 3/5] 上传 dist.zip 到 PythonAnywhere...")
    username = config.get("username")
    token = config.get("api_token")
    project = config.get("project", "calc-framework")
    if not username or not token:
        print("  [ERR] 未配置 PythonAnywhere 用户名或 API Token")
        print("  请通过 --username/--api-token 传参，或配置 ~/.pythonanywhere 文件")
        sys.exit(1)

    if not _ZIP_PATH.exists():
        print(f"  [ERR] 未找到 zip 文件: {_ZIP_PATH}")
        sys.exit(1)

    remote_path = f"/home/{username}/{project}/frontend/dist.zip"
    url = _pa_file_url(username, remote_path)

    # 检查 API 连通性（用 /cpu/ 端点验证）
    test_url = _PA_API.format(username=username) + "cpu/"
    code, body = _pa_request("GET", test_url, token)
    if code != 200:
        print(f"  [ERR] API 连接失败 ({code}): {body}")
        sys.exit(1)

    # 上传文件（使用 multipart/form-data）
    file_content = _ZIP_PATH.read_bytes()
    boundary = b"----pa-deploy-boundary"
    body_parts = [
        b"--" + boundary,
        b'Content-Disposition: form-data; name="content"; filename="dist.zip"',
        b"Content-Type: application/octet-stream",
        b"",
        file_content,
        b"--" + boundary + b"--",
    ]
    body_data = b"\r\n".join(body_parts)

    code, body = _pa_request(
        "POST", url, token,
        data=body_data,
        content_type=f"multipart/form-data; boundary={boundary.decode()}",
    )
    if code in (200, 201):
        print(f"  [OK] 上传成功: {remote_path}")
    else:
        print(f"  [ERR] 上传失败 ({code}): {body}")
        sys.exit(1)


# ── 阶段 4: 直接上传 dist 文件到服务器（避免 Console API 限制） ──────────────


def _upload_dist_files(config: dict) -> None:
    """将 dist/ 中的文件逐个直接上传到 PythonAnywhere 服务器。

    相比在服务器上解压 zip，本方案在本地解压后通过 Files API 逐个上传
    每个文件到正确的路径。避免了 Console API 限制。
    """
    print("\n[UP] [阶段 3/4] 上传前端文件到 dist/...")
    username = config.get("username")
    token = config.get("api_token")
    project = config.get("project", "calc-framework")
    if not username or not token:
        print("  [ERR] 未配置 API Token")
        sys.exit(1)

    if not _ZIP_PATH.exists():
        print(f"  [ERR] 未找到 zip 文件: {_ZIP_PATH}")
        sys.exit(1)

    dist_base = f"/home/{username}/{project}/web/frontend/dist/"

    count = 0
    errors = 0
    with ZipFile(str(_ZIP_PATH), "r") as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            arcname = info.filename.replace("\\", "/")
            remote_path = dist_base + arcname
            file_data = zf.read(info)

            url = _pa_file_url(username, remote_path)
            boundary = b"----pa-deploy-boundary"
            body_parts = [
                b"--" + boundary,
                f'Content-Disposition: form-data; name="content"; filename="{arcname}"'.encode(),
                b"Content-Type: application/octet-stream",
                b"",
                file_data,
                b"--" + boundary + b"--",
            ]
            body_data = b"\r\n".join(body_parts)
            code, body = _pa_request(
                "POST", url, token,
                data=body_data,
                content_type=f"multipart/form-data; boundary={boundary.decode()}",
            )
            if code in (200, 201):
                count += 1
                print(f"  [OK] {arcname} ({len(file_data)} bytes)")
            else:
                errors += 1
                print(f"  [WARN] {arcname}: HTTP {code} — 重试...")
                # 尝试创建父目录后重试
                if "/" in arcname:
                    parent = "/".join(arcname.split("/")[:-1])
                    dummy_url = _pa_file_url(username, f"{dist_base}{parent}/.keep")
                    _pa_request("POST", dummy_url, token, data=b"--boundary\r\n...",
                                content_type="multipart/form-data; boundary=boundary")
                retry_code, _ = _pa_request(
                    "POST", url, token,
                    data=body_data,
                    content_type=f"multipart/form-data; boundary={boundary.decode()}",
                )
                if retry_code in (200, 201):
                    count += 1
                    errors -= 1
                    print(f"  [OK] {arcname} (重试成功)")

    if errors:
        print(f"  [WARN] {count} 个成功, {errors} 个失败")
    else:
        print(f"  [OK] 全部 {count} 个文件上传完成")


# ── 上传后端 Python 文件 ─────────────────────────────────────────────────────


def _upload_backend_files(config: dict) -> None:
    """上传 web/backend/ 下的 Python 文件到服务器。"""
    print("\n[UP-BE] 上传后端 Python 文件...")
    username = config.get("username")
    token = config.get("api_token")
    project = config.get("project", "calc-framework")
    if not username or not token:
        print("  [ERR] 未配置 API Token")
        sys.exit(1)

    backend_dir = _REPO_ROOT / "web" / "backend"
    remote_base = f"/home/{username}/{project}/web/backend/"

    count = 0
    errors = 0
    for py_file in sorted(backend_dir.rglob("*.py")):
        rel = py_file.relative_to(backend_dir)
        remote_path = remote_base + str(rel).replace("\\", "/")
        url = _pa_file_url(username, remote_path)
        file_data = py_file.read_bytes()

        boundary = b"----pa-deploy-boundary"
        body_parts = [
            b"--" + boundary,
            b'Content-Disposition: form-data; name="content"; filename="main.py"',
            b"Content-Type: application/octet-stream",
            b"",
            file_data,
            b"--" + boundary + b"--",
        ]
        body_data = b"\r\n".join(body_parts)

        code, _body = _pa_request(
            "POST", url, token,
            data=body_data,
            content_type=f"multipart/form-data; boundary={boundary.decode()}",
        )
        if code in (200, 201):
            count += 1
            print(f"  [OK] {rel}")
        else:
            errors += 1
            print(f"  [ERR] {rel}: HTTP {code}")

    if errors:
        print(f"  [WARN] {count} 个成功, {errors} 个失败")
    else:
        print(f"  [OK] 后端 {count} 个文件上传完成")


# ── 本地上传: local-backend zip ──────────────────────────────────────────────


def _upload_local_backend_zip(config: dict) -> None:
    """上传本地搜索服务器 zip（如果存在）。"""
    local_zip = _REPO_ROOT / "dist" / "终末地本地搜索服务器" / "local-backend.zip"
    if not local_zip.exists():
        local_zip = _REPO_ROOT / "web" / "static" / "local-backend.zip"
    if not local_zip.exists():
        print("  [SKIP] 未找到本地搜索服务器 zip，跳过上传")
        return

    print("\n[UP-LB] 上传本地搜索服务器 zip...")
    username = config.get("username")
    token = config.get("api_token")
    project = config.get("project", "calc-framework")
    if not username or not token:
        print("  [ERR] 未配置 API Token")
        sys.exit(1)

    remote_path = f"/home/{username}/{project}/web/static/local-backend.zip"
    url = _pa_file_url(username, remote_path)

    file_content = local_zip.read_bytes()
    boundary = b"----pa-deploy-boundary"
    body_parts = [
        b"--" + boundary,
        b'Content-Disposition: form-data; name="content"; filename="local-backend.zip"',
        b"Content-Type: application/octet-stream",
        b"",
        file_content,
        b"--" + boundary + b"--",
    ]
    body_data = b"\r\n".join(body_parts)

    code, body = _pa_request(
        "POST", url, token,
        data=body_data,
        content_type=f"multipart/form-data; boundary={boundary.decode()}",
    )
    if code in (200, 201):
        mb = len(file_content) / 1024 / 1024
        print(f"  [OK] 上传成功: local-backend.zip ({mb:.1f} MB)")
    else:
        print(f"  [ERR] 上传失败 ({code}): {body}")


# ── 阶段 5: 重载 Web App ────────────────────────────────────────────────────────


def _reload_webapp(config: dict) -> None:
    """通过 PythonAnywhere API 重载 Web App。"""
    print("\n[RLOAD] [阶段 4/4] 重载 Web App...")
    username = config.get("username")
    token = config.get("api_token")
    domain = config.get("domain", _DEFAULT_DOMAIN.format(username=username or ""))
    if not username or not token:
        print("  [ERR] 未配置 API Token，无法自动重载")
        print("  请手动在 PythonAnywhere Web 页面点击 Reload")
        return

    url = _PA_RELOAD_API.format(username=username, domain=domain)
    code, body = _pa_request("POST", url, token)
    if code == 200:
        print(f"  [OK] 重载成功! 请访问 https://{domain}")
    else:
        print(f"  [ERR] 重载失败 ({code}): {body}")
        print("  请手动在 PythonAnywhere Web 页面点击 Reload")


# ── 初始化配置 ────────────────────────────────────────────────────────────────────


def _init_config() -> None:
    """生成 ~/.pythonanywhere 配置文件模板。"""
    if _CONFIG_PATH.exists():
        print(f"  [WARN] 配置文件已存在: {_CONFIG_PATH}")
        overwrite = input("  覆盖? [y/N] ").strip().lower()
        if overwrite != "y":
            print("  取消")
            return

    print(f"  写入配置模板: {_CONFIG_PATH}")
    _CONFIG_PATH.write_text(
        "[pythonanywhere]\n"
        "# PythonAnywhere 用户名\n"
        "username = wxhwwla\n"
        "# API Token（Account → API Token → Create new token）\n"
        "api_token = \n"
        "# 项目目录名（服务器上 ~/ 下的目录）\n"
        "project = calc-framework\n"
        "# Web App 域名（可选，默认 {username}.pythonanywhere.com）\n"
        "# domain = wxhwwla.pythonanywhere.com\n",
        encoding="utf-8",
    )
    print("  [OK] 配置模板已生成，请编辑填入 api_token")
    print(f"  也可通过环境变量设置: PA_USERNAME, PA_API_TOKEN, PA_PROJECT, PA_DOMAIN")


# ── 打印服务器端指令 ──────────────────────────────────────────────────────────────


def _print_server_instructions(zip_path: Path) -> None:
    """打印手动部署的服务器端操作指南。"""
    print("\n" + "=" * 60)
    print("📋 手动部署指南")
    print("=" * 60)
    print(f"\n1. 上传 zip 到 PythonAnywhere:")
    print(f"   打开 https://www.pythonanywhere.com/user/wxhwwla/files/")
    print(f"   上传 {zip_path} 到 /home/wxhwwla/calc-framework/frontend/")
    print(f"\n   或直接用 API 上传: python {sys.argv[0]} --upload")
    print(f"\n2. 在 PythonAnywhere Bash 控制台中执行:")
    print(f"\n   cd ~/calc-framework")
    print(f"   git pull")
    print(f"   source ~/.virtualenvs/calc-framework/bin/activate")
    print(f"   pip install -q -r web/backend/requirements.txt")
    print(f"   pip install -q -e framework/")
    print(f"   （--all 会自动上传 WSGI；或手动 cp web/wsgi_pythonanywhere.py /var/www/用户名_pythonanywhere_com_wsgi.py）")
    print(f"   cd ~/calc-framework/web/frontend")
    print(f"   rm -rf dist")
    print(f"   mkdir -p dist && cd dist")
    print(f"   unzip -q ~/calc-framework/frontend/dist.zip")
    print(f"   cd ~/calc-framework")
    print(f"   rm -f frontend/dist.zip")
    print(f"\n3. 在 Web 页面点击 Reload")
    print("=" * 60)


# ── 主流程 ──────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="终末地伤害计算器 - PythonAnywhere 自动化部署",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            f"  python {sys.argv[0]}                     全自动（有 Token）或 构建+打包（无 Token）\n"
            f"  python {sys.argv[0]} --help              显示帮助\n"
            f"  python {sys.argv[0]} --zip-only          仅重新打包（跳过 npm 构建）\n"
            f"  python {sys.argv[0]} --upload            构建+打包+上传（不重载）\n"
            f"  python {sys.argv[0]} --reload            仅触发重载\n"
            f"  python {sys.argv[0]} --all               显式全自动\n"
            f"  python {sys.argv[0]} --init-config       初始化配置文件\n\n"
            "配置文件: ~/.pythonanywhere\n"
            "环境变量: PA_USERNAME, PA_API_TOKEN, PA_PROJECT, PA_DOMAIN"
        ),
    )
    parser.add_argument("--upload", action="store_true", help="构建+打包+上传到 PythonAnywhere（需 API Token）")
    parser.add_argument("--reload", action="store_true", help="重载 PythonAnywhere Web App（需 API Token）")
    parser.add_argument("--all", action="store_true", dest="do_all", help="显式全自动: 构建->打包->上传->部署->重载（需 API Token）")
    parser.add_argument("--zip-only", action="store_true", help="仅重新打包 dist/（跳过 npm run build）")
    parser.add_argument("--init-config", action="store_true", help="生成配置文件模板")
    parser.add_argument("--username", help="PythonAnywhere 用户名（覆盖配置文件）")
    parser.add_argument("--api-token", help="PythonAnywhere API Token（覆盖配置文件）")
    parser.add_argument("--project", default="calc-framework", help="服务器上项目目录名（默认 calc-framework）")
    parser.add_argument("--domain", help="Web App 域名（默认 {username}.pythonanywhere.com）")

    args = parser.parse_args()

    if args.init_config:
        _init_config()
        return

    # 读取配置
    config = _load_config()
    if args.username:
        config["username"] = args.username
    if args.api_token:
        config["api_token"] = args.api_token
    if args.project:
        config["project"] = args.project
    if args.domain:
        config["domain"] = args.domain

    has_api = bool(config.get("username") and config.get("api_token"))

    # 默认行为：无参且配了 Token → 全自动；无参且无 Token → 仅构建+打包
    is_default_mode = not any([args.upload, args.reload, args.do_all, args.zip_only])

    if is_default_mode:
        do_upload = has_api
        do_reload = has_api
    else:
        do_upload = args.upload or args.do_all
        do_reload = args.reload or args.do_all

    if (args.upload or args.do_all) and not has_api:
        print("[ERR] --upload/--all 需要配置 API Token")
        print("   请通过 --username/--api-token 传参，或配置 ~/.pythonanywhere")
        print("   或使用 --init-config 生成配置模板")
        sys.exit(1)

    # Phase 1: 构建前端
    if not args.zip_only:
        _build_frontend()

    # Phase 2: 打包 zip
    _create_zip()

    # Phase 3: 上传 + 部署（dist + 后端 + WSGI + 捐赠图）
    if do_upload:
        _upload_dist_files(config)
        _upload_backend_files(config)
        _upload_wsgi(config)
        _upload_arknights_runtime(config)
        _upload_donation_assets(config)
        _upload_local_backend_zip(config)

    # Phase 4: 重载 + 验证
    if do_reload and has_api:
        _reload_webapp(config)
        if do_upload:
            _verify_deployment(config)
    elif not do_upload and not do_reload:
        _print_server_instructions(_ZIP_PATH)
    elif not has_api:
        print("\n[HINT] 提示: 添加 --reload 可自动重载 Web App")

    print(f"\n{'=' * 60}")
    print("[OK] 本地操作完成")
    if not do_upload:
        print(f"[DOC] zip 文件: {_ZIP_PATH}")
    if not do_reload and not do_upload:
        print("[RLOAD] 别忘了在 PythonAnywhere Web 页面点击 Reload")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
