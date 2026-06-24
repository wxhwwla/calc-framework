#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""

属性/乘区/单段伤害的展示文案构建（无 GUI 依赖，便于单测）。

"""

from __future__ import annotations

from typing import Any

from games.endfield.calc.core.preview_cache import cached_preview, sync_confirm_dependencies
from games.endfield.calc.dag_adapter.search_evaluate import DamageEvalResult, evaluate_search_damage
from games.endfield.calc.damage.engine import ZONE_ORDER
from games.endfield.calc.multiplicative_zones.final_attack_zone import calculate_final_attack_with_details

# 等级相关属性列表（需要根据等级从列表中提取对应值）

LEVEL_ATTRIBUTES = ["力量", "敏捷", "智识", "意志", "基础攻击力"]


# 角色技能类型与 JSON 字段、选择区滑块等级参数对应（见 skill_segments.CHARACTER_SKILL_TYPES）


NO_DAMAGE_MULTIPLIER_TEXT = "无伤害倍率"


# 武器 xxx+ 中不按百分数展示的词条（JSON 为去掉 % 的数值，展示为整数）

WEAPON_INTEGER_BONUS_ATTR_KEY = "源石技艺"

WEAPON_FLAT_BONUS_ATTRS: frozenset[str] = frozenset({"附加攻击力+", "主能力+", "副能力+"})


from .format import format_skill_multiplier_display_value
from .skill_resolve import resolve_selected_skill_for_damage


def format_fifteen_zone_damage_lines(
    result: DamageEvalResult,
    *,
    header_lines: list[str] | None = None,
    show_running_product: bool = True,
) -> list[str]:
    """将伤害引擎结果格式化为 15 乘区分步展示文案。"""

    lines: list[str] = list(header_lines or [])

    running = 1.0

    for zone_name in ZONE_ORDER:
        zone_value = float(result.zone_values[zone_name])

        if show_running_product:
            running *= zone_value

            lines.append(f"{zone_name}: {zone_value:.4f}  (累计: {running:.4f})")

        else:
            lines.append(f"{zone_name}: {zone_value:.4f}")

    lines.append(f"最终伤害: {result.final_damage:.1f}")

    if result.warnings:
        for warning in result.warnings:
            lines.append(f"提示: {warning}")

    if result.unknown_effects:
        lines.append(f"未识别效果数: {len(result.unknown_effects)}")

    return lines


def build_single_hit_damage_lines(
    *,
    char_data: dict[str, Any] | None,
    weapon_data: dict[str, Any] | None,
    char_level: int,
    weapon_level: int,
    trust_level: int = 0,
    skill_1_level: int = 0,
    skill_2_level: int = 0,
    skill_3_level: int = 0,
    normal_skill_1_name: str = "",
    normal_skill_1_level: int = 1,
    normal_skill_2_name: str = "",
    normal_skill_2_level: int = 1,
    normal_skill_3_name: str = "",
    normal_skill_3_level: int = 0,
    special_skill_1_name: str = "",
    special_skill_1_level: int = 1,
    special_skill_1_stack: int = 1,
    special_skill_2_name: str = "",
    special_skill_2_level: int = 1,
    special_skill_2_stack: int = 1,
    sa1_name: str = "",
    sa1_level: int = 1,
    sa2_name: str = "",
    sa2_level: int = 1,
    sa3_name: str = "",
    sa3_level: int = 0,
    ws_name: str = "",
    ws_level: int = 1,
    ws_stack: int = 1,
    ws2_name: str = "",
    ws2_level: int = 1,
    ws2_stack: int = 1,
    enemy_defense: float = 100.0,
) -> list[str]:
    """构建单段伤害计算模式的展示行（带结果缓存）。"""

    if not char_data or not weapon_data:
        return ["请选择有效角色和武器"]

    sync_confirm_dependencies(
        char_data=char_data,
        weapon_data=weapon_data,
        char_level=char_level,
        weapon_level=weapon_level,
        trust_level=trust_level,
        skill_levels=(skill_1_level, skill_2_level, skill_3_level),
        calculation_mode="single_hit",
        enemy_defense=enemy_defense,
    )

    def _compute() -> list[str]:
        return _build_single_hit_damage_lines_impl(
            char_data=char_data,
            weapon_data=weapon_data,
            char_level=char_level,
            weapon_level=weapon_level,
            trust_level=trust_level,
            skill_1_level=skill_1_level,
            skill_2_level=skill_2_level,
            skill_3_level=skill_3_level,
            normal_skill_1_name=normal_skill_1_name,
            normal_skill_1_level=normal_skill_1_level,
            normal_skill_2_name=normal_skill_2_name,
            normal_skill_2_level=normal_skill_2_level,
            normal_skill_3_name=normal_skill_3_name,
            normal_skill_3_level=normal_skill_3_level,
            special_skill_1_name=special_skill_1_name,
            special_skill_1_level=special_skill_1_level,
            special_skill_1_stack=special_skill_1_stack,
            special_skill_2_name=special_skill_2_name,
            special_skill_2_level=special_skill_2_level,
            special_skill_2_stack=special_skill_2_stack,
            sa1_name=sa1_name,
            sa1_level=sa1_level,
            sa2_name=sa2_name,
            sa2_level=sa2_level,
            sa3_name=sa3_name,
            sa3_level=sa3_level,
            ws_name=ws_name,
            ws_level=ws_level,
            ws_stack=ws_stack,
            ws2_name=ws2_name,
            ws2_level=ws2_level,
            ws2_stack=ws2_stack,
            enemy_defense=enemy_defense,
        )
        """compute。"""

    lines, _hit = cached_preview("single_hit_lines", _compute)

    return lines


def _build_single_hit_damage_lines_impl(
    *,
    char_data: dict[str, Any],
    weapon_data: dict[str, Any],
    char_level: int,
    weapon_level: int,
    trust_level: int = 0,
    skill_1_level: int = 0,
    skill_2_level: int = 0,
    skill_3_level: int = 0,
    normal_skill_1_name: str = "",
    normal_skill_1_level: int = 1,
    normal_skill_2_name: str = "",
    normal_skill_2_level: int = 1,
    normal_skill_3_name: str = "",
    normal_skill_3_level: int = 0,
    special_skill_1_name: str = "",
    special_skill_1_level: int = 1,
    special_skill_1_stack: int = 1,
    special_skill_2_name: str = "",
    special_skill_2_level: int = 1,
    special_skill_2_stack: int = 1,
    sa1_name: str = "",
    sa1_level: int = 1,
    sa2_name: str = "",
    sa2_level: int = 1,
    sa3_name: str = "",
    sa3_level: int = 0,
    ws_name: str = "",
    ws_level: int = 1,
    ws_stack: int = 1,
    ws2_name: str = "",
    ws2_level: int = 1,
    ws2_stack: int = 1,
    enemy_defense: float = 100.0,
) -> list[str]:
    has_normal_1 = bool(normal_skill_1_name)

    has_normal_2 = bool(normal_skill_2_name)

    has_normal_3 = bool(normal_skill_3_name)

    has_special_1 = bool(special_skill_1_name)

    has_special_2 = bool(special_skill_2_name)

    normal_skill_1_name = normal_skill_1_name or sa1_name

    normal_skill_1_level = normal_skill_1_level if has_normal_1 else sa1_level

    normal_skill_2_name = normal_skill_2_name or sa2_name

    normal_skill_2_level = normal_skill_2_level if has_normal_2 else sa2_level

    normal_skill_3_name = normal_skill_3_name or sa3_name

    normal_skill_3_level = normal_skill_3_level if has_normal_3 else sa3_level

    special_skill_1_name = special_skill_1_name or ws_name

    special_skill_1_level = special_skill_1_level if has_special_1 else ws_level

    special_skill_1_stack = special_skill_1_stack if has_special_1 else ws_stack

    special_skill_2_name = special_skill_2_name or ws2_name

    special_skill_2_level = special_skill_2_level if has_special_2 else ws2_level

    special_skill_2_stack = special_skill_2_stack if has_special_2 else ws2_stack

    skill = resolve_selected_skill_for_damage(
        char_data,
        skill_1_level=skill_1_level,
        skill_2_level=skill_2_level,
        skill_3_level=skill_3_level,
    )

    final = calculate_final_attack_with_details(
        character=char_data,
        weapon=weapon_data,
        char_level=char_level,
        weapon_level=weapon_level,
        normal_skill_1_name=normal_skill_1_name,
        normal_skill_1_level=normal_skill_1_level,
        normal_skill_2_name=normal_skill_2_name,
        normal_skill_2_level=normal_skill_2_level,
        normal_skill_3_name=normal_skill_3_name,
        normal_skill_3_level=normal_skill_3_level,
        special_skill_1_name=special_skill_1_name,
        special_skill_1_level=special_skill_1_level,
        special_skill_1_stack=special_skill_1_stack,
        special_skill_2_name=special_skill_2_name,
        special_skill_2_level=special_skill_2_level,
        special_skill_2_stack=special_skill_2_stack,
        trust_level=trust_level,
    )

    result = evaluate_search_damage(
        final_attack=float(final["final_attack"]),
        skill_multiplier=skill.multiplier,
        damage_type=skill.damage_type,
        skill_type=skill.skill_type,
        enemy_defense=enemy_defense,
        crit_mode="non_crit",
    )

    header = [
        "计算模式: 单段伤害计算",
        f"技能: {skill.label}",
        f"伤害类型: {skill.damage_type_display}",
        f"技能倍率: {format_skill_multiplier_display_value(skill.multiplier * 100)}",
        f"最终攻击力(基础伤害区): {final['final_attack']:.1f}",
        "暴击模式: 不暴击",
    ]

    if skill.warning:
        header.append(f"提示: {skill.warning}")

    return format_fifteen_zone_damage_lines(
        result,
        header_lines=header,
        show_running_product=True,
    )
    """build single hit damage lines impl。"""
