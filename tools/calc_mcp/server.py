# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""MCP 服务器装配。

仅使用 stdio 传输；所有日志必须写入 stderr，stdout 保留给 JSON-RPC。
"""

from __future__ import annotations

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from . import tools_build, tools_discovery, tools_files, tools_package, tools_verify
from .safety import ProjectScope

_INSTRUCTIONS = """\
你是游戏伤害计算器的构建助手。所有操作都限制在用户指定的项目目录内。

推荐流程：
1. list_templates / describe_schemas 了解模板与 DAG 字段。
2. generate_adapter（声明式公式）或 scaffold_adapter（完整 DAG）创建适配包。
3. validate_adapter 修复所有 errors，再用 smoke_test_adapter 检查数值。
4. export_calcpack 导出 .calcpack；import_calcpack 可回环验证。

注意：
- formula_steps 引用变量 name、步骤 id 或数字字面量，不要写 user_input.atk。
- expr 支持 + - * /、比较（< <= > >= == !=）、and/or/not、三元 a if cond else b；
  不支持 in/is/lambda/属性访问。
- generate_adapter.data_files 可提供 character/weapon/equipment/enemy 实体记录
  （每条含非空字符串 名称）；提供非空记录列表的来源视为绑定，其变量保留命名空间
  并由查看器实体下拉提供；未绑定或空列表来源的变量自动改写为 user_input 输入。
- 变量可带 min/max 与 ui_control（suffix/step/widget/options）；百分比输入用
  type=float + ui_control.suffix="%"，并在表达式中除以 100。
- generate_adapter.entity_selectors 可把实体下拉改为多级级联（如 舰船种类→舰船→武器）；
  来源须已绑定非空 data_files，末级 field 必须为 名称。
- generate_adapter.entity_detail 可在查看器最左侧显示当前实体字段明细；字段必须存在于
  已绑定数据文件。generate_adapter.entity_input_rules 可按实体字段禁用无关输入
  （例如不需要母舰时灰显母舰加成），disable 只能引用 user_input.* 变量。
- 写文件默认不覆盖，需要覆盖时显式传 overwrite=true。
- smoke_test_adapter 会执行适配包内的 functions.py，仅用于本地开发者适配包。
"""


def build_server(project_dir: str | Path, adapters_dir: str | Path | None = None) -> FastMCP:
    """构建 MCP 服务器实例。

    Args:
        project_dir: 仓库根目录；所有读写都限制在此目录内。
        adapters_dir: 可选适配器目录；默认 ``<project_dir>/framework/adapters``。

    Returns:
        已注册全部工具的 :class:`FastMCP` 实例。
    """
    scope = ProjectScope(project_dir, adapters_dir)
    mcp = FastMCP("calc-framework-builder", instructions=_INSTRUCTIONS)

    tools_discovery.register(mcp, scope)
    tools_files.register(mcp, scope)
    tools_build.register(mcp, scope)
    tools_verify.register(mcp, scope)
    tools_package.register(mcp, scope)

    return mcp
