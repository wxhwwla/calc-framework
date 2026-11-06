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

        本工具不接收 ``data_files``：若 DAG 含 character/weapon/equipment/enemy
        源变量，请用 ``write_adapter_file`` 写入 ``data/{characters,weapons,equipments,enemies}.json``
        （记录须含非空 ``名称``），查看器才会提供对应实体下拉；否则这些变量不可编辑。
        自动生成的 layout 仍会列出它们，``validate_adapter`` 会给出提示。
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
        data_files: dict[str, list[dict[str, Any]]] | None = None,
        entity_selectors: list[dict[str, Any]] | None = None,
        entity_detail: dict[str, Any] | None = None,
        entity_input_rules: list[dict[str, Any]] | None = None,
        layout_sections: list[dict[str, Any]] | None = None,
        dry_run: bool = False,
        overwrite: bool = False,
    ) -> dict[str, Any]:
        """Create an adapter package from declarative variables, formula steps and outputs.

        公式步骤只支持 ``+ - * /``、``condition``、``expr``。步骤引用变量 ``name``、
        步骤 ``id`` 或数字字面量（不要写 ``user_input.atk``）。``expr`` 支持
        比较（``< <= > >= == !=``）、布尔（``and/or/not``）与三元（``a if cond else b``）。

        变量可带 ``min``/``max``（仅 float/int）与 ``ui_control``：
        ``suffix``（如 ``"%"``）、``step``（正数）、``widget``
        （spinbox/slider/switch/dropdown）、``options``（字符串数组，自动用 dropdown）。

        ``data_files`` 可提供 character/weapon/equipment/enemy 四类实体记录，
        写入约定路径 ``data/{characters,weapons,equipments,enemies}.json``；
        每条记录必须含非空字符串 ``名称``，且变量 ``name`` 应与记录字段名一致。
        提供非空记录列表的来源视为已绑定：其变量保留 source 命名空间、由查看器
        实体下拉提供，不出现在输入区；未绑定或列表为空的来源，其变量自动改写为
        ``user_input.*``（空列表会在 warnings 中提示）。

        ``entity_selectors`` 把普通实体下拉改为多级级联，每项形如
        ``{"source": "weapon", "data_file": "weapons", "steps": [{"field": "舰船分类",
        "label": "舰船种类"}, {"field": "名称", "label": "武器", "display_field": "武器标签"}]}``；
        来源必须已绑定非空 data_files，步骤字段必须存在，末级 field 必须为 ``名称``。

        ``entity_detail`` 在查看器最左侧显示选中实体的字段明细，形如
        ``{"source": "weapon", "title": "武器数据", "sections": [{"title": "基础",
        "columns": 2, "fields": [{"field": "舰船", "label": "舰船"}]}]}``；
        source 必须已绑定数据，field 必须在该来源记录中存在。

        ``entity_input_rules`` 按实体字段值禁用无关输入，形如
        ``{"source": "weapon", "field": "needs_mothership", "equals": 0,
        "disable": ["user_input.mothership_flight_bonus"], "reason": "该舰船不需要母舰"}``；
        disable 只能引用生成后仍为 user_input 的变量路径。字段缺失的实体不会命中规则，
        对应输入保持可编辑。

        ``layout_sections`` 覆盖自动 layout，支持分页与列数，形如
        ``[{"type": "inputs", "title": "输入参数", "source": "user_input", "tab": "计算"},
        {"type": "outputs", "title": "计算结果", "outputs": ["最终伤害"],
        "columns": 3, "tab": "计算"},
        {"type": "outputs", "title": "乘区明细",
        "outputs": ["基础乘区", "暴击乘区"], "columns": 3, "tab": "乘区明细"}]``。
        inputs 段用 ``variables``（变量名，可带 ``user_input.`` 前缀）或 ``source``
        （按原始来源自动收集未绑定实体变量）二选一；outputs 段必须列出 ``outputs``。
        ``columns`` 为 1–3；``tab`` 必须所有段都写或都不写。绑定实体变量与
        computed 变量不能出现在 inputs 段。省略本参数时使用自动 layout：存在
        非主输出时自动分「计算」/「乘区明细」两页，否则保持单页。

        ``dry_run=true`` 只预览文件内容，不写盘。
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
            data_files=data_files,
            entity_selectors=entity_selectors,
            entity_detail=entity_detail,
            entity_input_rules=entity_input_rules,
            layout_sections=layout_sections,
            dry_run=dry_run,
            overwrite=overwrite,
        )

    _ = (scaffold_adapter, generate_adapter)
