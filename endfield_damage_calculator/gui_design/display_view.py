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
    evaluate_display_state,
)
from gui_design.loadout_evaluation import build_search_preview_lines
from calculation.loadout_slot_search import FixedLoadoutSelection
from gui_design.display_request import DisplayRequest
from gui_design.loadout_state import LoadoutState, read_loadout_from_panels
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

    specials = loadout.weapon_special_kwargs()
    _display_zone_data(
        right_scroll,
        char_data,
        weapon_data,
        loadout.char_level,
        loadout.weapon_level,
        specials["sa1_name"],
        specials["sa1_level"],
        specials["sa2_name"],
        specials["sa2_level"],
        specials["sa3_name"],
        specials["sa3_level"],
        specials["ws_name"],
        specials["ws_level"],
        specials["ws2_name"],
        specials["ws2_level"],
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


def confirm_from_display_request(
    char_attr_scroll: ctk.CTkScrollableFrame | None,
    weapon_attr_scroll: ctk.CTkScrollableFrame | None,
    right_scroll: ctk.CTkScrollableFrame | None,
    request: DisplayRequest,
    *,
    big_font: ctk.CTkFont,
    small_font: ctk.CTkFont,
) -> None:
    """根据 DisplayRequest 刷新三列展示（不再从 panel 二次刮取）。"""
    if char_attr_scroll is None or weapon_attr_scroll is None or right_scroll is None:
        return

    for widget in char_attr_scroll.winfo_children():
        widget.destroy()
    for widget in weapon_attr_scroll.winfo_children():
        widget.destroy()
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

    if not ui_state["char_message"]:
        char_lines = build_character_attribute_lines(
            char_data,
            loadout.char_level,
            skill_1_level=s1,
            skill_2_level=s2,
            skill_3_level=s3,
        )
        _render_lines(
            char_attr_scroll,
            char_lines,
            font=small_font,
            text_color="#B8B8B8",
        )
    else:
        _render_placeholder(char_attr_scroll, ui_state["char_message"], font=small_font)

    specials = loadout.weapon_special_kwargs()
    if not ui_state["weapon_message"]:
        weapon_lines = build_weapon_attribute_lines(
            weapon_data,
            loadout.weapon_level,
            **specials,
        )
        _render_lines(
            weapon_attr_scroll,
            weapon_lines,
            font=small_font,
            text_color="#4ECDC4",
        )
    else:
        _render_placeholder(weapon_attr_scroll, ui_state["weapon_message"], font=small_font)

    if not ui_state["can_update_zone"]:
        return

    _display_zone_data(
        right_scroll,
        char_data,
        weapon_data,
        loadout.char_level,
        loadout.weapon_level,
        specials["sa1_name"],
        specials["sa1_level"],
        specials["sa2_name"],
        specials["sa2_level"],
        specials["sa3_name"],
        specials["sa3_level"],
        specials["ws_name"],
        specials["ws_level"],
        specials["ws2_name"],
        specials["ws2_level"],
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
    """确认选择（测试/兼容入口：从 panel 组装 DisplayRequest）。"""
    counts = multi_skill_manual_counts or {}
    loadout = read_loadout_from_panels(
        char_panel,
        weapon_panel,
        calculation_mode=calculation_mode,
        weapon_scope_label=preview_scope_label or "当前武器",
        equipment_scope_label=preview_equipment_scope_label or "全部装备",
        fixed_loadout=FixedLoadoutSelection(),
        use_manual_multi_skill_counts=use_manual_multi_skill_counts,
        manual_counts=counts,
        enemy_defense=enemy_defense,
    )
    if loadout is None:
        for scroll, msg in (
            (char_attr_scroll, "请选择有效角色"),
            (weapon_attr_scroll, "请选择有效武器"),
        ):
            if scroll is not None:
                for widget in scroll.winfo_children():
                    widget.destroy()
                _render_placeholder(scroll, msg, font=small_font)
        if right_scroll is not None:
            for widget in right_scroll.winfo_children():
                widget.destroy()
        return

    request = DisplayRequest(
        loadout=loadout,
        equipment_catalog=preview_equipment_catalog or {},
        preview_weapon_candidates=tuple(preview_weapon_candidates or []),
    )
    confirm_from_display_request(
        char_attr_scroll,
        weapon_attr_scroll,
        right_scroll,
        request,
        big_font=big_font,
        small_font=small_font,
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
    loadout: Optional[LoadoutState] = None,
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

    if (
        loadout is not None
        and calculation_mode in ("single_skill_search", "multi_skill_search")
    ):
        for text in build_search_preview_lines(
            loadout,
            equipment_catalog=preview_equipment_catalog or {},
            preview_weapon_candidates=preview_weapon_candidates,
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
