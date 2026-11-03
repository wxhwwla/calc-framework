# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""MCP 发现类工具注册。"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from . import discovery
from .errors import tool_error_boundary
from .safety import ProjectScope


def register(mcp: FastMCP, scope: ProjectScope) -> None:
    """注册模板/适配器/schema/指南工具。"""

    @mcp.tool()
    @tool_error_boundary
    def list_templates() -> dict[str, Any]:
        """List calculator templates that can seed a new adapter.

        返回 ``framework/adapters`` 下可用的模板（下划线开头的内部目录已排除）。
        每个模板包含 id、名称、分类和描述；将 id 传给 ``generate_adapter`` 的
        ``template_id`` 即可复用模板的函数与元数据。
        """
        return discovery.list_templates(scope)

    @mcp.tool()
    @tool_error_boundary
    def describe_schemas() -> dict[str, Any]:
        """Describe DAG node fields, variable types, generator steps and expression functions.

        写 DAG 或公式前先调用。重点：``formula_steps`` 的 lhs/rhs/cond 等字段引用
        变量 ``name``、步骤 ``id`` 或数字字面量，不是 ``user_input.xxx`` 路径。
        """
        return discovery.describe_schemas()

    @mcp.tool()
    @tool_error_boundary
    def read_guide(topic: str) -> dict[str, Any]:
        """Read a whitelisted project guide by topic.

        可用 topic：overview、adapter、dag、generator、quickstart、context、
        pack_format、adapter_layout。内容超过约 60 KB 时会截断，并通过
        ``truncated`` 标记。
        """
        return discovery.read_guide(scope, topic)

    @mcp.tool()
    @tool_error_boundary
    def list_adapters() -> dict[str, Any]:
        """List existing adapter packages with metadata and layout availability."""
        return discovery.list_adapters(scope)

    _ = (list_templates, describe_schemas, read_guide, list_adapters)
