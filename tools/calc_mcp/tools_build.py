# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""MCP 适配器生成/脚手架工具注册。"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from . import build
from .errors import tool_error_boundary
from .safety import ProjectScope


def register(mcp: FastMCP, scope: ProjectScope) -> None:
    """注册 build 类工具。"""

    @mcp.tool()
    @tool_error_boundary
    def scaffold_adapter(
        adapter_id: str,
        dag: dict[str, Any],
        display_name: str = "",
        game: str = "",
        description: str = "",
        overwrite: bool = False,
    ) -> dict[str, Any]:
        """Create an adapter package from a complete DAG JSON (supports unary/expr/call/subgraphs).

        先用 ``describe_schemas`` 了解节点字段。DAG 中的节点引用必须使用节点 id，
        数字字面量需先建 ``const`` 节点。校验失败会返回 ``code=BUILD``。
        """
        return build.scaffold_adapter(
            scope,
            adapter_id=adapter_id,
            display_name=display_name,
            game=game,
            description=description,
            dag=dag,
            overwrite=overwrite,
        )

    @mcp.tool()
    @tool_error_boundary
    def generate_adapter(
        adapter_id: str,
        variables: list[dict[str, Any]],
        formula_steps: list[dict[str, Any]],
        outputs: list[dict[str, Any]] | None = None,
        display_name: str = "",
        game: str = "",
        template_id: str | None = None,
        dry_run: bool = False,
        overwrite: bool = False,
    ) -> dict[str, Any]:
        """Create an adapter package from declarative variables, formula steps and outputs.

        公式步骤只支持 ``+ - * /``、``condition``、``expr``。步骤引用变量 ``name``、
        步骤 ``id`` 或数字字面量（不要写 ``user_input.atk``）。``dry_run=true`` 只预览
        文件内容，不写盘。
        """
        return build.generate_adapter(
            scope,
            adapter_id=adapter_id,
            display_name=display_name,
            game=game,
            template_id=template_id,
            variables=variables,
            formula_steps=formula_steps,
            outputs=outputs,
            dry_run=dry_run,
            overwrite=overwrite,
        )

    _ = (scaffold_adapter, generate_adapter)
