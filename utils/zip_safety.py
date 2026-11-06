# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""ZIP 条目安全校验：防 Zip Slip、符号链接与资源耗尽。"""

from __future__ import annotations

import stat
import zipfile
from pathlib import Path, PurePosixPath, PureWindowsPath

__all__ = ["ZipSafetyError", "safe_extractall", "validate_zip_member_name"]


class ZipSafetyError(ValueError):
    """ZIP 条目非法或解压越界。"""


def validate_zip_member_name(name: str) -> PurePosixPath:
    """校验 ZIP 条目名并返回 POSIX 路径。

    Args:
        name: ZIP 内条目名。

    Returns:
        解析后的 ``PurePosixPath``。

    Raises:
        ZipSafetyError: 名称为空、含 NUL/反斜杠、绝对路径、盘符或 ``..``。
    """
    if not name or "\x00" in name or "\\" in name:
        raise ZipSafetyError(f"ZIP 条目名非法: {name!r}")

    pure = PurePosixPath(name)
    if not pure.parts or pure.is_absolute() or PureWindowsPath(name).drive or ".." in pure.parts:
        raise ZipSafetyError(f"ZIP 条目越界: {name!r}")
    return pure


def safe_extractall(
    zf: zipfile.ZipFile,
    destination: str | Path,
    *,
    max_entries: int = 10_000,
    max_total_bytes: int = 64 * 1024 * 1024,
) -> None:
    """校验全部条目后解压；任一非法条目则整体拒绝。

    Args:
        zf: 已打开的 ZIP 文件。
        destination: 解压目标目录。
        max_entries: 条目数上限。
        max_total_bytes: 解压后总字节数上限。

    Raises:
        ZipSafetyError: 条目过多、解压后总大小超限、条目名非法或含符号链接。
    """
    infos = zf.infolist()
    if len(infos) > max_entries:
        raise ZipSafetyError(f"ZIP 条目过多（上限 {max_entries}）")

    root = Path(destination).resolve()
    total_bytes = 0
    for info in infos:
        validate_zip_member_name(info.filename)
        if info.is_dir():
            continue
        if stat.S_ISLNK(info.external_attr >> 16):
            raise ZipSafetyError(f"ZIP 条目不允许符号链接: {info.filename!r}")
        total_bytes += info.file_size
        if total_bytes > max_total_bytes:
            raise ZipSafetyError(f"ZIP 解压后超过 {max_total_bytes // (1024 * 1024)} MiB 限制")

    zf.extractall(root)
