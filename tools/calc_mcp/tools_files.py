# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""MCP 适配包文件读写工具注册。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from .errors import tool_error_boundary
from .safety import ProjectScope, ScopeError

_READABLE_SUFFIXES = frozenset({".json", ".py", ".md", ".txt", ".csv", ".yaml", ".yml"})
_MAX_LISTED_FILES = 5000


def register(mcp: FastMCP, scope: ProjectScope) -> None:
    """注册适配包文件工具。"""

    @mcp.tool()
    @tool_error_boundary
    def list_adapter_files(adapter_id: str) -> dict[str, Any]:
        """List files inside one adapter package with relative paths and byte sizes.

        ``adapter_id`` 是 ``framework/adapters`` 下的目录名（不是显示名称）。
        """
        base = scope.adapter_dir(adapter_id, must_exist=True)
        files: list[dict[str, Any]] = []
        for path in sorted(base.rglob("*")):
            if len(files) >= _MAX_LISTED_FILES:
                break
            if not path.is_file() or not path.resolve().is_relative_to(base):
                continue
            files.append(
                {
                    "path": path.relative_to(base).as_posix(),
                    "size": path.stat().st_size,
                }
            )
        return {"ok": True, "adapter_id": adapter_id, "files": files}

    @mcp.tool()
    @tool_error_boundary
    def read_adapter_file(adapter_id: str, path: str) -> dict[str, Any]:
        """Read a UTF-8 text file inside an adapter package (truncated at 256 KiB).

        仅允许 .json/.py/.md/.txt/.csv/.yaml/.yml。
        """
        target = _adapter_path(scope, adapter_id, path)
        if target.suffix.lower() not in _READABLE_SUFFIXES:
            raise ScopeError(f"不支持读取该文件类型: {target.suffix!r}")
        content, truncated = scope.read_text(target, max_bytes=256 * 1024)
        return {
            "ok": True,
            "adapter_id": adapter_id,
            "path": target.relative_to(scope.adapter_dir(adapter_id, must_exist=True)).as_posix(),
            "content": content,
            "truncated": truncated,
        }

    @mcp.tool()
    @tool_error_boundary
    def write_adapter_file(
        adapter_id: str,
        path: str,
        content: str,
        overwrite: bool = False,
    ) -> dict[str, Any]:
        """Write a UTF-8 text file inside an adapter package (max 512 KiB).

        扩展名白名单：.json/.py/.md/.txt/.csv/.yaml/.yml。默认不覆盖已有文件。
        """
        target = _adapter_path(scope, adapter_id, path)
        written = scope.write_text(target, content, overwrite=overwrite)
        base = scope.adapter_dir(adapter_id, must_exist=True)
        return {
            "ok": True,
            "adapter_id": adapter_id,
            "path": target.relative_to(base).as_posix(),
            "bytes": written,
        }

    _ = (list_adapter_files, read_adapter_file, write_adapter_file)


def _adapter_path(scope: ProjectScope, adapter_id: str, rel: str) -> Path:
    base = scope.adapter_dir(adapter_id, must_exist=True)
    raw = str(rel or "")
    if not raw or "\x00" in raw or "\\" in raw:
        raise ScopeError(f"路径非法: {rel!r}")

    candidate = Path(raw)
    if candidate.is_absolute() or candidate.drive:
        raise ScopeError(f"不允许绝对路径: {rel!r}")

    resolved = (base / candidate).resolve()
    if not resolved.is_relative_to(base):
        raise ScopeError(f"路径越界: {rel!r}")
    return resolved
