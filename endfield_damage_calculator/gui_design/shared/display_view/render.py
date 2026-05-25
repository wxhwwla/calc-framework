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


