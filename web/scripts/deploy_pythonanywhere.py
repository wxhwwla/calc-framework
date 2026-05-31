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
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from zipfile import ZipFile, ZIP_DEFLATED

# ── 路径 ──────────────────────────────────────────────────────────────────────
_REPO_ROOT = Path(__file__).resolve().parents[2]
_FRONTEND_DIR = _REPO_ROOT / "web" / "frontend"
_DIST_DIR = _FRONTEND_DIR / "dist"
_SCRIPTS_DIR = _REPO_ROOT / "web" / "scripts"
_ZIP_PATH = _REPO_ROOT / "dist_pa.zip"
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
    url = _PA_FILES_API.format(username=username, path=remote_path)

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

            url = _PA_FILES_API.format(username=username, path=remote_path)
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
                    dummy_url = _PA_FILES_API.format(
                        username=username, path=f"{dist_base}{parent}/.keep")
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
        url = _PA_FILES_API.format(username=username, path=remote_path)
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
    url = _PA_FILES_API.format(username=username, path=remote_path)

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

    # Phase 3: 上传 + 部署（上传 zip + 逐文件上传 dist + 后端代码 + 本地后端 zip）
    if do_upload:
        _upload_dist_files(config)
        _upload_backend_files(config)
        _upload_local_backend_zip(config)

    # Phase 4: 重载
    if do_reload and has_api:
        _reload_webapp(config)
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
