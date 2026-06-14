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
  python web/scripts/deploy_pythonanywhere.py --upload      # 构建+打包+上传（不重载）
  python web/scripts/deploy_pythonanywhere.py --reload      # 仅重载 Web App
  python web/scripts/deploy_pythonanywhere.py --backend-only # 仅上传后端+WSGI（跳过前端）
  python web/scripts/deploy_pythonanywhere.py --fast        # 快速部署: git push → /api/admin/deploy，~3分钟
  python web/scripts/deploy_pythonanywhere.py --help        # 查看完整帮助

首次使用:
  1. 在 PythonAnywhere 生成 API Token: Account → API Token → Create new token
  2. 交互式配置: python web/scripts/deploy_pythonanywhere.py --init-config
  3. 查看部署指南: python web/scripts/deploy_pythonanywhere.py --guide
  4. 首次从零部署: python web/scripts/deploy_pythonanywhere.py --setup
  5. 或直接传参: --username wxhwwla --api-token xxxxx

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
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
from zipfile import ZIP_DEFLATED, ZipFile

# ── 路径 ──────────────────────────────────────────────────────────────────────
_REPO_ROOT = Path(__file__).resolve().parents[2]
_FRONTEND_DIR = _REPO_ROOT / "web" / "frontend"
_DIST_DIR = _FRONTEND_DIR / "dist"
_SCRIPTS_DIR = _REPO_ROOT / "web" / "scripts"
_ZIP_PATH = _REPO_ROOT / "dist_pa.zip"
_ARKNIGHTS_PARSED_ZIP = _REPO_ROOT / "dist_arknights_parsed.zip"
_PA_UPLOAD_INTERVAL = 0.2  # Files API 限流，逐文件上传时的间隔（秒；并发模式下调低）
_MAX_CONCURRENT_UPLOADS = 5  # 并发上传线程数（PA 免费版通常可承受 5-8 并发）
_CONFIG_PATH = Path.home() / ".pythonanywhere"

# ── PythonAnywhere API ────────────────────────────────────────────────────────
_PA_API = "https://www.pythonanywhere.com/api/v0/user/{username}/"
_PA_FILES_API = _PA_API + "files/path{path}"
_PA_RELOAD_API = _PA_API + "webapps/{domain}/reload/"
_PA_CONSOLE_API = _PA_API + "consoles/"
_PA_WEBAPPS_API = _PA_API + "webapps/"

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
    for env_key, cfg_key in [
        ("PA_USERNAME", "username"),
        ("PA_API_TOKEN", "api_token"),
        ("PA_PROJECT", "project"),
        ("PA_DOMAIN", "domain"),
    ]:
        val = os.environ.get(env_key)
        if val:
            config[cfg_key] = val
    return config


# ── 阶段 1: 构建前端 ────────────────────────────────────────────────────────────


def _run_npm(args: list[str], cwd: Path) -> None:
    """跨平台执行 npm 命令。"""
    cmd = [*(["npm.cmd"] if sys.platform == "win32" else ["npm"]), *args]
    print(f"  $ {' '.join(cmd)}  (in {cwd.name})")
    result = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        print("  [ERR] npm 命令失败:")
        print(result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)
        print(result.stderr[-2000:] if len(result.stderr) > 2000 else result.stderr)
        sys.exit(1)
    # 仅回显错误级日志，过滤 Vite 体积提示等噪声
    for line in (result.stdout + result.stderr).splitlines():
        lower = line.lower()
        if "error" in lower and "warning" not in lower:
            print(f"  {line}")


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
    max_retries: int = 3,
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
            "POST",
            url,
            token,
            data=body_data,
            content_type=f"multipart/form-data; boundary={boundary.decode()}",
            timeout=60.0,
        )
        if code in (200, 201):
            if not quiet:
                print(f"  [OK] {label} → {remote_path}")
            return True
        if (code in (-1, -2) or code == 429) and attempt + 1 < max_retries:
            wait = 5 * (attempt + 1)
            reason = "超时" if code == -2 else ("网络错误" if code == -1 else "限流")
            if not quiet:
                print(f"  [RETRY] {label}: {reason} ({code})，{wait}s 后重试 ({attempt + 1}/{max_retries})...")
            time.sleep(wait)
            continue
        if not quiet or code not in (200, 201):
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
    """递归上传目录下指定后缀文件（并发）。返回 (成功数, 失败数)。"""
    if not local_root.is_dir():
        print(f"  [SKIP] {label or local_root.name}: 本地目录不存在 {local_root}")
        return 0, 0

    remote_base = remote_base.rstrip("/") + "/"
    files = sorted(
        p
        for p in local_root.rglob("*")
        if p.is_file() and p.suffix in suffixes and not any(s in skip_parts for s in p.parts)
    )
    total = len(files)
    if label:
        print(f"  {label}: {total} 个文件 → {remote_base}")
    tasks = [
        (
            fpath.read_bytes(),
            remote_base + fpath.relative_to(local_root).as_posix(),
            fpath.relative_to(local_root).as_posix(),
        )
        for fpath in files
    ]
    ok, err = _parallel_upload(config, tasks)
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

    # 与线上一致路径，便于本地/PA 在未解压时从 zip 读取
    canonical = _REPO_ROOT / "tools" / "arknights_scout" / "arknights_parsed.zip"
    canonical.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_bytes(_ARKNIGHTS_PARSED_ZIP.read_bytes())

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
            config,
            f"{home}/games/__init__.py",
            games_init.read_bytes(),
            "games/__init__.py",
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
    home = f"/home/{username}/{project}"
    files = [p for p in donation_dir.iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")]
    if not files:
        print("\n[UP-DON] 跳过捐赠图片（resources/donation/ 无图片）")
        return
    print(f"\n[UP-DON] 上传 {len(files)} 个捐赠图片...")
    for fp in files:
        remote = f"{home}/resources/donation/{fp.name}"
        if not _upload_bytes_to_path(config, remote, fp.read_bytes(), fp.name):
            print(f"  [WARN] 捐赠图上传失败: {fp.name}（可稍后在 PA Files 手动上传到 resources/donation/）")


def _upload_donation_utils(config: dict) -> None:
    """上传捐赠路径解析模块（FastAPI 本地后端等依赖）。"""
    username = config["username"]
    project = config.get("project", "calc-framework")
    home = f"/home/{username}/{project}"
    utils_files = (
        _REPO_ROOT / "utils" / "__init__.py",
        _REPO_ROOT / "utils" / "path_utils.py",
        _REPO_ROOT / "utils" / "donation_assets.py",
    )
    print("\n[UP-UTIL] 上传 utils（捐赠解析）...")
    ok = 0
    for fp in utils_files:
        if not fp.is_file():
            continue
        remote = f"{home}/utils/{fp.name}"
        if _upload_bytes_to_path(config, remote, fp.read_bytes(), f"utils/{fp.name}"):
            ok += 1
    if ok:
        print(f"  [OK] utils {ok} 个文件")


def _ensure_hub_storage(config: dict) -> None:
    """确保 PA 上 hub 数据目录可写（首次上传前创建）。"""
    username = config["username"]
    project = config.get("project", "calc-framework")
    home = f"/home/{username}/{project}"
    keep = b"# hub storage\n"
    for rel in (
        "web/backend/data/.keep",
        "web/backend/data/hub/.keep",
        "web/backend/data/hub/packs/.keep",
    ):
        remote = f"{home}/{rel}"
        if _upload_bytes_to_path(config, remote, keep, rel, quiet=True):
            print(f"  [OK] hub 目录: {rel.rsplit('/', 1)[0]}/")


def _verify_deployment(config: dict) -> None:
    """重载后检查关键 API 是否返回 JSON（非 HTML）。"""
    domain = config.get("domain") or f"{config['username']}.pythonanywhere.com"
    print(f"\n[CHK] 验证 https://{domain} ...")
    time.sleep(4)
    checks: list[tuple[str, str, bool]] = [
        (f"https://{domain}/api/health", '"status"', True),
        (f"https://{domain}/api/layout", '"sections"', True),
        (f"https://{domain}/api/donation/manifest", '"file"', True),
        (f"https://{domain}/api/hub/packs?limit=1", '"packs"', True),
        (f"https://{domain}/api/pack/theme/default", '"schema_version"', True),
        (f"https://{domain}/api/adapters", '"id"', True),
        (f"https://{domain}/api/adapters/endfield/pack-bundle", '"adapter_id"', True),
        (f"https://{domain}/api/data/profiles", '"endfield"', True),
        (f"https://{domain}/api/history", "[", True),
        (f"https://{domain}/api/download/client", "PK", True),  # zip 魔数
        (f"https://{domain}/compute", "Calc Framework", False),  # SPA 路由，允许 HTML
    ]
    ok = True
    for url, needle, require_non_html in checks:
        # PA 免费版 reload 后首个请求可能冷启动超时，layout 端点加重试
        is_layout = "/api/layout" in url
        max_tries = 3 if is_layout else 1
        for attempt in range(max_tries):
            try:
                with urlopen(url, timeout=45) as resp:
                    body = resp.read(800).decode("utf-8", errors="replace")
                if needle in body and (not require_non_html or not body.lstrip().startswith("<")):
                    print(f"  [OK] {url}")
                    break
                else:
                    if attempt + 1 < max_tries:
                        print(f"  [RETRY] {url} (attempt {attempt + 2}/{max_tries})...")
                        time.sleep(5)
                        continue
                    print(f"  [FAIL] {url} 返回非预期内容: {body[:120]!r}")
                    ok = False
            except Exception as e:
                if attempt + 1 < max_tries:
                    print(f"  [RETRY] {url}: {e} (attempt {attempt + 2}/{max_tries})...")
                    time.sleep(5)
                    continue
                print(f"  [FAIL] {url}: {e}")
                ok = False

    ak_url = f"https://{domain}/api/arknights/operators"
    print(f"  [WARM] 预热 {ak_url}（首次加载耗时长，超时 120s）...")
    try:
        with urlopen(ak_url, timeout=120) as resp:
            ak_body = resp.read().decode("utf-8", errors="replace")
        ak_data = json.loads(ak_body)
        ak_count = int(ak_data.get("count", 0))
        if ak_count >= 100:
            print(f"  [OK] {ak_url} (干员 {ak_count} 个)")
        else:
            print(f"  [WARN] {ak_url} 仅 {ak_count} 个干员（应有约 400+）")
            print("  [DOC] zip 已上传但未解压。请在 PA Bash 执行:")
            project = config.get("project", "calc-framework")
            print(f"    cd ~/{project}/tools/arknights_scout/output")
            print("    rm -rf parsed && mkdir -p parsed && unzip -oq arknights_parsed.zip -d parsed")
            ok = False
    except Exception as e:
        print(f"  [FAIL] {ak_url}: {e}")
        ok = False

    gen_template_url = f"https://{domain}/api/generator/templates"
    try:
        with urlopen(gen_template_url, timeout=60) as resp:
            gen_body = resp.read().decode("utf-8", errors="replace")
        gen_data = json.loads(gen_body)
        if isinstance(gen_data, dict) and len(gen_data) >= 0:
            print(f"  [OK] {gen_template_url} (模板数: {len(gen_data)})")
        else:
            print(f"  [FAIL] {gen_template_url} 返回非预期内容")
            ok = False
    except Exception as e:
        print(f"  [FAIL] {gen_template_url}: {e}")
        ok = False

    if not ok:
        print("\n  [HINT] 若仍报 missing argument 'send'，请打开 PA Web → WSGI configuration file")
        print(
            "  确认路径为 /var/www/你的用户名_pythonanywhere_com_wsgi.py，"
            "且内容为 wsgi_pythonanywhere.py（无 application=app）"
        )
    else:
        print("  [OK] API 正常，请 Ctrl+F5 刷新 /compute")


def _pa_request(
    method: str, url: str, token: str, data: bytes | None = None, content_type: str | None = None, timeout: float = 30.0
) -> tuple[int, str]:
    """向 PythonAnywhere API 发起请求（含超时）。"""
    headers = {"Authorization": f"Token {token}"}
    if content_type:
        headers["Content-Type"] = content_type
    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8")
    except HTTPError as e:
        body = e.read().decode("utf-8")[:500]
        return e.code, body
    except URLError as e:
        return -1, str(e)
    except TimeoutError:
        return -2, "timeout"


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
        "POST",
        url,
        token,
        data=body_data,
        content_type=f"multipart/form-data; boundary={boundary.decode()}",
    )
    if code in (200, 201):
        print(f"  [OK] 上传成功: {remote_path}")
    else:
        print(f"  [ERR] 上传失败 ({code}): {body}")
        sys.exit(1)


# ── 阶段 4: 直接上传 dist 文件到服务器（避免 Console API 限制） ──────────────


def _upload_single_dist_file(
    config: dict,
    username: str,
    dist_base: str,
    arcname: str,
    file_data: bytes,
) -> tuple[str, int, bool]:
    """上传单个 dist 文件（含 4 次重试 + 父目录创建 fallback）。

    返回 (arcname, size_bytes, ok)。
    每个文件内部支持最多 4 次重试，失败后尝试通过 .keep 创建父目录再重试。
    """  # fmt: skip
    token: str = config["api_token"]
    remote_path = dist_base + arcname
    boundary = b"----pa-deploy-boundary"
    body_data = b""

    for attempt in range(2):
        url = _pa_file_url(username, remote_path)
        body_parts = [
            b"--" + boundary,
            f'Content-Disposition: form-data; name="content"; filename="{arcname}"'.encode(),
            b"Content-Type: application/octet-stream",
            b"",
            file_data,
            b"--" + boundary + b"--",
        ]
        body_data = b"\r\n".join(body_parts)
        code, _body = _pa_request(
            "POST",
            url,
            token,
            data=body_data,
            content_type=f"multipart/form-data; boundary={boundary.decode()}",
            timeout=30.0,
        )
        if code in (200, 201):
            return (arcname, len(file_data), True)
        if (code in (-1, -2) or code == 429) and attempt < 1:
            wait = 3
            reason = "超时" if code == -2 else ("网络错误" if code == -1 else "限流")
            print(f"  [RETRY] {arcname}: {reason} ({code})，{wait}s 后重试...")
            time.sleep(wait)

    return (arcname, len(file_data), False)


def _upload_dist_files(config: dict) -> None:
    """将 dist/ 中的文件并发上传到 PythonAnywhere。

    先发一个预热请求激活 PA API，再 5 并发上传剩余文件。
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

    # 收集所有 zip 条目
    entries: list[tuple[str, bytes]] = []
    with ZipFile(str(_ZIP_PATH), "r") as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            entries.append((info.filename.replace("\\", "/"), zf.read(info)))

    total = len(entries)

    # 预热：先传一个小文件激活 PA API，避免首批并发全超时
    warmup = next((e for e in entries if e[0].endswith("index.html")), entries[0])
    print(f"  预热 PA API（{warmup[0]}，{len(warmup[1])} bytes）...")
    _upload_bytes_to_path(config, dist_base + warmup[0], warmup[1], "warmup", quiet=True, max_retries=5)
    entries = [e for e in entries if e[0] != warmup[0]]
    total = len(entries)
    print(f"  剩余 {total} 个文件，并发 {_MAX_CONCURRENT_UPLOADS} 线程...")
    t0 = time.time()

    # 心跳线程
    heartbeat_stop = threading.Event()

    def _heartbeat() -> None:
        while not heartbeat_stop.wait(5):
            elapsed = time.time() - t0
            done = count + errors
            tail = f"，{errors} 失败" if errors else ""
            print(f"  [⏱ {elapsed:.0f}s] {done}/{total} 完成{tail}")

    ticker = threading.Thread(target=_heartbeat, daemon=True)
    ticker.start()

    count = 0
    errors = 0
    with ThreadPoolExecutor(max_workers=_MAX_CONCURRENT_UPLOADS) as pool:
        futures = {
            pool.submit(
                _upload_bytes_to_path, config, dist_base + arcname, data, arcname, quiet=True, max_retries=3
            ): arcname
            for arcname, data in entries
        }
        for f in as_completed(futures):
            arcname = futures[f]
            try:
                if f.result():
                    count += 1
                else:
                    errors += 1
                    print(f"  [WARN] {arcname}: 上传失败")
            except Exception as e:
                errors += 1
                print(f"  [ERR] {arcname}: {e}")

    heartbeat_stop.set()
    elapsed = time.time() - t0
    if errors:
        print(f"  [⏱ {elapsed:.0f}s] {count} 成功, {errors} 失败")
    else:
        print(f"  [⏱ {elapsed:.0f}s] 全部 {count} 个文件上传完成")


# ── 上传后端 Python 文件 ─────────────────────────────────────────────────────
def _parallel_upload(config: dict, tasks: list[tuple[bytes, str, str]]) -> tuple[int, int]:
    """并发上传多个文件。tasks: [(file_data, remote_path, label), ...] 返回 (ok, err)。"""
    ok, err = 0, 0
    total = len(tasks)
    if not tasks:
        return ok, err

    print(f"  共 {total} 个文件，并发 {_MAX_CONCURRENT_UPLOADS} 线程...")
    t0 = time.time()

    # 心跳线程：每 3s 输出进度（长文件上传时不至看起来卡住）
    heartbeat_stop = threading.Event()

    def _heartbeat() -> None:
        while not heartbeat_stop.wait(3):
            elapsed = time.time() - t0
            done = ok + err
            tail = f"，{err} 失败" if err else ""
            print(f"  [⏱ {elapsed:.0f}s] {done}/{total} 完成{tail}")

    ticker = threading.Thread(target=_heartbeat, daemon=True)
    ticker.start()

    with ThreadPoolExecutor(max_workers=_MAX_CONCURRENT_UPLOADS) as pool:
        futures = {
            pool.submit(_upload_bytes_to_path, config, remote, data, label, quiet=True): label
            for data, remote, label in tasks
        }
        for f in as_completed(futures):
            label = futures[f]
            done = ok + err + 1  # +1 for the file just completing
            try:
                if f.result():
                    print(f"  [{done}/{total} OK] {label}")
                    ok += 1
                else:
                    print(f"  [{done}/{total} ERR] {label}")
                    err += 1
            except Exception as e:
                print(f"  [{done}/{total} ERR] {label}: {e}")
                err += 1

    heartbeat_stop.set()
    elapsed = time.time() - t0
    print(f"  [⏱ {elapsed:.1f}s] 完成: {ok} 成功, {err} 失败")
    return ok, err


def _upload_backend_files(config: dict) -> None:
    """上传 web/backend/ 下的 Python 文件到服务器（并发，含 429 重试）。"""
    print("\n[UP-BE] 上传后端 Python 文件...")
    username = config.get("username")
    token = config.get("api_token")
    project = config.get("project", "calc-framework")
    if not username or not token:
        print("  [ERR] 未配置 API Token")
        sys.exit(1)

    backend_dir = _REPO_ROOT / "web" / "backend"
    remote_base = f"/home/{username}/{project}/web/backend/"

    py_files = sorted(backend_dir.rglob("*.py"))
    tasks = [
        (
            py_file.read_bytes(),
            remote_base + str(py_file.relative_to(backend_dir)).replace("\\", "/"),
            str(py_file.relative_to(backend_dir)),
        )
        for py_file in py_files
    ]

    count, errors = _parallel_upload(config, tasks)
    if errors:
        print(f"  [WARN] {count} 个成功, {errors} 个失败")
    else:
        print(f"  [OK] 后端 {count} 个文件上传完成")


def _upload_generator_tools(config: dict) -> None:
    """上传 tools/generator/ 下的 Python / JSON 文件（生成器 API 依赖，并发）。"""
    print("\n[UP-GEN] 上传生成器工具文件 tools/generator/...")
    username = config.get("username")
    token = config.get("api_token")
    project = config.get("project", "calc-framework")
    if not username or not token:
        print("  [ERR] 未配置 API Token")
        sys.exit(1)

    gen_dir = _REPO_ROOT / "tools" / "generator"
    if not gen_dir.is_dir():
        print("  [SKIP] tools/generator/ 目录不存在")
        return

    files = sorted(p for p in gen_dir.rglob("*") if p.is_file() and p.suffix in (".py", ".json"))
    tasks = [
        (
            fpath.read_bytes(),
            f"/home/{username}/{project}/" + str(fpath.relative_to(gen_dir.parent)).replace("\\", "/"),
            str(fpath.relative_to(gen_dir.parent)),
        )
        for fpath in files
    ]

    count, errors = _parallel_upload(config, tasks)
    if errors:
        print(f"  [WARN] {count} 个成功, {errors} 个失败")
    else:
        print(f"  [OK] 生成器工具 {count} 个文件上传完成")


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
        "POST",
        url,
        token,
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
    """交互式生成 ~/.pythonanywhere 配置文件，并验证 API Token。

    引导用户输入用户名和 Token，调用 PA API 验证 Token 有效性，
    验证通过后才写入配置文件。
    """
    # 打印说明
    print("\n" + "=" * 60)
    print("  PythonAnywhere 配置初始化")
    print("=" * 60)
    print()
    print("  本工具将帮助您配置 PythonAnywhere API Token，实现自动化部署。")
    print()
    print("  准备事项:")
    print("    1. 已注册 PythonAnywhere 账号 (https://www.pythonanywhere.com/)")
    print("    2. 已生成 API Token (Account → API Token → Create new token)")
    print("    3. 知道您的用户名")
    print()
    print("  也可直接设置环境变量: PA_USERNAME, PA_API_TOKEN, PA_PROJECT, PA_DOMAIN")
    print()

    # 检查已有配置
    existing_config = _load_config() if _CONFIG_PATH.exists() else {}
    if existing_config.get("username") and existing_config.get("api_token"):
        print(f"  [INFO] 已有配置文件: {_CONFIG_PATH}")
        print(f"         用户名: {existing_config.get('username')}")
        print(f"         Token: {'*' * 8}...")
        overwrite = input("\n  是否覆盖现有配置? [y/N] ").strip().lower()
        if overwrite not in ("y", "yes"):
            print("  取消。使用 --validate-token 可验证现有 Token。")
            return

    # 询问用户名
    print()
    default_user = existing_config.get("username", "")
    prompt = f"  PythonAnywhere 用户名 [{default_user}]: " if default_user else "  PythonAnywhere 用户名: "
    username = input(prompt).strip()
    if not username and default_user:
        username = default_user
    if not username:
        print("  [ERR] 用户名不能为空")
        return

    # 询问 API Token
    default_token_hint = "（已有）" if existing_config.get("api_token") else ""
    prompt = f"  API Token {default_token_hint}: "
    token = input(prompt).strip()
    if not token and existing_config.get("api_token"):
        token = existing_config["api_token"]
    if not token:
        print("  [ERR] API Token 不能为空")
        print("  获取方式: 登录 PA → Account → API Token → Create new token")
        print(f"  链接: https://www.pythonanywhere.com/user/{username}/account/#api-token")
        return

    # 询问项目目录名
    default_project = existing_config.get("project", "calc-framework")
    project = input(f"  项目目录名 [{default_project}]: ").strip()
    if not project:
        project = default_project

    # 验证 Token
    print("\n  正在验证 API Token...")
    valid, msg = _validate_pa_token(username, token)
    if not valid:
        print(f"  [ERR] Token 验证失败: {msg}")
        print()
        print("  常见原因:")
        print("    - Token 复制不完整")
        print("    - 用户名拼写错误")
        print("    - Token 已过期（请在 PA 重新生成）")
        print("    - 网络连接问题")
        retry = input("\n  仍要保存配置（跳过验证）? [y/N] ").strip().lower()
        if retry not in ("y", "yes"):
            print("  取消。请检查后重试。")
            return

    # 写入配置文件
    print(f"\n  写入配置: {_CONFIG_PATH}")
    _CONFIG_PATH.write_text(
        "[pythonanywhere]\n"
        f"# PythonAnywhere 用户名\n"
        f"username = {username}\n"
        f"# API Token (已验证)\n"
        f"# 获取方式: 登录 PA → Account → API Token → Create new token\n"
        f"# 链接: https://www.pythonanywhere.com/user/{username}/account/#api-token\n"
        f"api_token = {token}\n"
        f"# 项目目录名（服务器上 ~/ 下的目录）\n"
        f"project = {project}\n"
        f"# Web App 域名（可选，默认 {{username}}.pythonanywhere.com）\n"
        f"# domain = {username}.pythonanywhere.com\n",
        encoding="utf-8",
    )

    print("  [OK] 配置已保存！")
    if valid:
        print("  [OK] Token 验证通过 — 可以开始部署")
    print()
    print("  下一步:")
    print("    - 首次部署（推荐）: python web/scripts/deploy_pythonanywhere.py --setup")
    print("    - 查看部署指南:     python web/scripts/deploy_pythonanywhere.py --guide")
    print("    - 全量更新:         python web/scripts/deploy_pythonanywhere.py --all")
    print()
    print("  也可通过环境变量设置: PA_USERNAME, PA_API_TOKEN, PA_PROJECT, PA_DOMAIN")
    sys.exit(0)


# ── 打印服务器端指令 ──────────────────────────────────────────────────────────────


def _print_server_instructions(zip_path: Path) -> None:
    """打印手动部署的服务器端操作指南。"""
    print("\n" + "=" * 60)
    print("📋 手动部署指南")
    print("=" * 60)
    print("\n1. 上传 zip 到 PythonAnywhere:")
    print("   打开 https://www.pythonanywhere.com/user/wxhwwla/files/")
    print(f"   上传 {zip_path} 到 /home/wxhwwla/calc-framework/frontend/")
    print(f"\n   或直接用 API 上传: python {sys.argv[0]} --upload")
    print("\n2. 在 PythonAnywhere Bash 控制台中执行:")
    print("\n   cd ~/calc-framework")
    print("   git pull")
    print("   source ~/.virtualenvs/calc-framework/bin/activate")
    print("   pip install -q -r web/backend/requirements.txt")
    print("   pip install -q -e framework/")
    print(
        "   （--all 会自动上传 WSGI；或手动 cp web/wsgi_pythonanywhere.py /var/www/用户名_pythonanywhere_com_wsgi.py）"
    )
    print("   cd ~/calc-framework/web/frontend")
    print("   rm -rf dist")
    print("   mkdir -p dist && cd dist")
    print("   unzip -q ~/calc-framework/frontend/dist.zip")
    print("   cd ~/calc-framework")
    print("   rm -f frontend/dist.zip")
    print("\n3. 在 Web 页面点击 Reload")
    print("=" * 60)


# ── 首次部署指南 ─────────────────────────────────────────────────────────────────


def _print_first_time_guide(config: dict | None = None) -> None:
    """打印完整的首次部署步骤指南（中英文对照）。"""
    username = (config or {}).get("username", "你的用户名")
    project = (config or {}).get("project", "calc-framework")
    print(
        """
╔══════════════════════════════════════════════════════════════════════════╗
║              终末地伤害计算器 — 首次部署完整指南                            ║
║              Endfield Damage Calculator — First-Time Deploy Guide         ║
╚══════════════════════════════════════════════════════════════════════════╝

【第 1 步 | Step 1】注册 PythonAnywhere 账号
────────────────────────────────────────────────────
  1. 访问 https://www.pythonanywhere.com/
  2. 点击 "Start running Python online" → "Create a Beginner account"（免费套餐）
  3. 填写用户名、邮箱、密码，完成注册

【第 2 步 | Step 2】生成 API Token
────────────────────────────────────────────────────
  1. 登录后，点击右上角 Account → "API token" 标签
  2. 或直接访问: https://www.pythonanywhere.com/user/{user}/account/#api-token
  3. 点击 "Create a new API token"，复制生成的 Token
  4. ⚠ Token 只显示一次，请妥善保存！

【第 3 步 | Step 3】初始化本地配置
────────────────────────────────────────────────────
  运行以下命令，交互式配置用户名和 Token:
"""
        + "    python web/scripts/deploy_pythonanywhere.py --init-config"
        + """
  或直接设置环境变量:
    set PA_USERNAME=你的用户名        (Windows PowerShell: $env:PA_USERNAME="...")
    set PA_API_TOKEN=你的Token        (Windows PowerShell: $env:PA_API_TOKEN="...")

【第 4 步 | Step 4】自动首次部署（推荐）
────────────────────────────────────────────────────
  配置完成后，一条命令完成首次部署:
"""
        + "    python web/scripts/deploy_pythonanywhere.py --setup"
        + """
  --setup 会自动完成以下操作:
    1. 检查/创建 PythonAnywhere Web App
    2. 创建必要的服务器目录结构
    3. 构建并上传前端文件（dist/）
    4. 上传后端 API 文件（web/backend/）
    5. 上传计算框架（framework/）
    6. 上传游戏数据文件（games/）
    7. 上传 WSGI 入口文件到 /var/www/
    8. 上传示例配置包到 Calc Hub 市场
    9. 重载 Web App
   10. 验证部署结果

【第 5 步 | Step 5】手动部署（备选方案）
────────────────────────────────────────────────────
  如果自动部署失败，可在 PythonAnywhere Bash 控制台手动执行:
"""
        + f"""    # 克隆代码仓库
    git clone https://github.com/wxhwwla/endfield_damage_calculator.git ~/{project}

    # 创建虚拟环境并安装依赖
    mkvirtualenv --python=/usr/bin/python3.10 {project}
    workon {project}
    pip install -r ~/{project}/web/backend/requirements.txt
    pip install -e ~/{project}/framework/

    # 复制 WSGI 文件
    cp ~/{project}/web/wsgi_pythonanywhere.py /var/www/{username}_pythonanywhere_com_wsgi.py

    # 在 Web 页面设置:
    #   - Source code: /home/{username}/{project}
    #   - Working directory: /home/{username}/{project}
    #   - WSGI configuration file: /var/www/{username}_pythonanywhere_com_wsgi.py
    #   - Virtualenv: /home/{username}/.virtualenvs/{project}

    # 点击 Reload 按钮
"""
        + f"""
【常见问题 | FAQ】
────────────────────────────────────────────────────
  Q: 提示 "missing argument 'send'"?
  A: WSGI 配置文件路径未正确设置。请确保 Web 页面中 WSGI configuration file
     指向 /var/www/你的用户名_pythonanywhere_com_wsgi.py，且该文件内容为
     wsgi_pythonanywhere.py 的内容（不应包含 application=app）。

  Q: 前端页面 404?
  A: 请确保 dist/ 文件已正确解压到 ~/calc-framework/web/frontend/dist/

  Q: 干员数量为 0 或很少?
  A: 需要在 PA Bash 中解压干员数据:
     cd ~/calc-framework/tools/arknights_scout/output
     rm -rf parsed && mkdir -p parsed && unzip -oq arknights_parsed.zip -d parsed

  Q: API 返回 500 错误?
  A: 检查 WSGI 错误日志（Web 页面 → Log files → Error log），确认所有依赖已安装。
     常见缺失: pip install -e ~/calc-framework/framework/

╔══════════════════════════════════════════════════════════════════════════╗
║  部署完成后访问: https://{username}.pythonanywhere.com/compute                ║
╚══════════════════════════════════════════════════════════════════════════╝
"""
    )


def _validate_pa_token(username: str, token: str) -> tuple[bool, str]:
    """验证 PA API Token 是否有效。

    参数:
        username: PA 用户名。
        token: PA API Token。

    返回:
        (是否有效, 错误信息或账户类型)。
    """
    url = _PA_API.format(username=username) + "cpu/"
    code, body = _pa_request("GET", url, token)
    if code == 200:
        return True, "ok"
    if code == 401:
        return False, "Token 无效或未授权（401 Unauthorized）"
    if code == 404:
        return False, f"用户名 '{username}' 不存在（404 Not Found）"
    if code == -1:
        return False, f"网络连接失败: {body[:120]}"
    if code == -2:
        return False, "请求超时，请检查网络"
    return False, f"HTTP {code}: {body[:120]}"


# ── Web App 管理 ────────────────────────────────────────────────────────────────


def _check_existing_webapp(config: dict) -> dict | None:
    """检查 PythonAnywhere 账号是否已有 Web App。

    参数:
        config: 含 username, api_token 的配置字典。

    返回:
        已有 Web App 信息 dict，或 None（无 Web App / 查询失败）。
    """
    username = config["username"]
    token = config["api_token"]
    url = _PA_API.format(username=username) + "webapps/"
    code, body = _pa_request("GET", url, token)
    if code == 200:
        try:
            webapps = json.loads(body)
            if isinstance(webapps, list) and webapps:
                wa = webapps[0]
                domain = wa.get("domain_name", f"{username}.pythonanywhere.com")
                print(f"  [OK] 检测到已有 Web App: {domain}")
                print(f"       Python 版本: {wa.get('python_version', 'unknown')}")
                return wa
        except json.JSONDecodeError:
            pass
    elif code == 401:
        print("  [ERR] API Token 无效（401），无法查询 Web App")
    else:
        print(f"  [WARN] 查询 Web App 失败 ({code}): {body[:200]}")
    return None


def _create_webapp(config: dict, python_version: str = "3.10") -> bool:
    """通过 PA API 创建新的 Web App（手动配置模式）。

    PythonAnywhere 免费套餐只允许 1 个 Web App，使用手动配置
    （manual_config=True）以便自定义 WSGI 路径。

    参数:
        config: 含 username, api_token 的配置字典。
        python_version: Python 版本，默认 "3.10"。

    返回:
        是否创建成功。
    """
    username = config["username"]
    token = config["api_token"]
    url = _PA_API.format(username=username) + "webapps/"

    payload = json.dumps(
        {
            "python_version": f"python{python_version}",
            "manual_config": True,
        }
    ).encode("utf-8")

    print(f"  正在创建 Web App: {username}.pythonanywhere.com (Python {python_version})...")
    code, body = _pa_request("POST", url, token, data=payload, content_type="application/json")

    if code in (200, 201):
        domain = f"{username}.pythonanywhere.com"
        print(f"  [OK] Web App 创建成功: {domain}")
        print("  [DOC] 请在 PythonAnywhere Web 页面完善以下设置:")
        print(f"    - Source code: /home/{username}/calc-framework")
        print(f"    - Working directory: /home/{username}/calc-framework")
        print(f"    - WSGI configuration file: /var/www/{username}_pythonanywhere_com_wsgi.py")
        print(f"    - Virtualenv: /home/{username}/.virtualenvs/calc-framework")
        return True
    else:
        # 常见错误处理
        try:
            resp = json.loads(body) if body else {}
        except json.JSONDecodeError:
            resp = {}
        detail = resp.get("error", resp.get("detail", body[:200]))
        if "already have" in str(detail).lower() or "limit" in str(detail).lower():
            print(f"  [WARN] 可能已有 Web App（免费套餐仅限 1 个）: {detail}")
            print(f"  若需重建，请先删除已有 Web App: https://www.pythonanywhere.com/user/{username}/webapps/")
        else:
            print(f"  [ERR] Web App 创建失败 ({code}): {detail}")
        return False


def _create_directories_on_server(config: dict) -> None:
    """在 PA 服务器上创建必要的项目目录结构（通过上传 .keep 文件）。

    确保以下目录存在:
      ~/{project}/web/backend/data/
      ~/{project}/web/backend/data/hub/
      ~/{project}/web/backend/data/hub/packs/
      ~/{project}/web/frontend/dist/
      ~/{project}/framework/src/
      ~/{project}/framework/adapters/
      ~/{project}/games/
      ~/{project}/games/endfield/
      ~/{project}/games/endfield/data/
      ~/{project}/games/arknights/
      ~/{project}/resources/donation/
      ~/{project}/tools/generator/
      ~/{project}/utils/
    """
    username = config["username"]
    project = config.get("project", "calc-framework")
    home = f"/home/{username}/{project}"
    keep = b"# auto-created by deploy script\n"

    dirs = [
        "web/backend/data/.keep",
        "web/backend/data/hub/.keep",
        "web/backend/data/hub/packs/.keep",
        "web/frontend/dist/.keep",
        "framework/src/calc_framework/.keep",
        "framework/adapters/.keep",
        "games/.keep",
        "games/endfield/.keep",
        "games/endfield/data/.keep",
        "games/arknights/.keep",
        "resources/donation/.keep",
        "tools/generator/.keep",
        "utils/.keep",
    ]

    print("\n[DIR] 创建服务器目录结构...")
    ok = 0
    for rel in dirs:
        remote = f"{home}/{rel}"
        if _upload_bytes_to_path(config, remote, keep, rel, quiet=True):
            ok += 1
    print(f"  [OK] {ok}/{len(dirs)} 个目录就绪")


# ── 框架文件上传 ─────────────────────────────────────────────────────────────────


def _upload_framework_src(config: dict) -> None:
    """上传 framework/src/ 下的所有 Python 文件（WSGI import 依赖）。"""
    print("\n[UP-FW] 上传计算框架 framework/src/...")
    username = config["username"]
    project = config.get("project", "calc-framework")
    home = f"/home/{username}/{project}"

    src_dir = _REPO_ROOT / "framework" / "src"
    if not src_dir.is_dir():
        print("  [WARN] framework/src/ 目录不存在，跳过")
        return

    _upload_directory_tree(
        config,
        src_dir,
        f"{home}/framework/src",
        suffixes=(".py",),
        label="framework/src",
    )


def _upload_framework_adapters(config: dict) -> None:
    """上传 framework/adapters/ 下的所有文件（meta.json + Python 适配器）。"""
    print("\n[UP-ADAPTERS] 上传适配器 framework/adapters/...")
    username = config["username"]
    project = config.get("project", "calc-framework")
    home = f"/home/{username}/{project}"

    adapters_dir = _REPO_ROOT / "framework" / "adapters"
    if not adapters_dir.is_dir():
        print("  [WARN] framework/adapters/ 目录不存在，跳过")
        return

    _upload_directory_tree(
        config,
        adapters_dir,
        f"{home}/framework/adapters",
        suffixes=(".py", ".json"),
        label="framework/adapters",
    )


def _upload_framework_init(config: dict) -> None:
    """上传 framework 包入口文件（setup.py / pyproject.toml 等，用于 pip install -e）。"""
    username = config["username"]
    project = config.get("project", "calc-framework")
    home = f"/home/{username}/{project}"
    fw_root = _REPO_ROOT / "framework"

    init_files = [
        fw_root / "setup.py",
        fw_root / "setup.cfg",
        fw_root / "pyproject.toml",
    ]
    print("\n[UP-FW-CFG] 上传 framework 包配置...")
    ok = 0
    for fp in init_files:
        if fp.is_file():
            remote = f"{home}/framework/{fp.name}"
            if _upload_bytes_to_path(config, remote, fp.read_bytes(), f"framework/{fp.name}"):
                ok += 1
    if ok:
        print(f"  [OK] framework 包配置 {ok} 个文件")


# ── 游戏数据上传 ─────────────────────────────────────────────────────────────────


def _upload_game_data(config: dict) -> None:
    """上传游戏数据文件（endfield data JSON + arknights runtime）。"""
    print("\n[UP-GAME] 上传游戏数据文件...")
    username = config["username"]
    project = config.get("project", "calc-framework")
    home = f"/home/{username}/{project}"

    # games/__init__.py
    games_init = _REPO_ROOT / "games" / "__init__.py"
    if games_init.is_file():
        _upload_bytes_to_path(
            config,
            f"{home}/games/__init__.py",
            games_init.read_bytes(),
            "games/__init__.py",
        )

    # games/endfield/
    _upload_directory_tree(
        config,
        _REPO_ROOT / "games" / "endfield",
        f"{home}/games/endfield",
        suffixes=(".py", ".json"),
        label="games/endfield",
    )

    # arknights 运行时（与 --all 一致）
    _upload_arknights_runtime(config)


# ── Hub 市场示例上传 ────────────────────────────────────────────────────────────


def _upload_hub_samples(config: dict) -> None:
    """上传示例 .calcpack 文件到 Calc Hub 市场。

    将 web/hub/samples/ 下的 .calcpack 文件上传到 PA 服务器的
    web/backend/data/hub/packs/ 目录，使首次部署后市场不为空。
    同时上传 catalog.json 索引文件。
    """
    samples_dir = _REPO_ROOT / "web" / "hub" / "samples"
    if not samples_dir.is_dir():
        print("\n[HUB-SAMPLE] 跳过示例上传（web/hub/samples/ 目录不存在）")
        return

    calcpack_files = sorted(samples_dir.glob("*.calcpack"))
    if not calcpack_files:
        print("\n[HUB-SAMPLE] 跳过示例上传（无 .calcpack 文件）")
        return

    print(f"\n[HUB-SAMPLE] 上传 {len(calcpack_files)} 个示例配置包到 Calc Hub...")
    username = config["username"]
    project = config.get("project", "calc-framework")
    home = f"/home/{username}/{project}"
    hub_packs_remote = f"{home}/web/backend/data/hub/packs"

    uploaded = 0
    for fp in calcpack_files:
        remote = f"{hub_packs_remote}/{fp.name}"
        if _upload_bytes_to_path(config, remote, fp.read_bytes(), f"hub/samples/{fp.name}"):
            uploaded += 1

    if uploaded:
        print(f"  [OK] {uploaded}/{len(calcpack_files)} 个示例包上传完成")

    # 上传 catalog.json 索引
    catalog_path = _REPO_ROOT / "web" / "hub" / "catalog.json"
    if catalog_path.is_file():
        remote_catalog = f"{home}/web/hub/catalog.json"
        if _upload_bytes_to_path(config, remote_catalog, catalog_path.read_bytes(), "hub/catalog.json"):
            print("  [OK] catalog.json 索引上传完成")


# ── 服务器端 Bash 命令执行 ──────────────────────────────────────────────────────


def _run_console_command(config: dict, command: str, label: str = "") -> tuple[int, str]:
    """通过 PA Console API 在服务器上执行 Bash 命令。

    参数:
        config: 配置字典。
        command: 要执行的 Bash 命令。
        label: 标签（用于日志）。

    返回:
        (console_id, 错误信息或空字符串)。
    """
    username = config["username"]
    token = config["api_token"]
    url = _PA_API.format(username=username) + "consoles/"

    payload = json.dumps(
        {
            "executable": "bash",
            "arguments": command,
            "working_directory": f"/home/{username}/{config.get('project', 'calc-framework')}",
        }
    ).encode("utf-8")

    code, body = _pa_request("POST", url, token, data=payload, content_type="application/json")
    if code in (200, 201):
        try:
            resp = json.loads(body)
            console_id = resp.get("id", 0)
            return console_id, ""
        except json.JSONDecodeError:
            return -1, f"无法解析响应: {body[:200]}"
    return -1, f"HTTP {code}: {body[:200]}"


def _get_console_output(config: dict, console_id: int) -> str:
    """获取 PA Console 输出（用于验证服务器端命令执行结果）。"""
    username = config["username"]
    token = config["api_token"]
    url = _PA_API.format(username=username) + f"consoles/{console_id}/get_latest_output/"
    code, body = _pa_request("GET", url, token)
    if code == 200:
        try:
            resp = json.loads(body)
            return resp.get("output", "")
        except json.JSONDecodeError:
            return ""
    return ""


def _setup_virtualenv_on_server(config: dict) -> None:
    """在 PA 服务器上创建虚拟环境并安装依赖（通过 Console API）。

    免费套餐 Console 有限制，此函数提供手动指令作为备选。
    """
    project = config.get("project", "calc-framework")

    print("\n[VENV] 虚拟环境设置...")
    print("  [DOC] PythonAnywhere 免费套餐不支持 Console API 长时间任务。")
    print("  请打开 PA Bash 控制台手动执行以下命令:")
    print()
    print(f"    mkvirtualenv --python=/usr/bin/python3.10 {project}")
    print(f"    workon {project}")
    print(f"    pip install -r ~/{project}/web/backend/requirements.txt")
    print(f"    pip install -e ~/{project}/framework/")
    print()

    # 尝试调用 Console API（可能因套餐限制而失败）
    cmd = (
        f"cd ~/{project} && "
        f"python3.10 -m venv ~/.virtualenvs/{project} 2>/dev/null; "
        f"~/.virtualenvs/{project}/bin/pip install -q -r web/backend/requirements.txt 2>&1 | tail -5"
    )
    console_id, _err = _run_console_command(config, cmd, "venv-setup")
    if console_id > 0:
        print(f"  [OK] 已在服务器启动虚拟环境创建（Console #{console_id}）")
        print("  等待 30 秒后检查输出...")
        time.sleep(30)
        output = _get_console_output(config, console_id)
        if output:
            print(f"  服务器输出: {output[:500]}")
    else:
        print("  [INFO] Console API 不可用（免费套餐限制），请手动执行上述命令")


# ── 首次部署 ───────────────────────────────────────────────────────────────────


def _setup_first_time(config: dict) -> None:
    """执行首次从零开始的完整部署流程。

    1. 检查/创建 Web App
    2. 打印部署指南
    3. 创建服务器目录
    4. 构建前端
    5. 上传所有文件（前端、后端、框架、游戏数据、WSGI、Hub 示例）
    6. 虚拟环境设置提示
    7. 重载 Web App
    8. 验证部署
    """
    username = config["username"]
    token = config["api_token"]
    if not username or not token:
        print("[ERR] --setup 需要配置 API Token")
        print("   请通过 --username/--api-token 传参，或配置 ~/.pythonanywhere")
        print("   或使用 --init-config 生成配置模板")
        sys.exit(1)

    # 0. 验证 API Token
    print("\n[SETUP] 验证 API Token...")
    valid, msg = _validate_pa_token(username, token)
    if not valid:
        print(f"  [ERR] API Token 验证失败: {msg}")
        print("  请检查 Token 是否正确，或使用 --init-config 重新配置")
        sys.exit(1)
    print("  [OK] API Token 有效")

    # 打印首次部署指南概览
    _print_first_time_guide(config)

    # 1. 检查/创建 Web App
    print("\n" + "=" * 60)
    print("[SETUP] 第 1 步: 检查/创建 Web App")
    print("=" * 60)
    existing = _check_existing_webapp(config)
    if not existing:
        print("\n  当前账号下未检测到 Web App。")
        choice = input("  是否创建新的 Web App? [Y/n] ").strip().lower()
        if choice not in ("n", "no"):
            if not _create_webapp(config):
                print("\n  [WARN] Web App 创建失败，将继续上传文件。")
                print("  请稍后手动在 Web 页面创建 Web App:")
                print(f"    https://www.pythonanywhere.com/user/{username}/webapps/")
        else:
            print("\n  [SKIP] 跳过 Web App 创建。")
            print(f"  请稍后手动创建: https://www.pythonanywhere.com/user/{username}/webapps/")

    # 2. 创建目录结构
    print("\n" + "=" * 60)
    print("[SETUP] 第 2 步: 创建服务器目录结构")
    print("=" * 60)
    _create_directories_on_server(config)

    # 3. 构建前端
    print("\n" + "=" * 60)
    print("[SETUP] 第 3 步: 构建前端")
    print("=" * 60)
    _build_frontend()
    _create_zip()

    # 4. 上传前端文件
    print("\n" + "=" * 60)
    print("[SETUP] 第 4 步: 上传前端文件")
    print("=" * 60)
    _upload_dist_files(config)

    # 5. 上传后端文件
    print("\n" + "=" * 60)
    print("[SETUP] 第 5 步: 上传后端 API")
    print("=" * 60)
    _upload_backend_files(config)
    _upload_generator_tools(config)

    # 6. 上传框架文件（WSGI import 依赖）
    print("\n" + "=" * 60)
    print("[SETUP] 第 6 步: 上传计算框架")
    print("=" * 60)
    _upload_framework_src(config)
    _upload_framework_adapters(config)
    _upload_framework_init(config)

    # 7. 上传游戏数据
    print("\n" + "=" * 60)
    print("[SETUP] 第 7 步: 上传游戏数据")
    print("=" * 60)
    _upload_game_data(config)

    # 8. Hub 存储与示例
    print("\n" + "=" * 60)
    print("[SETUP] 第 8 步: Hub 市场初始化")
    print("=" * 60)
    _ensure_hub_storage(config)
    _upload_hub_samples(config)

    # 9. 其他静态资源
    print("\n" + "=" * 60)
    print("[SETUP] 第 9 步: 上传附加资源")
    print("=" * 60)
    _upload_donation_utils(config)
    _upload_donation_assets(config)
    _upload_local_backend_zip(config)

    # 10. 上传 WSGI 入口
    print("\n" + "=" * 60)
    print("[SETUP] 第 10 步: 配置 WSGI 入口")
    print("=" * 60)
    _upload_wsgi(config)

    # 11. 虚拟环境设置提示
    print("\n" + "=" * 60)
    print("[SETUP] 第 11 步: 虚拟环境设置")
    print("=" * 60)
    _setup_virtualenv_on_server(config)

    # 12. 重载 Web App
    print("\n" + "=" * 60)
    print("[SETUP] 第 12 步: 重载 Web App")
    print("=" * 60)
    _reload_webapp(config)

    # 13. 验证部署
    print("\n" + "=" * 60)
    print("[SETUP] 第 13 步: 验证部署")
    print("=" * 60)
    _verify_deployment(config)

    # 完成
    domain = config.get("domain", f"{username}.pythonanywhere.com")
    print("\n" + "=" * 60)
    print("[SETUP] 首次部署完成!")
    print(f"  访问地址: https://{domain}/compute")
    print(f"  API 健康检查: https://{domain}/api/health")
    print(f"  Hub 市场: https://{domain}/compute 页内 Calc Hub 面板")
    print("=" * 60)

    # 补充提示
    print("\n[REMINDER] 部署后可能需要的操作:")
    print("  1. 若虚拟环境未创建，请在 PA Bash 执行:")
    print(f"     mkvirtualenv --python=/usr/bin/python3.10 {config.get('project', 'calc-framework')}")
    print(f"     workon {config.get('project', 'calc-framework')}")
    print(f"     pip install -r ~/{config.get('project', 'calc-framework')}/web/backend/requirements.txt")
    print(f"     pip install -e ~/{config.get('project', 'calc-framework')}/framework/")
    print("  2. 在 PA Web 页面确认 WSGI 配置路径:")
    print(f"     /var/www/{username}_pythonanywhere_com_wsgi.py")
    print("  3. 若干员列表为空，请解压干员数据（见上方指南第 4 步备注）")


def _fast_deploy(config: dict) -> None:
    """快速部署：调用服务器 /api/admin/deploy（git pull + npm build）。

    前提：代码已 git push 到 GitHub。
    """
    domain = config.get("domain", f"{config['username']}.pythonanywhere.com")
    deploy_url = f"https://{domain}/api/admin/deploy"

    print("\n[FAST] 快速部署模式（服务器端 git pull + npm build）")
    print("  确保代码已 git push，否则服务器拉不到最新版本。")
    print()

    # Step 1: 触发部署
    print("[FAST] Step 1/3: 触发服务器部署...")
    try:
        req = Request(deploy_url, method="POST")
        with urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        if result.get("ok"):
            print(f"  [OK] {result.get('status')}")
        else:
            print(f"  [ERR] {result}")
            return
    except Exception as e:
        print(f"  [ERR] 触发失败: {e}")
        print("  可能原因：服务器未部署 /api/admin/deploy 端点（需先慢速部署一次）")
        return

    # Step 2: 轮询等待
    print("\n[FAST] Step 2/3: 等待部署完成（git pull + npm build，约 2-3 分钟）...")
    for i in range(60):
        time.sleep(5)
        try:
            req = Request(deploy_url, method="GET")
            with urlopen(req, timeout=15) as resp:
                status = json.loads(resp.read().decode("utf-8"))
            if status.get("done"):
                print(f"  [OK] 部署完成: {status.get('status')}")
                break
        except Exception:
            pass
        if i % 6 == 5:
            print(f"  仍在进行中... ({(i + 1) * 5}s)")
    else:
        print("  [WARN] 超时（5 分钟），请检查 PA 服务器状态")

    # Step 3: 重载 + 验证
    print("\n[FAST] Step 3/3: 重载 Web App...")
    _reload_webapp(config)
    print("  等待重载生效...")
    time.sleep(5)
    _verify_deployment(config)

    print(f"\n  [OK] 快速部署完成! 访问 https://{domain}/compute")


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
            f"  python {sys.argv[0]} --all               显式全自动\n\n"
            f"  python {sys.argv[0]} --init-config       初始化配置文件（交互式）\n"
            f"  python {sys.argv[0]} --guide             打印首次部署完整指南\n"
            f"  python {sys.argv[0]} --setup             首次从零部署（自动创建 Web App）\n"
            f"  python {sys.argv[0]} --fast              快速部署: git pull + npm build，~3 分钟\n\n"
            "配置文件: ~/.pythonanywhere\n"
            "环境变量: PA_USERNAME, PA_API_TOKEN, PA_PROJECT, PA_DOMAIN"
        ),
    )
    parser.add_argument("--upload", action="store_true", help="构建+打包+上传到 PythonAnywhere（需 API Token）")
    parser.add_argument("--reload", action="store_true", help="重载 PythonAnywhere Web App（需 API Token）")
    parser.add_argument(
        "--all", action="store_true", dest="do_all", help="显式全自动: 构建->打包->上传->部署->重载（需 API Token）"
    )
    parser.add_argument("--zip-only", action="store_true", help="仅重新打包 dist/（跳过 npm run build）")
    parser.add_argument(
        "--backend-only", action="store_true", help="仅上传后端 Python + WSGI 并重载（跳过前端构建/上传）"
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        dest="do_fast",
        help="快速部署: 调用服务器 /api/admin/deploy（git pull + npm build），~3 分钟",
    )
    parser.add_argument("--init-config", action="store_true", help="交互式生成配置文件模板（含 Token 验证）")
    parser.add_argument(
        "--setup",
        action="store_true",
        dest="do_setup",
        help="首次从零部署: 创建 Web App + 上传全部文件 + Hub 示例（需 API Token）",
    )
    parser.add_argument(
        "--guide",
        action="store_true",
        dest="do_guide",
        help="打印首次部署完整指南（中英文对照）",
    )
    parser.add_argument(
        "--validate-token",
        action="store_true",
        dest="validate_token",
        help="验证已配置的 API Token 是否有效",
    )
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

    # --guide: 打印首次部署指南
    if args.do_guide:
        _print_first_time_guide(config if has_api else None)
        return

    # --validate-token: 验证 Token
    if args.validate_token:
        if not has_api:
            print("[ERR] 未配置 API Token，无法验证")
            print("  请通过 --username/--api-token 传参，或配置 ~/.pythonanywhere")
            print("  或使用 --init-config 交互式配置")
            sys.exit(1)
        print(f"  验证 Token（用户: {config['username']}）...")
        valid, msg = _validate_pa_token(config["username"], config["api_token"])
        if valid:
            print("  [OK] Token 有效 — 可以正常使用 PA API")
        else:
            print(f"  [ERR] Token 验证失败: {msg}")
            sys.exit(1)
        return

    # --setup: 首次从零部署
    if args.do_setup:
        _setup_first_time(config)
        return

    # --fast: 服务器端 git pull + npm build（~3 分钟，无需上传文件）
    if args.do_fast:
        if not has_api:
            print("[ERR] --fast 需要配置 API Token")
            sys.exit(1)
        _fast_deploy(config)
        return

    # 默认行为：无参且配了 Token → 全自动；无参且无 Token → 仅构建+打包
    is_default_mode = not any([args.upload, args.reload, args.do_all, args.zip_only, args.backend_only])

    if is_default_mode:
        do_upload = has_api
        do_reload = has_api
    else:
        do_upload = args.upload or args.do_all or args.backend_only
        do_reload = args.reload or args.do_all or args.backend_only

    if (args.upload or args.do_all or args.backend_only) and not has_api:
        print("[ERR] --upload/--all 需要配置 API Token")
        print("   请通过 --username/--api-token 传参，或配置 ~/.pythonanywhere")
        print("   或使用 --init-config 生成配置模板")
        sys.exit(1)

    # Phase 1: 构建前端
    if not args.zip_only and not args.backend_only:
        _build_frontend()

    # Phase 2: 打包 zip
    if not args.backend_only:
        _create_zip()

    # Phase 3: 上传全部文件（不重载，保持站点运行）
    if do_upload:
        if not args.backend_only:
            _upload_dist_files(config)
        _upload_backend_files(config)
        _upload_generator_tools(config)
        _ensure_hub_storage(config)
        _upload_wsgi(config)
        if not args.backend_only:
            _upload_arknights_runtime(config)
            _upload_donation_utils(config)
            _upload_donation_assets(config)
            _upload_local_backend_zip(config)

    # Phase 4: 全部上传完成后一次性重载 + 验证
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
