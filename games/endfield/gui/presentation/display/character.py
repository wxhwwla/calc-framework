#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""

属性/乘区/单段伤害的展示文案构建（无 GUI 依赖，便于单测）。

"""

from __future__ import annotations

from typing import Any

from games.endfield.calc.damage.types import format_damage_type_display, resolve_segment_damage_type
from games.endfield.calc.skills.segments import CHARACTER_SKILL_TYPES
from games.endfield.calc.skills.special_fields import (
    read_weapon_skills_schema,
    special_pick_bonus,
)

# 等级相关属性列表（需要根据等级从列表中提取对应值）

LEVEL_ATTRIBUTES = ["力量", "敏捷", "智识", "意志", "基础攻击力"]


# 角色技能类型与 JSON 字段、选择区滑块等级参数对应（见 skill_segments.CHARACTER_SKILL_TYPES）


# 武器 xxx+ 中不按百分数展示的词条（JSON 为去掉 % 的数值，展示为整数）

WEAPON_INTEGER_BONUS_ATTR_KEY = "源石技艺"

WEAPON_FLAT_BONUS_ATTRS: frozenset[str] = frozenset({"附加攻击力+", "主能力+", "副能力+"})


from .format import (
    NO_DAMAGE_MULTIPLIER_TEXT,
    _get_attribute_value,
    _skill_segment_display_value,
    format_weapon_bonus_display_value,
)


def build_character_skill_damage_type_lines(
    char_data: dict[str, Any],
    *,
    skill_1_level: int = 0,
    skill_2_level: int = 0,
    skill_3_level: int = 0,
) -> list[str]:
    """构建角色各段伤害类型只读列表（与倍率段序对齐）。"""

    skill_levels = (skill_1_level, skill_2_level, skill_3_level)

    lines: list[str] = []

    for (skill_type, field_name, _), skill_level in zip(CHARACTER_SKILL_TYPES, skill_levels):
        if skill_level <= 0:
            continue

        segments = char_data.get(field_name)

        if not isinstance(segments, list) or not segments:
            continue

        for segment_index in range(1, len(segments) + 1):
            damage_type, explicit = resolve_segment_damage_type(char_data, field_name, segment_index)

            type_display = format_damage_type_display(damage_type, is_default=not explicit)

            lines.append(f"{skill_type} 第{segment_index}段: {type_display}")

    return lines


def build_character_skill_lines(
    char_data: dict[str, Any],
    *,
    skill_1_level: int = 0,
    skill_2_level: int = 0,
    skill_3_level: int = 0,
) -> list[str]:
    """构建角色技能倍率明细行（战技 → 连携技 → 终结技）。"""

    skill_levels = (skill_1_level, skill_2_level, skill_3_level)

    lines: list[str] = []

    for (skill_type, field_name, _), skill_level in zip(CHARACTER_SKILL_TYPES, skill_levels):
        if skill_level <= 0:
            continue

        segments = char_data.get(field_name)

        if not isinstance(segments, list) or not segments:
            continue

        for segment_index, segment in enumerate(segments, start=1):
            display_value = _skill_segment_display_value(segment, skill_level)

            if display_value is None:
                value_text = NO_DAMAGE_MULTIPLIER_TEXT

            else:
                value_text = display_value

            damage_type, explicit = resolve_segment_damage_type(char_data, field_name, segment_index)

            type_display = format_damage_type_display(damage_type, is_default=not explicit)

            lines.append(f"{skill_type} 等级{skill_level} 第{segment_index}段: {value_text} · {type_display}")

    return lines


def build_character_attribute_lines(
    char_data: dict[str, Any] | None,
    level: int,
    *,
    skill_1_level: int = 0,
    skill_2_level: int = 0,
    skill_3_level: int = 0,
) -> list[str]:
    """构建角色属性列展示明细（不含摘要）。"""

    if not char_data:
        return []

    lines: list[str] = []

    for attr_name in LEVEL_ATTRIBUTES:
        value = _get_attribute_value(char_data, level, attr_name)

        if value:
            lines.append(f"{attr_name}: {value}")

    if skill_1_level or skill_2_level or skill_3_level:
        type_lines = build_character_skill_damage_type_lines(
            char_data,
            skill_1_level=skill_1_level,
            skill_2_level=skill_2_level,
            skill_3_level=skill_3_level,
        )

        if type_lines:
            lines.append("--- 技能段伤害类型 ---")

            lines.extend(type_lines)

        lines.extend(
            build_character_skill_lines(
                char_data,
                skill_1_level=skill_1_level,
                skill_2_level=skill_2_level,
                skill_3_level=skill_3_level,
            )
        )

    return lines


def build_weapon_attribute_lines(
    weapon_data: dict[str, Any] | None,
    weapon_level: int,
    *,
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
) -> list[str]:
    """构建武器属性列展示明细（不含摘要）。"""

    if not weapon_data:
        return []

    # 新命名优先；旧命名保持兼容

    sa1_name = normal_skill_1_name or sa1_name

    sa1_level = normal_skill_1_level if normal_skill_1_name else sa1_level

    sa2_name = normal_skill_2_name or sa2_name

    sa2_level = normal_skill_2_level if normal_skill_2_name else sa2_level

    sa3_name = normal_skill_3_name or sa3_name

    sa3_level = normal_skill_3_level if normal_skill_3_name else sa3_level

    ws_name = special_skill_1_name or ws_name

    ws_level = special_skill_1_level if special_skill_1_name else ws_level

    ws_stack = special_skill_1_stack if special_skill_1_name else ws_stack

    ws2_name = special_skill_2_name or ws2_name

    ws2_level = special_skill_2_level if special_skill_2_name else ws2_level

    ws2_stack = special_skill_2_stack if special_skill_2_name else ws2_stack

    lines: list[str] = []

    base_attack = _get_attribute_value(weapon_data, weapon_level, "基础攻击力")

    if base_attack:
        lines.append(f"基础攻击力: {base_attack}")

    schema = read_weapon_skills_schema(weapon_data)

    normal_skills = schema.get("normal_skills", [])

    special_skills = schema.get("special_skills", [])

    bonus_attrs = [str(item.get("effect", "")) for item in normal_skills]

    for item in normal_skills:
        attr_name = str(item.get("effect", ""))

        curve = item.get("curve")

        values = curve if isinstance(curve, list) else []

        if not attr_name or not values:
            continue

        if attr_name == sa1_name:
            level_index = sa1_level - 1

        elif attr_name == sa2_name:
            level_index = sa2_level - 1

        elif attr_name == sa3_name:
            level_index = sa3_level - 1

        else:
            level_index = 0

        raw_value = values[level_index] if 0 <= level_index < len(values) else values[0]

        display_value = format_weapon_bonus_display_value(
            raw_value,
            attr_name=attr_name,
            is_first_skill=(attr_name == sa1_name),
        )

        lines.append(f"{attr_name}: {display_value}")

    for slot_idx, pick_level, pick_stack, pick_name, label in (
        (0, ws_level, ws_stack, ws_name, "特殊一"),
        (1, ws2_level, ws2_stack, ws2_name, "特殊二"),
    ):
        if not pick_name or pick_name in bonus_attrs:
            continue

        raw_value = None

        if slot_idx < len(special_skills):
            special = special_skills[slot_idx]

            curve = special.get("curve")

            if isinstance(curve, list) and curve:
                special_name = str(special.get("name", ""))

                special_effect = str(special.get("effect", ""))

                if pick_name in (special_name, special_effect):
                    raw_value = special_pick_bonus(
                        [float(v) for v in curve],
                        int(special.get("max_stack", 1)),
                        skill_level=pick_level,
                        stack_count=pick_stack,
                    )

        display_value = "0%"

        if raw_value is not None:
            display_value = format_weapon_bonus_display_value(
                raw_value,
                attr_name=pick_name,
                is_first_skill=False,
            )

        lines.append(f"{pick_name}({label}): {display_value}")

    return lines
