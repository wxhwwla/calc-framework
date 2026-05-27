#!/usr/bin/env python3
"""
属性三列 CTk 渲染与确认刷新编排（依赖 display_lines 文案）。
"""

from __future__ import annotations

from typing import Any

from utils.platform_win32_patch import apply_platform_win32_patch

apply_platform_win32_patch()
import customtkinter as ctk

from calculation.loadout.optimizer import WeaponCandidate
from calculation.multiplicative_zones.zone_snapshot import (
    MultiplicativeZoneSelection,
    WeaponBonusSelection,
    compute_multiplicative_zone_snapshot,
)
from gui_design.app.loadout_evaluation import build_search_preview_lines
from gui_design.app.loadout_state import LoadoutState
from gui_design.presentation.display_lines import (
    build_single_hit_damage_lines,
)


def _display_zone_data(
    right_scroll: ctk.CTkScrollableFrame,
    char_data: dict[str, Any] | None,
    weapon_data: dict[str, Any] | None,
    char_level: int,
    weapon_level: int,
    normal_skill_1_name: str = "",
    normal_skill_1_level: int = 1,
    normal_skill_2_name: str = "",
    normal_skill_2_level: int = 1,
    normal_skill_3_name: str = "",
    normal_skill_3_level: int = 0,
    special_skill_1_name: str = "",
    special_skill_1_level: int = 1,
    special_skill_1_stack: int = 0,
    special_skill_2_name: str = "",
    special_skill_2_level: int = 1,
    special_skill_2_stack: int = 0,
    trust_level: int = 0,
    big_font: ctk.CTkFont | None = None,
    small_font: ctk.CTkFont | None = None,
    loadout: LoadoutState | None = None,
    calculation_mode: str = "zone_snapshot",
    skill_1_level: int = 0,
    skill_2_level: int = 0,
    skill_3_level: int = 0,
    multi_skill_manual_counts: dict[str, int] | None = None,
    use_manual_multi_skill_counts: bool = False,
    preview_weapon_candidates: list[WeaponCandidate] | None = None,
    preview_scope_label: str = "",
    preview_equipment_catalog: dict[str, list[dict]] | None = None,
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

    if loadout is not None and calculation_mode in ("single_skill_search", "multi_skill_search"):
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
