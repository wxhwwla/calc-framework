# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""布局与属性描述构建 — 按有效 source 分组生成 layout / attr_schema。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tools.generator.engine import OutputDef, VarDef

# 需要实体数据文件（或用户输入）提供取值的来源
ENTITY_SOURCES: frozenset[str] = frozenset({"character", "weapon", "equipment", "enemy"})

SECTION_ORDER: tuple[str, ...] = ("user_input", "character", "weapon", "equipment", "enemy")

SECTION_TITLES: dict[str, str] = {
    "user_input": "输入参数",
    "character": "角色参数",
    "weapon": "武器参数",
    "equipment": "装备参数",
    "enemy": "目标参数",
}

SECTION_IDS: dict[str, str] = {
    "user_input": "inputs",
    "character": "inputs_character",
    "weapon": "inputs_weapon",
    "equipment": "inputs_equipment",
    "enemy": "inputs_enemy",
}


def _layout_group(original_source: str) -> str:
    """把原始 source 映射到输入分组；非实体来源统一归入 user_input。"""
    return original_source if original_source in ENTITY_SOURCES else "user_input"


def build_layout(
    game_name: str,
    variables: list[VarDef],
    effective_sources: dict[str, str],
    outputs: list[OutputDef],
) -> dict[str, Any]:
    """构建 UI layout，输入区按原始 source 分组，路径统一为 ``user_input.*``。

    Args:
        game_name: 游戏/计算器名称。
        variables: 变量声明列表（保留原始 source 用于分组）。
        effective_sources: 变量名 → 生成后实际 source。
        outputs: 输出声明列表。

    Returns:
        layout.json 对应的字典。
    """
    grouped: dict[str, list[str]] = {source: [] for source in SECTION_ORDER}
    for v in variables:
        if effective_sources[v.name] != "user_input":
            continue
        grouped[_layout_group(v.source)].append(f"user_input.{v.name}")

    sections: list[dict[str, Any]] = []
    for source in SECTION_ORDER:
        if grouped[source]:
            sections.append(
                {
                    "id": SECTION_IDS[source],
                    "type": "inputs",
                    "title": SECTION_TITLES[source],
                    "variables": grouped[source],
                }
            )

    primary_outs = [o.name for o in outputs if o.is_primary]
    if primary_outs:
        sections.append(
            {
                "id": "outputs",
                "type": "outputs",
                "title": "计算结果",
                "outputs": primary_outs,
            }
        )
    other_outs = [o.name for o in outputs if o.name not in primary_outs]
    if other_outs:
        sections.append(
            {
                "id": "detail",
                "type": "outputs",
                "title": "中间过程",
                "outputs": other_outs,
            }
        )

    return {
        "schema_version": "ui-v1",
        "name": f"{game_name}计算表",
        "description": f"{game_name}的 ComputeSheet 排版（自动生成）",
        "sections": sections,
    }


def build_attr_schema(variables: list[VarDef], effective_sources: dict[str, str]) -> dict[str, Any]:
    """构建 attr_schema，``source`` 写入变量生成后的实际来源。"""
    attrs = []
    for v in variables:
        entry: dict[str, Any] = {
            "name": v.name,
            "type": "percent" if v.type in ("percent", "bool") else "float",
            "source": effective_sources[v.name],
            "description": v.description,
        }
        if v.default != 0:
            entry["default"] = v.default
        attrs.append(entry)
    return {"attributes": attrs}
