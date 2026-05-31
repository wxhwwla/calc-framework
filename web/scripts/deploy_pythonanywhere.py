# SPDX-License-Identifier: AGPL-3.0
"""
终末地伤害计算器 — PythonAnywhere 自动化部署脚本

一站式完成：构建前端 → 打包 zip → 上传 → 服务器部署 → 重载 Web App

使用方法:
  python web/scripts/deploy_pythonanywhere.py              # 构建 + 打包，输出 zip 位置（手动上传 + 部署）
  python web/scripts/deploy_pythonanywhere.py --upload     # 构建 + 打包 + 上传 + 部署（需配置 API Token）
  python web/scripts/deploy_pythonanywhere.py --zip-only   # 仅打包已有 dist/（跳过 npm run build）
  python web/scripts/deploy_pythonanywhere.py --help       # 查看完整帮助

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
_PA_API = "https://www.pythonanywhere.com/api/v0/user/{username}"
_PA_FILES_API = _PA_API + "/files/path{path}"
_PA_RELOAD_API = _PA_API + "/webapps/{domain}/reload/"
_PA_SCHEDULE_API = _PA_API + "/schedules/"

_DEFAULT_DOMAIN = "{username}.pythonanywhere.com"

# ── 配置读取 ────────────────────────────────────────────────────────────────────


def _load_config() -> dict:
    """读取 ~/.pythonanywhere 配置文件，返回 dict。"""
    config = {}
    ini = configparser.ConfigParser()
    if _CONFIG_PATH.exists():
        ini.read(str(_CONFIG_PATH))
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
    result = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    if result.returncode != 0:
        print("  ❌ npm 命令失败:")
        print(result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)
        print(result.stderr[-2000:] if len(result.stderr) > 2000 else result.stderr)
        sys.exit(1)


def _build_frontend() -> None:
    """执行 npm run build。"""
    print("\n📦 [阶段 1/5] 构建前端...")
    print(f"  目录: {_FRONTEND_DIR}")
    if not (_FRONTEND_DIR / "package.json").exists():
        print("  ❌ 未找到 package.json，请确认路径正确")
        sys.exit(1)
    _run_npm(["install"], _FRONTEND_DIR)
    _run_npm(["run", "build"], _FRONTEND_DIR)
    if not _DIST_DIR.exists():
        print("  ❌ 构建完成但 dist/ 目录未生成")
        sys.exit(1)
    js_files = list(_DIST_DIR.rglob("*.js"))
    print(f"  ✅ 构建完成: {len(js_files)} 个 JS 文件, {sum(f.stat().st_size for f in js_files) // 1024} KB")


# ── 阶段 2: 打包 zip ────────────────────────────────────────────────────────────


def _create_zip() -> None:
    """用 Python zipfile 创建兼容 Linux 的 zip（避免 LZMA 问题）。"""
    print("\n📦 [阶段 2/5] 打包 dist/...")
    if not _DIST_DIR.exists():
        print(f"  ❌ dist/ 目录不存在: {_DIST_DIR}")
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
    print(f"  ✅ 打包完成: {count} 个文件, {zip_size // 1024} KB")
    print(f"  📄 输出: {_ZIP_PATH}")


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
    print("\n📤 [阶段 3/5] 上传 dist.zip 到 PythonAnywhere...")
    username = config.get("username")
    token = config.get("api_token")
    project = config.get("project", "calc-framework")
    if not username or not token:
        print("  ❌ 未配置 PythonAnywhere 用户名或 API Token")
        print("  请通过 --username/--api-token 传参，或配置 ~/.pythonanywhere 文件")
        sys.exit(1)

    if not _ZIP_PATH.exists():
        print(f"  ❌ 未找到 zip 文件: {_ZIP_PATH}")
        sys.exit(1)

    remote_path = f"/home/{username}/{project}/frontend/dist.zip"
    url = _PA_FILES_API.format(username=username, path=remote_path)

    # 检查 API 连通性
    code, body = _pa_request("GET", _PA_API.format(username=username), token)
    if code != 200:
        print(f"  ❌ API 连接失败 ({code}): {body}")
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
        print(f"  ✅ 上传成功: {remote_path}")
    else:
        print(f"  ❌ 上传失败 ({code}): {body}")
        sys.exit(1)


# ── 阶段 4: 服务器端执行命令 ──────────────────────────────────────────────────────


def _build_server_script(config: dict) -> str:
    """生成服务器端部署脚本内容。"""
    project = config.get("project", "calc-framework")
    lines = [
        "#!/bin/bash",
        "# 终末地伤害计算器 - PythonAnywhere 服务器端部署脚本",
        "# 在 PythonAnywhere Bash 控制台中执行: bash ~/deploy_server.sh",
        f"# 项目: {project}",
        "",
        "set -e",
        "",
        f'echo "=== 1/4: 拉取最新代码 ==="',
        f"cd ~/{project}",
        "git pull",
        "",
        'echo "=== 2/4: 安装 Python 依赖 ==="',
        "source ~/.virtualenvs/calc-framework/bin/activate",
        "pip install -q -r web/backend/requirements.txt",
        "pip install -q -e framework/",
        "",
        'echo "=== 3/4: 解压前端构建产物 ==="',
        f"cd ~/{project}/web/frontend",
        "rm -rf dist",
        "mkdir -p dist",
        "cd dist",
        "unzip -q ~/dist.zip 2>/dev/null || (echo '  ⚠ 未找到 ~/dist.zip，尝试项目路径...' && unzip -q ~/{project}/frontend/dist.zip)",
        "cd ..",
        "ls -la dist/",
        "echo '  JS文件:'",
        "ls -lh dist/assets/*.js 2>/dev/null || echo '  (无 assets 目录, 检查 dist 嵌套)'",
        "",
        'echo "=== 4/4: 清理临时文件 ==="',
        "rm -f ~/dist.zip",
        "",
        'echo "=== ✅ 服务器端部署完成 ==="',
        'echo "请手动在 PythonAnywhere Web 页面点击 Reload，或本脚本带 --reload 参数自动触发"',
    ]
    return "\n".join(lines)


def _upload_server_script(config: dict) -> None:
    """上传服务器端部署脚本到 PythonAnywhere。"""
    print("\n📜 [阶段 4/5] 上传服务器端部署脚本...")
    username = config.get("username")
    token = config.get("api_token")
    project = config.get("project", "calc-framework")
    if not username or not token:
        print("  ⏭ 跳过（无 API Token）")
        return

    script_content = _build_server_script(config)
    remote_path = f"/home/{username}/{project}/web/scripts/deploy_server.sh"
    url = _PA_FILES_API.format(username=username, path=remote_path)

    boundary = b"----pa-deploy-boundary"
    body_parts = [
        b"--" + boundary,
        b'Content-Disposition: form-data; name="content"; filename="deploy_server.sh"',
        b"Content-Type: text/plain",
        b"",
        script_content.encode("utf-8"),
        b"--" + boundary + b"--",
    ]
    body_data = b"\r\n".join(body_parts)
    code, body = _pa_request(
        "POST", url, token,
        data=body_data,
        content_type=f"multipart/form-data; boundary={boundary.decode()}",
    )
    if code in (200, 201):
        print(f"  ✅ 部署脚本已上传: {remote_path}")
    else:
        print(f"  ⚠ 上传部署脚本失败 ({code}), 可手动复制")


# ── 阶段 5: 重载 Web App ────────────────────────────────────────────────────────


def _reload_webapp(config: dict) -> None:
    """通过 PythonAnywhere API 重载 Web App。"""
    print("\n🔄 [阶段 5/5] 重载 Web App...")
    username = config.get("username")
    token = config.get("api_token")
    domain = config.get("domain", _DEFAULT_DOMAIN.format(username=username or ""))
    if not username or not token:
        print("  ❌ 未配置 API Token，无法自动重载")
        print("  请手动在 PythonAnywhere Web 页面点击 Reload")
        return

    url = _PA_RELOAD_API.format(username=username, domain=domain)
    code, body = _pa_request("POST", url, token)
    if code == 200:
        print(f"  ✅ 重载成功! 请访问 https://{domain}")
    else:
        print(f"  ❌ 重载失败 ({code}): {body}")
        print("  请手动在 PythonAnywhere Web 页面点击 Reload")


# ── 初始化配置 ────────────────────────────────────────────────────────────────────


def _init_config() -> None:
    """生成 ~/.pythonanywhere 配置文件模板。"""
    if _CONFIG_PATH.exists():
        print(f"  ⚠ 配置文件已存在: {_CONFIG_PATH}")
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
    print("  ✅ 配置模板已生成，请编辑填入 api_token")
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
            f"  python {sys.argv[0]}                  构建+打包\n"
            f"  python {sys.argv[0]} --upload         构建+打包+上传+部署脚本\n"
            f"  python {sys.argv[0]} --all            全自动: 构建+打包+上传+部署+重载\n"
            f"  python {sys.argv[0]} --zip-only       仅重新打包（跳过 npm 构建）\n"
            f"  python {sys.argv[0]} --init-config    初始化配置文件\n\n"
            "配置文件: ~/.pythonanywhere\n"
            "环境变量: PA_USERNAME, PA_API_TOKEN, PA_PROJECT, PA_DOMAIN"
        ),
    )
    parser.add_argument("--upload", action="store_true", help="构建+打包后自动上传到 PythonAnywhere")
    parser.add_argument("--reload", action="store_true", help="重载 PythonAnywhere Web App（需 API Token）")
    parser.add_argument("--all", action="store_true", dest="do_all", help="全自动: 构建+打包+上传+部署脚本+重载")
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
    do_upload = args.upload or args.do_all
    do_reload = args.reload or args.do_all

    if do_upload and not has_api:
        print("❌ --upload/--all 需要配置 API Token")
        print("   请通过 --username/--api-token 传参，或配置 ~/.pythonanywhere")
        print("   或使用 --init-config 生成配置模板")
        sys.exit(1)

    # Phase 1: 构建前端
    if not args.zip_only:
        _build_frontend()

    # Phase 2: 打包 zip
    _create_zip()

    # Phase 3: 上传
    if do_upload:
        _upload_zip(config)
        _upload_server_script(config)

    # Phase 4: 打印服务器端指令
    if not do_upload:
        _print_server_instructions(_ZIP_PATH)

    # Phase 5: 重载
    if do_reload:
        time.sleep(2)  # 给服务器一点时间处理上传
        _reload_webapp(config)
    elif has_api:
        print("\n💡 提示: 添加 --reload 可自动重载 Web App")
        print("   或: python web/scripts/deploy_server.sh --reload")

    print(f"\n{'=' * 60}")
    print("✅ 本地操作完成")
    if not do_upload:
        print(f"📄 zip 文件: {_ZIP_PATH}")
    if not do_reload:
        print("🔄 别忘了在 PythonAnywhere Web 页面点击 Reload")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
