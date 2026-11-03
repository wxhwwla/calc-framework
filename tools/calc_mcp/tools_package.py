# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""MCP .calcpack 导出/导入工具注册。"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from . import package
from .errors import tool_error_boundary
from .safety import ProjectScope


def register(mcp: FastMCP, scope: ProjectScope) -> None:
    """注册 package 类工具。"""

    @mcp.tool()
    @tool_error_boundary
    def export_calcpack(
        adapter_id: str,
        output_path: str = "",
        force: bool = False,
    ) -> dict[str, Any]:
        """Export an adapter package to a .calcpack ZIP and verify the archive contents.

        默认输出到 ``dist/<adapter_id>.calcpack``。导出前会做完整校验；校验失败时
        需显式设置 ``force=true``。包内包含 meta/DAG/layout/attr_schema/data/assets。
        """
        return package.export_calcpack(
            scope,
            adapter_id=adapter_id,
            output_path=output_path,
            force=force,
        )

    @mcp.tool()
    @tool_error_boundary
    def import_calcpack(calcpack_path: str, adapter_id: str) -> dict[str, Any]:
        """Import a .calcpack into an adapter directory and validate the result.

        ``calcpack_path`` 必须是项目内相对路径；目标目录已存在时拒绝导入。
        返回导入的文件列表与自动校验摘要。
        """
        return package.import_calcpack(
            scope,
            calcpack_path=calcpack_path,
            adapter_id=adapter_id,
        )

    _ = (export_calcpack, import_calcpack)
