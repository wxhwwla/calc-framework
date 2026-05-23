#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
兼容门面（deprecated）：请改用 display_lines / display_view / preview_lines。

新代码勿再 import 本模块。
"""

from gui_design.display_lines import (
    CHARACTER_SKILL_TYPES,
    LEVEL_ATTRIBUTES,
    NO_DAMAGE_MULTIPLIER_TEXT,
    WEAPON_INTEGER_BONUS_ATTR_KEY,
    _resolve_selected_skill_for_damage,
    build_character_attribute_lines,
    build_character_skill_lines,
    build_single_hit_damage_lines,
    build_weapon_attribute_lines,
    evaluate_display_state,
    format_fifteen_zone_damage_lines,
    format_skill_multiplier_display_value,
    format_weapon_bonus_display_value,
    resolve_selected_skill_for_damage,
)
from gui_design.display_request import DisplayRequest, build_display_request
from gui_design.display_view import (
    confirm_from_display_request,
    confirm_selection,
)
from gui_design.preview_lines import (
    build_multi_skill_search_preview_lines,
    build_single_skill_search_preview_lines,
)

__all__ = (
    "CHARACTER_SKILL_TYPES",
    "DisplayRequest",
    "LEVEL_ATTRIBUTES",
    "NO_DAMAGE_MULTIPLIER_TEXT",
    "WEAPON_INTEGER_BONUS_ATTR_KEY",
    "_resolve_selected_skill_for_damage",
    "build_character_attribute_lines",
    "build_character_skill_lines",
    "build_display_request",
    "build_multi_skill_search_preview_lines",
    "build_single_hit_damage_lines",
    "build_single_skill_search_preview_lines",
    "build_weapon_attribute_lines",
    "confirm_from_display_request",
    "confirm_selection",
    "evaluate_display_state",
    "format_fifteen_zone_damage_lines",
    "format_skill_multiplier_display_value",
    "format_weapon_bonus_display_value",
    "resolve_selected_skill_for_damage",
)
