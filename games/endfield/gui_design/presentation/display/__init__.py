#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""属性/乘区/单段伤害展示文案。"""

from .character import (
    build_character_attribute_lines,
    build_character_skill_damage_type_lines,
    build_character_skill_lines,
    build_weapon_attribute_lines,
)
from .format import (
    NO_DAMAGE_MULTIPLIER_TEXT,
    SelectedSkillForDamage,
    evaluate_display_state,
    format_skill_multiplier_display_value,
    format_weapon_bonus_display_value,
    weapon_bonus_display_uses_percent,
)
from .single_hit import build_single_hit_damage_lines, format_fifteen_zone_damage_lines
from .skill_resolve import resolve_selected_skill_for_damage

__all__ = [
    "NO_DAMAGE_MULTIPLIER_TEXT",
    "SelectedSkillForDamage",
    "build_character_attribute_lines",
    "build_character_skill_damage_type_lines",
    "build_character_skill_lines",
    "build_single_hit_damage_lines",
    "build_weapon_attribute_lines",
    "evaluate_display_state",
    "format_fifteen_zone_damage_lines",
    "format_skill_multiplier_display_value",
    "format_weapon_bonus_display_value",
    "resolve_selected_skill_for_damage",
    "weapon_bonus_display_uses_percent",
]
