#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
属性三列 CTk 渲染与确认刷新编排（依赖 display_lines 文案）。
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import customtkinter as ctk

from calculation.loadout_optimizer import WeaponCandidate
from calculation.multiplicative_zones.zone_snapshot import (
    MultiplicativeZoneSelection,
    WeaponBonusSelection,
    compute_multiplicative_zone_snapshot,
)
from calculation.preview_cache import sync_confirm_dependencies
from gui_design.display_lines import (
    build_character_attribute_lines,
    build_single_hit_damage_lines,
    build_weapon_attribute_lines,
)
from gui_design.preview_lines import (
    build_multi_skill_search_preview_lines,
    build_single_skill_search_preview_lines,
)
from gui_design.selection_panel import ChooseTypesStarsNamesLevels


def _render_lines(
    target_scroll: ctk.CTkScrollableFrame,
    lines: list[str],
    *,
    font: ctk.CTkFont,
    text_color: str,
) -> None:
    """按顺序渲染文本行。"""
    for row, text in enumerate(lines):
        label = ctk.CTkLabel(
            target_scroll,
            text=text,
            font=font,
            text_color=text_color,
        )
        label.grid(row=row, column=0, sticky="w", pady=2)


def _render_placeholder(
    target_scroll: ctk.CTkScrollableFrame,
    message: str,
    *,
    font: ctk.CTkFont,
) -> None:
    """渲染空状态或错误提示。"""
    label = ctk.CTkLabel(
        target_scroll,
        text=message,
        font=font,
        text_color="#888888",
    )
    label.grid(row=0, column=0, sticky="w", pady=(6, 2))


def evaluate_display_state(
    char_data: Optional[Dict[str, Any]],
    weapon_data: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """评估本次确认后各列提示及右侧乘区是否可更新。"""
    state = {
        "char_message": "",
        "weapon_message": "",
        "can_update_zone": bool(char_data and weapon_data),
    }
    if not char_data:
        state["char_message"] = "请选择有效角色"
    if not weapon_data:
        state["weapon_message"] = "请选择有效武器"
    return state


def confirm_selection(
    char_attr_scroll: ctk.CTkScrollableFrame | None,
    weapon_attr_scroll: ctk.CTkScrollableFrame | None,
    right_scroll: ctk.CTkScrollableFrame | None,
    char_panel: ChooseTypesStarsNamesLevels,
    weapon_panel: ChooseTypesStarsNamesLevels,
    big_font: ctk.CTkFont,
    small_font: ctk.CTkFont,
    calculation_mode: str = "zone_snapshot",
    multi_skill_manual_counts: Optional[Dict[str, int]] = None,
    use_manual_multi_skill_counts: bool = False,
    preview_weapon_candidates: Optional[list[WeaponCandidate]] = None,
    preview_scope_label: str = "",
    preview_equipment_catalog: Optional[Dict[str, list[dict]]] = None,
    preview_equipment_scope_label: str = "",
    enemy_defense: float = 100.0,
) -> None:
    """
    确认选择并刷新角色属性列、武器属性列，以及右侧乘区数据。
    """
    if char_attr_scroll is None or weapon_attr_scroll is None or right_scroll is None:
        return

    for widget in char_attr_scroll.winfo_children():
        widget.destroy()
    for widget in weapon_attr_scroll.winfo_children():
        widget.destroy()
    for widget in right_scroll.winfo_children():
        widget.destroy()

    char_data = char_panel.get_selected_data()
    weapon_data = weapon_panel.get_selected_data()
    state = evaluate_display_state(char_data, weapon_data)
    skill_1_level = char_panel.get_skill_1_level()
    skill_2_level = char_panel.get_skill_2_level()
    skill_3_level = char_panel.get_skill_3_level()
    if char_data and weapon_data:
        sync_confirm_dependencies(
            char_data=char_data,
            weapon_data=weapon_data,
            char_level=char_panel.get_level(),
            weapon_level=weapon_panel.get_level(),
            trust_level=char_panel.get_trust_level(),
            skill_levels=(skill_1_level, skill_2_level, skill_3_level),
            calculation_mode=calculation_mode,
            weapon_scope=preview_scope_label,
            equipment_scope=preview_equipment_scope_label,
            multi_skill_counts=multi_skill_manual_counts,
            use_manual_multi_skill_counts=use_manual_multi_skill_counts,
            enemy_defense=enemy_defense,
        )
    char_level = char_panel.get_level()
    weapon_level = weapon_panel.get_level()
    trust_level = char_panel.get_trust_level()
    if not state["char_message"] and char_data:
        char_lines = build_character_attribute_lines(
            char_data,
            char_level,
            skill_1_level=skill_1_level,
            skill_2_level=skill_2_level,
            skill_3_level=skill_3_level,
        )
        _render_lines(
            char_attr_scroll,
            char_lines,
            font=small_font,
            text_color="#B8B8B8",
        )
    else:
        _render_placeholder(char_attr_scroll, state["char_message"], font=small_font)

    special_ability_1_name = weapon_panel.get_special_ability_1_name()
    special_ability_1_level = weapon_panel.get_special_ability_1_level()
    special_ability_2_name = weapon_panel.get_special_ability_2_name()
    special_ability_2_level = weapon_panel.get_special_ability_2_level()
    special_ability_3_name = weapon_panel.get_special_ability_3_name()
    special_ability_3_level = weapon_panel.get_special_ability_3_level()
    weapon_special_name = weapon_panel.get_weapon_special_name()
    weapon_special_level = weapon_panel.get_weapon_special_level()
    weapon_special_2_name = weapon_panel.get_weapon_special_2_name()
    weapon_special_2_level = weapon_panel.get_weapon_special_2_level()

    if not state["weapon_message"] and weapon_data:
        weapon_lines = build_weapon_attribute_lines(
            weapon_data,
            weapon_level,
            sa1_name=special_ability_1_name,
            sa1_level=special_ability_1_level,
            sa2_name=special_ability_2_name,
            sa2_level=special_ability_2_level,
            sa3_name=special_ability_3_name,
            sa3_level=special_ability_3_level,
            ws_name=weapon_special_name,
            ws_level=weapon_special_level,
            ws2_name=weapon_special_2_name,
            ws2_level=weapon_special_2_level,
        )
        _render_lines(
            weapon_attr_scroll,
            weapon_lines,
            font=small_font,
            text_color="#4ECDC4",
        )
    else:
        _render_placeholder(weapon_attr_scroll, state["weapon_message"], font=small_font)

    if not state["can_update_zone"]:
        return

    _display_zone_data(
        right_scroll,
        char_data,
        weapon_data,
        char_level,
        weapon_level,
        special_ability_1_name,
        special_ability_1_level,
        special_ability_2_name,
        special_ability_2_level,
        special_ability_3_name,
        special_ability_3_level,
        weapon_special_name,
        weapon_special_level,
        weapon_special_2_name,
        weapon_special_2_level,
        trust_level,
        big_font,
        small_font,
        calculation_mode=calculation_mode,
        skill_1_level=skill_1_level,
        skill_2_level=skill_2_level,
        skill_3_level=skill_3_level,
        multi_skill_manual_counts=multi_skill_manual_counts,
        enemy_defense=enemy_defense,
        use_manual_multi_skill_counts=use_manual_multi_skill_counts,
        preview_weapon_candidates=preview_weapon_candidates,
        preview_scope_label=preview_scope_label,
        preview_equipment_catalog=preview_equipment_catalog,
        preview_equipment_scope_label=preview_equipment_scope_label,
    )


def _display_zone_data(
    right_scroll: ctk.CTkScrollableFrame,
    char_data: Optional[Dict[str, Any]],
    weapon_data: Optional[Dict[str, Any]],
    char_level: int,
    weapon_level: int,
    sa1_name: str = "",
    sa1_level: int = 1,
    sa2_name: str = "",
    sa2_level: int = 1,
    sa3_name: str = "",
    sa3_level: int = 0,
    ws_name: str = "",
    ws_level: int = 0,
    ws2_name: str = "",
    ws2_level: int = 0,
    trust_level: int = 0,
    big_font: Optional[ctk.CTkFont] = None,
    small_font: Optional[ctk.CTkFont] = None,
    calculation_mode: str = "zone_snapshot",
    skill_1_level: int = 0,
    skill_2_level: int = 0,
    skill_3_level: int = 0,
    multi_skill_manual_counts: Optional[Dict[str, int]] = None,
    use_manual_multi_skill_counts: bool = False,
    preview_weapon_candidates: Optional[list[WeaponCandidate]] = None,
    preview_scope_label: str = "",
    preview_equipment_catalog: Optional[Dict[str, list[dict]]] = None,
    preview_equipment_scope_label: str = "",
    enemy_defense: float = 100.0,
) -> None:
    """在右侧区域展示乘区或各计算模式预览文案。"""
    mode_title = "乘区数据" if calculation_mode == "zone_snapshot" else "单段伤害预览"
    zone_title = ctk.CTkLabel(
        right_scroll,
        text=f"=== {mode_title} ===",
        font=big_font,
        text_color="#FF6B6B",
    )
    zone_title.grid(row=0, column=0, sticky="w", pady=(5, 5))

    row_idx = 1
    if calculation_mode == "single_hit":
        for text in build_single_hit_damage_lines(
            char_data=char_data,
            weapon_data=weapon_data,
            char_level=char_level,
            weapon_level=weapon_level,
            trust_level=trust_level,
            skill_1_level=skill_1_level,
            skill_2_level=skill_2_level,
            skill_3_level=skill_3_level,
            sa1_name=sa1_name,
            sa1_level=sa1_level,
            sa2_name=sa2_name,
            sa2_level=sa2_level,
            sa3_name=sa3_name,
            sa3_level=sa3_level,
            ws_name=ws_name,
            ws_level=ws_level,
            ws2_name=ws2_name,
            ws2_level=ws2_level,
            enemy_defense=enemy_defense,
        ):
            label = ctk.CTkLabel(
                right_scroll,
                text=text,
                font=small_font,
                text_color="#B8B8B8",
            )
            label.grid(row=row_idx, column=0, sticky="w", pady=2)
            row_idx += 1
        return

    if calculation_mode == "single_skill_search":
        for text in build_single_skill_search_preview_lines(
            char_data=char_data,
            weapon_data=weapon_data,
            char_level=char_level,
            weapon_level=weapon_level,
            trust_level=trust_level,
            skill_1_level=skill_1_level,
            skill_2_level=skill_2_level,
            skill_3_level=skill_3_level,
            preview_weapon_candidates=preview_weapon_candidates,
            preview_scope_label=preview_scope_label,
            preview_equipment_catalog=preview_equipment_catalog,
            preview_equipment_scope_label=preview_equipment_scope_label,
            enemy_defense=enemy_defense,
        ):
            label = ctk.CTkLabel(
                right_scroll,
                text=text,
                font=small_font,
                text_color="#B8B8B8",
            )
            label.grid(row=row_idx, column=0, sticky="w", pady=2)
            row_idx += 1
        return

    if calculation_mode == "multi_skill_search":
        for text in build_multi_skill_search_preview_lines(
            char_data=char_data,
            weapon_data=weapon_data,
            char_level=char_level,
            weapon_level=weapon_level,
            trust_level=trust_level,
            skill_1_level=skill_1_level,
            skill_2_level=skill_2_level,
            skill_3_level=skill_3_level,
            manual_counts=multi_skill_manual_counts,
            use_manual_counts=use_manual_multi_skill_counts,
            preview_equipment_scope_label=preview_equipment_scope_label,
            enemy_defense=enemy_defense,
        ):
            label = ctk.CTkLabel(
                right_scroll,
                text=text,
                font=small_font,
                text_color="#B8B8B8",
            )
            label.grid(row=row_idx, column=0, sticky="w", pady=2)
            row_idx += 1
        return

    if calculation_mode != "zone_snapshot":
        tip = ctk.CTkLabel(
            right_scroll,
            text="该模式开发中，当前先支持“单段伤害计算”。",
            font=small_font,
            text_color="#888888",
        )
        tip.grid(row=row_idx, column=0, sticky="w", pady=(6, 2))
        return

    if char_data:
        selection = MultiplicativeZoneSelection(
            character=char_data,
            weapon=weapon_data,
            char_level=char_level,
            weapon_level=weapon_level,
            trust_level=trust_level,
            bonuses=WeaponBonusSelection(
                sa1_name=sa1_name,
                sa1_level=sa1_level,
                sa2_name=sa2_name,
                sa2_level=sa2_level,
                sa3_name=sa3_name,
                sa3_level=sa3_level,
                ws_name=ws_name,
                ws_level=ws_level,
                ws2_name=ws2_name,
                ws2_level=ws2_level,
            ),
        )
        for line in compute_multiplicative_zone_snapshot(selection):
            label = ctk.CTkLabel(
                right_scroll,
                text=line.text,
                font=small_font,
                text_color=line.color,
            )
            label.grid(row=row_idx, column=0, sticky="w", pady=2)
            row_idx += 1

    hint_label = ctk.CTkLabel(
        right_scroll,
        text="\n* 能力乘区已包含角色基础属性和武器加成",
        font=small_font,
        text_color="#666666",
    )
    hint_label.grid(row=row_idx, column=0, sticky="w", pady=(5, 2))
