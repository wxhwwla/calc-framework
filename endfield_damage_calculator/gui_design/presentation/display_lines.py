#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""属性/乘区/单段伤害展示文案（门面）。"""

from .display import *  # noqa: F403
from .display.format import NO_DAMAGE_MULTIPLIER_TEXT, SelectedSkillForDamage
from .display.character import (
    build_character_attribute_lines,
    build_character_skill_damage_type_lines,
    build_character_skill_lines,
    build_weapon_attribute_lines,
)
from .display.single_hit import build_single_hit_damage_lines, format_fifteen_zone_damage_lines
from .display.skill_resolve import resolve_selected_skill_for_damage
from .display.format import (
    evaluate_display_state,
    format_skill_multiplier_display_value,
    format_weapon_bonus_display_value,
    weapon_bonus_display_uses_percent,
)
