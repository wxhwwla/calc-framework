# SPDX-License-Identifier: AGPL-3.0
"""自动更新模块 — 检查 GitHub Release → 下载 → 校验 → 替换。

用法::

    from utils.updater import check_update, download_update, extract_and_replace

    info = check_update(current_version)
    if info:
        zip_path = download_update(info, progress_callback)
        success = extract_and_replace(zip_path, target_dir)
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from urllib.error import URLError
from urllib.request import Request, urlopen

GITHUB_OWNER = "wxhwwla"
GITHUB_REPO = "calc-framework"
RELEASE_API = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"

_PROGRESS_CALLBACK = Callable[[int, int], None]
_STATUS_CALLBACK = Callable[[str], None]


@dataclass
class UpdateInfo:
    latest_version: str
    download_url: str
    asset_name: str
    asset_size: int
    release_notes: str
    published_at: str = ""


def _get_latest_release_data() -> dict[str, Any] | None:
    """获取最新 Release 的 API 响应。"""
    req = Request(RELEASE_API, headers={
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "endfield-damage-calc/1.0",
    })
    try:
        with urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (URLError, OSError, json.JSONDecodeError):
        return None


def check_update(current_version: str) -> UpdateInfo | None:
    """检查是否有新版本。

    Args:
        current_version: 当前版本号（如 ``0.6.0-beta``，对应 _EXE_VERSION）

    Returns:
        有新版本时返回 UpdateInfo，否则返回 None
    """
    data = _get_latest_release_data()
    if data is None:
        return None

    tag = data.get("tag_name", "")
    if not tag.startswith("v"):
        return None
    latest = tag[1:]

    if latest == current_version:
        return None

    assets = data.get("assets", [])
    if not assets:
        return None

    target_asset = assets[0]
    asset_name: str = target_asset.get("name", "release.zip")
    asset_size: int = target_asset.get("size", 0)
    download_url: str = target_asset.get("browser_download_url", "")

    if not download_url:
        return None

    release_notes: str = data.get("body", "")
    published_at: str = data.get("published_at", "")

    return UpdateInfo(
        latest_version=latest,
        download_url=download_url,
        asset_name=asset_name,
        asset_size=asset_size,
        release_notes=release_notes[:2000],
        published_at=published_at[:10],
    )


def download_update(
    update: UpdateInfo,
    progress: _PROGRESS_CALLBACK | None = None,
    status: _STATUS_CALLBACK | None = None,
) -> Path:
    """下载更新包到临时目录。

    Args:
        update: UpdateInfo
        progress: 进度回调 (downloaded_bytes, total_bytes)
        status: 状态回调 (status_message)

    Returns:
        下载后的 ZIP 文件路径
    """
    temp_dir = Path(tempfile.gettempdir()) / "egdc_updater"
    temp_dir.mkdir(parents=True, exist_ok=True)
    dest = temp_dir / update.asset_name

    if status:
        status(f"正在下载 {update.asset_name} ({update.asset_size // 1024 // 1024} MB)...")

    req = Request(update.download_url, headers={
        "User-Agent": "endfield-damage-calc/1.0",
    })
    with urlopen(req, timeout=300) as resp:
        total = int(resp.headers.get("content-length", update.asset_size))
        downloaded = 0
        chunk_size = 8192
        with open(dest, "wb") as f:
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if progress:
                    progress(downloaded, total)

    if status:
        status("下载完成，正在校验...")

    return dest


def verify_zip(zip_path: Path) -> bool:
    """校验 ZIP 文件的完整性。"""
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            bad = zf.testzip()
            return bad is None
    except (zipfile.BadZipFile, OSError):
        return False


def _get_target_dir() -> Path:
    """获取安装目录（当前仓库根目录）。"""
    return Path(__file__).resolve().parent.parent


def extract_and_replace(
    zip_path: Path,
    target_dir: str | Path | None = None,
) -> bool:
    """解压更新包并替换文件。

    将 ZIP 解压到临时目录，然后复制替换目标目录中的文件。
    对于当前正在运行的文件（如 exe），使用 subprocess 延迟替换。

    Args:
        zip_path: 已下载的更新包路径
        target_dir: 目标安装目录（None = 自动检测仓库根目录）

    Returns:
        是否成功
    """
    if target_dir is None:
        target_dir = _get_target_dir()
    target = Path(target_dir)

    extract_dir = Path(tempfile.gettempdir()) / "egdc_extract"
    if extract_dir.exists():
        shutil.rmtree(extract_dir)
    extract_dir.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)
    except (zipfile.BadZipFile, OSError):
        return False

    is_frozen = getattr(sys, "frozen", False)

    for item in extract_dir.rglob("*"):
        if item.is_file():
            rel = item.relative_to(extract_dir)
            dest = target / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(item, dest)
            except PermissionError:
                if is_frozen:
                    _schedule_replace(item, dest)

    shutil.rmtree(extract_dir)
    return True


def _schedule_replace(src: Path, dst: Path) -> None:
    """使用批处理脚本延迟替换被占用的文件。"""
    if not getattr(sys, "frozen", False):
        return

    script = _generate_replace_script(src, dst)
    script_path = Path(tempfile.gettempdir()) / "egdc_replace.bat"
    script_path.write_text(script, encoding="utf-8")
    subprocess.Popen(
        ["cmd", "/c", str(script_path)],
        shell=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )


def _generate_replace_script(src: Path, dst: Path) -> str:
    return f"""@echo off
timeout /t 2 /nobreak >nul
copy /y "{src}" "{dst}" >nul
del "{src}" >nul 2>nul
if exist "{dst}" (
    start "" "{dst}"
)
del "%~f0"
"""


def restart_launcher() -> None:
    """重启启动器。"""
    script = Path(tempfile.gettempdir()) / "egdc_restart.bat"
    launcher = Path(sys.argv[0]).resolve()
    script.write_text(
        f"""@echo off
timeout /t 1 /nobreak >nul
start "" "{launcher}"
del "%~f0"
""",
        encoding="utf-8",
    )
    subprocess.Popen(
        ["cmd", "/c", str(script)],
        shell=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    sys.exit(0)
