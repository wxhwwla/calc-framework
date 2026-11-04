# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""项目作用域与路径安全。

所有 MCP 文件操作都必须经过 :class:`ProjectScope`，确保读写不会越出
``--project-dir``。
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from tools.generator.data_files import MAX_DATA_FILE_BYTES

_ADAPTER_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
_WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:")
_ALLOWED_SUFFIXES = frozenset({".json", ".py", ".md", ".txt", ".csv", ".yaml", ".yml"})


class ScopeError(ValueError):
    """项目作用域或路径安全错误。"""


class ProjectScope:
    """限制在项目目录内的路径访问器。

    Args:
        root: 项目根目录。
        adapters_dir: 适配器根目录；默认为 ``<root>/framework/adapters``。
            相对路径按 ``root`` 解析，绝对路径必须位于 ``root`` 内。
    """

    def __init__(self, root: str | Path, adapters_dir: str | Path | None = None) -> None:
        candidate = Path(os.fspath(root)).expanduser()
        if not candidate.is_dir():
            raise ScopeError(f"项目目录不存在: {candidate}")
        self.root = candidate.resolve()

        raw_adapters = Path(os.fspath(adapters_dir)).expanduser() if adapters_dir else Path("framework") / "adapters"
        if not raw_adapters.is_absolute():
            raw_adapters = self.root / raw_adapters
        resolved = raw_adapters.resolve()
        if not resolved.is_relative_to(self.root):
            raise ScopeError(f"适配器目录必须位于项目内: {resolved}")
        self.adapters_dir = resolved

    def resolve(self, rel: str | Path, *, must_exist: bool = False) -> Path:
        """将相对路径解析为项目内的绝对路径。

        Args:
            rel: 相对于项目根目录的路径。
            must_exist: 为 True 时要求目标存在。

        Returns:
            解析并校验后的绝对路径。

        Raises:
            ScopeError: 路径越界、包含非法字符或目标不存在。
        """
        raw = os.fspath(rel)
        if "\x00" in raw:
            raise ScopeError("路径包含 NUL 字符")
        if "\\" in raw:
            raise ScopeError(f"路径不能包含反斜杠: {raw!r}")

        path = Path(raw)
        if path.is_absolute() or path.drive or _WINDOWS_DRIVE_RE.match(raw):
            raise ScopeError(f"不允许绝对路径: {raw!r}")

        resolved = (self.root / path).resolve()
        if not resolved.is_relative_to(self.root):
            raise ScopeError(f"路径越界: {raw!r}")
        if must_exist and not resolved.exists():
            raise ScopeError(f"路径不存在: {raw!r}")
        return resolved

    def adapter_dir(self, adapter_id: str, *, must_exist: bool = False) -> Path:
        """解析适配器目录。

        Args:
            adapter_id: 适配器目录名，仅允许字母、数字、下划线和连字符。
            must_exist: 为 True 时要求目录存在。

        Returns:
            适配器目录的绝对路径。

        Raises:
            ScopeError: id 非法或目录越界/不存在。
        """
        if not isinstance(adapter_id, str) or not _ADAPTER_ID_RE.match(adapter_id):
            raise ScopeError(f"adapter_id 无效: {adapter_id!r}")
        if adapter_id.startswith("_"):
            raise ScopeError(f"adapter_id 不能以 _ 开头: {adapter_id!r}")

        resolved = (self.adapters_dir / adapter_id).resolve()
        if not resolved.is_relative_to(self.adapters_dir):
            raise ScopeError(f"适配器路径越界: {adapter_id!r}")
        if must_exist and not resolved.is_dir():
            raise ScopeError(f"适配器不存在: {adapter_id!r}")
        return resolved

    def read_text(self, path: Path, max_bytes: int = 256 * 1024) -> tuple[str, bool]:
        """读取项目内文本文件。

        Args:
            path: 已解析的绝对路径。
            max_bytes: 最大读取字节数。

        Returns:
            ``(文本, 是否截断)``。
        """
        resolved = self._ensure_inside(path)
        if not resolved.is_file():
            raise ScopeError(f"文件不存在: {resolved}")

        raw = resolved.read_bytes()
        truncated = len(raw) > max_bytes
        if truncated:
            raw = raw[:max_bytes]
        return raw.decode("utf-8", errors="replace"), truncated

    def write_text(
        self,
        path: Path,
        content: str,
        *,
        overwrite: bool,
        max_bytes: int = MAX_DATA_FILE_BYTES,
    ) -> int:
        """写入项目内文本文件（UTF-8 无 BOM）。

        Args:
            path: 已解析的绝对路径。
            content: 文本内容。
            overwrite: 是否允许覆盖已存在文件。
            max_bytes: 最大写入字节数。

        Returns:
            写入的字节数。

        Raises:
            ScopeError: 扩展名不允许、文件已存在或内容过大。
        """
        resolved = self._ensure_inside(path)
        if resolved.suffix.lower() not in _ALLOWED_SUFFIXES:
            raise ScopeError(f"不允许的文件扩展名: {resolved.suffix!r}")

        encoded = content.encode("utf-8")
        if len(encoded) > max_bytes:
            raise ScopeError(f"内容过大: {len(encoded)} 字节（上限 {max_bytes}）")

        if resolved.exists():
            if resolved.is_dir():
                raise ScopeError(f"目标是目录: {resolved}")
            if not overwrite:
                raise ScopeError(f"文件已存在（如需覆盖请设置 overwrite=true）: {resolved}")

        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_bytes(encoded)
        return len(encoded)

    def _ensure_inside(self, path: Path) -> Path:
        resolved = Path(path).resolve()
        if not resolved.is_relative_to(self.root):
            raise ScopeError(f"路径越界: {resolved}")
        return resolved
