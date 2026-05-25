#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
属性三列 CTk 渲染与确认刷新编排（依赖 display_lines 文案）。
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from utils.platform_win32_patch import apply_platform_win32_patch

apply_platform_win32_patch()
import customtkinter as ctk

from calculation.loadout.optimizer import WeaponCandidate
from calculation.multiplicative_zones.zone_snapshot import (
    MultiplicativeZoneSelection,
    WeaponBonusSelection,
    compute_multiplicative_zone_snapshot,
)
from calculation.core.preview_cache import sync_confirm_dependencies
from gui_design.presentation.display_lines import (
    build_character_attribute_lines,
    build_single_hit_damage_lines,
    build_weapon_attribute_lines,
    evaluate_display_state,
)
from gui_design.app.loadout_evaluation import build_search_preview_lines
from calculation.loadout.slot_search import FixedLoadoutSelection
from gui_design.app.display_request import DisplayRequest
from gui_design.app.loadout_state import LoadoutState, read_loadout_from_panels
from gui_design.panels.selection_panel import ChooseTypesStarsNamesLevels

from .zone_panel import _display_zone_data



def refresh_right_column_from_request(
    right_scroll: ctk.CTkScrollableFrame | None,
    request: DisplayRequest,
    *,
    big_font: ctk.CTkFont,
    small_font: ctk.CTkFont,
) -> None:
    """仅重绘右侧乘区/预览列（避免切换手动次数时整页刷新）。"""
    if right_scroll is None:
        return

    for widget in right_scroll.winfo_children():
        widget.destroy()

    loadout = request.loadout
    char_data = loadout.char_data
    weapon_data = loadout.weapon_data
    ui_state = evaluate_display_state(char_data, weapon_data)
    s1, s2, s3 = loadout.skill_levels

    sync_confirm_dependencies(
        char_data=char_data,
        weapon_data=weapon_data,
        char_level=loadout.char_level,
        weapon_level=loadout.weapon_level,
        trust_level=loadout.trust_level,
        skill_levels=loadout.skill_levels,
        calculation_mode=loadout.calculation_mode,
        weapon_scope=loadout.weapon_scope_label,
        equipment_scope=loadout.equipment_scope_label,
        multi_skill_counts=loadout.manual_counts,
        use_manual_multi_skill_counts=loadout.use_manual_multi_skill_counts,
        physical_abnormal_counts=loadout.physical_abnormal_counts,
        spell_abnormal_counts=loadout.spell_abnormal_counts,
        damage_component_mode=loadout.damage_component_mode,
        use_expected_crit=loadout.use_expected_crit,
        include_conditional_equipment_crit=loadout.include_conditional_equipment_crit,
        extra_crit_rate=loadout.extra_crit_rate,
        extra_crit_damage=loadout.extra_crit_damage,
        enemy_defense=loadout.enemy_defense,
    )

    if not ui_state["can_update_zone"]:
        return

    skill_specials = loadout.weapon_skill_kwargs()
    _display_zone_data(
        right_scroll,
        char_data,
        weapon_data,
        loadout.char_level,
        loadout.weapon_level,
        skill_specials["normal_skill_1_name"],
        skill_specials["normal_skill_1_level"],
        skill_specials["normal_skill_2_name"],
        skill_specials["normal_skill_2_level"],
        skill_specials["normal_skill_3_name"],
        skill_specials["normal_skill_3_level"],
        skill_specials["special_skill_1_name"],
        skill_specials["special_skill_1_level"],
        skill_specials["special_skill_1_stack"],
        skill_specials["special_skill_2_name"],
        skill_specials["special_skill_2_level"],
        skill_specials["special_skill_2_stack"],
        loadout.trust_level,
        big_font,
        small_font,
        loadout=loadout,
        calculation_mode=loadout.calculation_mode,
        skill_1_level=s1,
        skill_2_level=s2,
        skill_3_level=s3,
        enemy_defense=loadout.enemy_defense,
        preview_weapon_candidates=list(request.preview_weapon_candidates),
        preview_equipment_catalog=request.equipment_catalog,
    )


