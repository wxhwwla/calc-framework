# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""MCP 适配器校验/冒烟工具注册。"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from . import verify
from .errors import tool_error_boundary
from .safety import ProjectScope


def register(mcp: FastMCP, scope: ProjectScope) -> None:
    """注册 verify 类工具。"""

    @mcp.tool()
    @tool_error_boundary
    def validate_adapter(adapter_id: str) -> dict[str, Any]:
        """Validate meta/DAG/layout/attr_schema and report all errors without failing fast.

        返回 ``{valid, errors[], warnings[], stats}``。错误项包含 ``code``、
        ``message`` 与 ``file``，可据此直接定位并修复。
        """
        return verify.validate_adapter(scope, adapter_id)

    @mcp.tool()
    @tool_error_boundary
    def smoke_test_adapter(
        adapter_id: str,
        context: dict[str, Any] | None = None,
        include_node_values: bool = False,
    ) -> dict[str, Any]:
        """Evaluate an adapter with variable defaults plus optional context overrides.

        会执行适配包内的 ``functions.py``，仅对本地仓库中的开发者适配包使用。
        返回 outputs、实际执行的节点数与（可选）全部 node_values。
        """
        return verify.smoke_test_adapter(
            scope,
            adapter_id,
            context=context,
            include_node_values=include_node_values,
        )

    _ = (validate_adapter, smoke_test_adapter)
