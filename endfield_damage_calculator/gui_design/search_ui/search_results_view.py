#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全量遍历结果展示（CTk 弹窗；文案见 search_results_lines）。"""

from __future__ import annotations

from typing import Any, Optional, Sequence

from utils.platform_win32_patch import apply_platform_win32_patch

apply_platform_win32_patch()
import customtkinter as ctk

from calculation.loadout.optimizer import LoadoutScore
from gui_design.presentation.search_results_lines import (
    build_search_results_report_lines,
    export_paths_to_strings,
    loadout_scores_from_payload,
)
from utils.gui_fonts import default_ui_font

# 弹窗默认尺寸（主窗口右侧区域较窄，结果用独立窗口展示）
DEFAULT_DIALOG_WIDTH = 920
DEFAULT_DIALOG_HEIGHT = 720

__all__ = (
    "DEFAULT_DIALOG_HEIGHT",
    "DEFAULT_DIALOG_WIDTH",
    "build_search_results_report_lines",
    "export_paths_to_strings",
    "loadout_scores_from_payload",
    "show_search_results_dialog",
)


def show_search_results_dialog(
    parent: ctk.CTk,
    *,
    title: str,
    lines: list[str],
    width: int = DEFAULT_DIALOG_WIDTH,
    height: int = DEFAULT_DIALOG_HEIGHT,
) -> None:
    """在独立大窗口中展示遍历结果（可滚动）。"""
    dialog = ctk.CTkToplevel(parent)
    dialog.title(title)
    dialog.geometry(f"{width}x{height}")
    dialog.minsize(640, 480)
    dialog.transient(parent)

    header = ctk.CTkLabel(
        dialog,
        text=title,
        font=default_ui_font(size=18, weight="bold"),
    )
    header.pack(anchor="w", padx=12, pady=(12, 4))

    textbox = ctk.CTkTextbox(
        dialog,
        font=default_ui_font(size=13),
        wrap="word",
    )
    textbox.pack(fill="both", expand=True, padx=12, pady=(0, 12))
    textbox.insert("1.0", "\n".join(lines))
    textbox.configure(state="disabled")

    close_btn = ctk.CTkButton(dialog, text="关闭", font=default_ui_font(size=12), command=dialog.destroy, width=120)
    close_btn.pack(pady=(0, 12))

    dialog.after(100, dialog.lift)
    dialog.after(120, dialog.focus_force)
