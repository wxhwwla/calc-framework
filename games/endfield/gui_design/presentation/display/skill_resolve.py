#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""
属性/乘区/单段伤害的展示文案构建（无 GUI 依赖，便于单测）。
"""

from __future__ import annotations

from typing import Any

from calc_engine.endfield.calc.damage.types import format_damage_type_display, resolve_segment_damage_type

# 等级相关属性列表（需要根据等级从列表中提取对应值）
LEVEL_ATTRIBUTES = ["力量", "敏捷", "智识", "意志", "基础攻击力"]

# 角色技能类型与 JSON 字段、选择区滑块等级参数对应（见 skill_segments.CHARACTER_SKILL_TYPES）

NO_DAMAGE_MULTIPLIER_TEXT = "无伤害倍率"

# 武器 xxx+ 中不按百分数展示的词条（JSON 为去掉 % 的数值，展示为整数）
WEAPON_INTEGER_BONUS_ATTR_KEY = "源石技艺"
WEAPON_FLAT_BONUS_ATTRS: frozenset[str] = frozenset({"附加攻击力+", "主能力+", "副能力+"})

from .format import SelectedSkillForDamage


def resolve_selected_skill_for_damage(
    char_data: dict[str, Any],
    *,
    skill_1_level: int = 0,
    skill_2_level: int = 0,
    skill_3_level: int = 0,
) -> SelectedSkillForDamage:
    """根据技能滑块解析单段伤害预览所用的技能倍率与段伤害类型。"""
    picks = (
        ("战技", "战技倍率", skill_1_level),
        ("连携技", "连携技倍率", skill_2_level),
        ("终结技", "终结技倍率", skill_3_level),
    )
    for skill_name, field_name, level in picks:
        if level <= 0:
            continue
        segments = char_data.get(field_name)
        if not isinstance(segments, list) or not segments:
            continue
        first_segment = segments[0]
        if not isinstance(first_segment, list) or not first_segment:
            continue
        idx = level - 1
        if not (0 <= idx < len(first_segment)):
            continue
        value = first_segment[idx]
        if value is None:
            continue
        damage_type, explicit = resolve_segment_damage_type(char_data, field_name, 1)
        type_display = format_damage_type_display(damage_type, is_default=not explicit)
        warning = ""
        if not explicit:
            warning = "该段伤害类型未收录，按物理伤害计算。"
        return SelectedSkillForDamage(
            label=f"{skill_name} 等级{level} 第1段",
            multiplier=float(value) / 100.0,
            warning=warning,
            damage_type=damage_type,
            damage_type_display=type_display,
            skill_type=skill_name,
        )
    return SelectedSkillForDamage(
        label="默认普攻段",
        multiplier=1.0,
        warning="未选择技能等级或无可用倍率，按 100% 计算。",
        damage_type="物理",
        damage_type_display=format_damage_type_display("物理", is_default=True),
        skill_type="战技",
    )


# 兼容旧私有名（历史模块名，勿再新增引用）
_resolve_selected_skill_for_damage = resolve_selected_skill_for_damage
