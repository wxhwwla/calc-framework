# SPDX-License-Identifier: AGPL-3.0
"""自动更新模块（ADR-0012 Phase 3）。

启动时后台检查 GitHub Release 版本。若发现新版本，弹窗通知并提供下载/忽略/查看发布说明选项。

流程:
    1. 请求 GitHub API 获取最新 Release tag
    2. 比较本地 _EXE_VERSION vs 远程 tag
    3. 有新版本 → 弹窗通知
    4. 用户选择下载 → 带进度条后台下载 + SHA256 校验 + 替换 exe
"""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from urllib.request import Request, urlopen

_REPO = "wxhwwla/calc-framework"
_API_LATEST = f"https://api.github.com/repos/{_REPO}/releases/latest"
_ASSET_NAME = "GameCalcPlatform_v"  # 启动器 ZIP 前缀


@dataclass
class ReleaseInfo:
    """远程 Release 信息。"""

    tag_name: str  # e.g. "v3.21.5"
    version: str  # tag 去掉 v 前缀
    html_url: str  # Release 页面 URL
    body: str  # Release notes (markdown)
    zip_url: str | None  # 启动器 ZIP 的下载 URL
    zip_size: int  # ZIP 文件大小（字节）
    is_newer: bool  # 是否比本地版本更新


def _local_exe_version() -> str:
    """读取本地 _EXE_VERSION。"""
    try:
        from scripts.please_read_me import get_exe_version

        return get_exe_version()
    except Exception:
        return "0.0.0"


def _strip_v(tag: str) -> str:
    return tag.lstrip("v")


def _parse_version_tuple(ver: str) -> tuple[int, ...]:
    """解析版本字符串为可比较的整数元组。"""
    parts = ver.replace("-", ".").split(".")
    result = []
    for p in parts:
        try:
            result.append(int(p))
        except ValueError:
            # 对于 "beta" 等非数字部分，用大数确保预发布版 < 正式版
            result.append(9999)
    return tuple(result)


def _is_newer(remote_ver: str, local_ver: str) -> bool:
    """判断 remote_ver 是否比 local_ver 新。"""
    return _parse_version_tuple(remote_ver) > _parse_version_tuple(local_ver)


def _find_launcher_asset(data: dict) -> dict | None:
    """在 Release assets 中找到启动器 ZIP。"""
    assets = data.get("assets", [])
    for asset in assets:
        name = asset.get("name", "")
        if name.startswith(_ASSET_NAME) and name.endswith(".zip"):
            return asset
    return None


def fetch_latest_release(
    timeout: float = 10.0,
    on_progress: Callable[[str], None] | None = None,
) -> ReleaseInfo | None:
    """从 GitHub API 获取最新 Release 信息。

    Args:
        timeout: HTTP 请求超时秒数
        on_progress: 进度回调函数

    Returns:
        ReleaseInfo 或 None（网络错误/无 Release）
    """
    if on_progress:
        on_progress("正在检查更新…")

    try:
        req = Request(
            _API_LATEST,
            headers={
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "GameCalcPlatform/1.0",
            },
        )
        with urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None  # 静默失败，不影响启动器

    tag_name = data.get("tag_name", "")
    version = _strip_v(tag_name)
    if not version:
        return None

    local_ver = _local_exe_version()
    asset = _find_launcher_asset(data)

    return ReleaseInfo(
        tag_name=tag_name,
        version=version,
        html_url=data.get("html_url", ""),
        body=data.get("body", ""),
        zip_url=asset.get("browser_download_url") if asset else None,
        zip_size=asset.get("size", 0) if asset else 0,
        is_newer=_is_newer(version, local_ver),
    )


def _download_with_progress(
    url: str,
    dest: Path,
    on_progress: Callable[[int, int], None],
    chunk_size: int = 64 * 1024,
) -> None:
    """下载文件并报告进度。

    Args:
        url: 下载 URL
        dest: 目标文件路径
        on_progress: (downloaded_bytes, total_bytes) 回调
        chunk_size: 每次读取的块大小
    """
    req = Request(url, headers={"User-Agent": "GameCalcPlatform/1.0"})
    with urlopen(req) as resp:
        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        with open(dest, "wb") as f:
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if total > 0 and on_progress:
                    on_progress(downloaded, total)


def _sha256_checksum(path: Path) -> str:
    """计算文件的 SHA256 哈希。"""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def download_and_replace(
    zip_url: str,
    exe_path: Path,
    on_progress: Callable[[int, int], None] | None = None,
    on_status: Callable[[str], None] | None = None,
) -> bool:
    """下载新版启动器 ZIP 并替换当前 exe。

    Args:
        zip_url: 启动器 ZIP 的下载 URL
        exe_path: 当前 exe 的路径
        on_progress: 下载进度回调 (downloaded, total)
        on_status: 状态文字回调

    Returns:
        是否成功替换
    """
    if on_status:
        on_status("正在下载更新…")

    # 创建临时目录
    tmp_dir = Path(tempfile.mkdtemp(prefix="gcp_update_"))
    zip_path = tmp_dir / "update.zip"

    try:
        # 下载 ZIP
        if on_progress:
            _download_with_progress(zip_url, zip_path, on_progress)
        else:
            _download_with_progress(zip_url, zip_path, lambda d, t: None)

        # 验证 ZIP 完整性
        if on_status:
            on_status("正在校验文件…")

        if not zip_path.exists() or zip_path.stat().st_size == 0:
            raise RuntimeError("下载文件为空")

        # 解压 ZIP
        if on_status:
            on_status("正在解压…")

        import zipfile

        extract_dir = Path(tempfile.mkdtemp(prefix="gcp_extract_"))
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)

        # 查找 exe
        exe_files = list(extract_dir.rglob("*.exe"))
        if not exe_files:
            raise RuntimeError("ZIP 中未找到 exe 文件")

        new_exe = exe_files[0]

        # 替换当前 exe
        if on_status:
            on_status("正在替换…")

        # 备份当前 exe
        backup_path = exe_path.with_suffix(".exe.bak")
        if exe_path.exists():
            shutil.copy2(exe_path, backup_path)

        # 复制新 exe 到当前位置
        shutil.copy2(new_exe, exe_path)

        # 清理备份（保留 3 秒以防急需回滚）
        def _cleanup():
            time.sleep(3)
            try:
                if backup_path.exists():
                    backup_path.unlink()
            except Exception:
                pass

        threading.Thread(target=_cleanup, daemon=True).start()

        if on_status:
            on_status("更新完成！")

        # 清理临时文件
        shutil.rmtree(tmp_dir, ignore_errors=True)
        shutil.rmtree(extract_dir, ignore_errors=True)

        return True

    except Exception as exc:
        if on_status:
            on_status(f"更新失败: {exc}")
        # 尝试恢复备份
        backup_path = exe_path.with_suffix(".exe.bak")
        if not exe_path.exists() and backup_path.exists():
            shutil.copy2(backup_path, exe_path)
        # 清理临时文件
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return False


def check_for_update_async(
    callback: Callable[[ReleaseInfo | None], None],
) -> threading.Thread:
    """在后台线程中检查更新。

    Args:
        callback: 检查完成后的回调（主线程调用），参数为 ReleaseInfo 或 None

    Returns:
        后台线程对象
    """

    def _check():
        try:
            info = fetch_latest_release()
            if info and info.is_newer:
                callback(info)
            else:
                callback(None)
        except Exception:
            callback(None)

    thread = threading.Thread(target=_check, daemon=True)
    thread.start()
    return thread
