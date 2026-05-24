#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""底栏「多技能次数」区控件（与 search_controls 对称）。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Optional

from utils.platform_win32_patch import apply_platform_win32_patch

apply_platform_win32_patch()
import customtkinter as ctk

from calculation.skill_segments import list_segment_count_specs
from gui_design.confirm_refresh import normalize_skill_count_text, skill_count_commit_changed
from gui_design.gui_layout import (
    MULTI_SKILL_HINT_BOX_HEIGHT,
    MULTI_SKILL_SEGMENT_BOX_MIN_HEIGHT,
    multi_skill_segment_box_height,
)
from gui_design.panel_hints import MULTI_SKILL_COUNTS_HINT

if TYPE_CHECKING:
    from gui_design.gui import DamageCalculatorApp


def ensure_multi_skill_segment_rows(app: "DamageCalculatorApp") -> None:
    """技能等级或角色变化时重建段级输入行（保留同键次数）。"""
    char_data = app.char_panel.get_selected_data() if app.char_panel else None
    skill_panel = app.char_panel.skill_level_panel if app.char_panel else None
    if not char_data or not skill_panel:
        return
    try:
        s1 = int(skill_panel.skill_1_level.get())
        s2 = int(skill_panel.skill_2_level.get())
        s3 = int(skill_panel.skill_3_level.get())
    except (TypeError, ValueError):
        s1 = s2 = s3 = 0
    specs = list_segment_count_specs(
        char_data,
        skill_1_level=s1,
        skill_2_level=s2,
        skill_3_level=s3,
    )
    keys = tuple(spec["key"] for spec in specs)
    if getattr(app, "_segment_row_keys", None) == keys:
        return
    app._segment_row_keys = keys
    rebuild_multi_skill_segment_rows(app)


def read_manual_multi_skill_counts(app: "DamageCalculatorApp") -> dict[str, int]:
    """读取 GUI 段级手动次数（键如 ``连携技:2``）。"""

    def _to_int(text: str) -> int:
        try:
            return max(0, int(float(text)))
        except (TypeError, ValueError):
            return 0

    counts: dict[str, int] = {}
    segment_vars = getattr(app, "_segment_count_vars", None) or {}
    for key, var in segment_vars.items():
        counts[key] = _to_int(var.get())
    return counts


def rebuild_multi_skill_segment_rows(app: "DamageCalculatorApp") -> None:
    """按当前角色技能等级重建段级次数输入行。"""
    frame = getattr(app, "_multi_skill_counts_body", None)
    if frame is None:
        return

    for child in frame.winfo_children():
        child.destroy()

    char_data = app.char_panel.get_selected_data() if app.char_panel else None
    skill_panel = app.char_panel.skill_level_panel if app.char_panel else None
    if not char_data or not skill_panel:
        return

    try:
        s1 = int(skill_panel.skill_1_level.get())
        s2 = int(skill_panel.skill_2_level.get())
        s3 = int(skill_panel.skill_3_level.get())
    except (TypeError, ValueError):
        s1 = s2 = s3 = 0

    specs = list_segment_count_specs(
        char_data,
        skill_1_level=s1,
        skill_2_level=s2,
        skill_3_level=s3,
    )

    preserved = dict(getattr(app, "_segment_count_vars", {}))
    app._segment_count_vars = {}
    app._skill_count_last_committed = {}

    frame.grid_columnconfigure(0, weight=1)
    frame.grid_columnconfigure(1, weight=0, minsize=72)

    schedule_confirm = app._schedule_confirm

    for row_idx, spec in enumerate(specs):
        key = str(spec["key"])
        label_text = str(spec["label"])
        prev = preserved.get(key)
        default = prev.get() if prev is not None else "0"
        value_var = ctk.StringVar(value=default)
        app._segment_count_vars[key] = value_var
        app._skill_count_last_committed[key] = normalize_skill_count_text(default)

        ctk.CTkLabel(
            frame,
            text=label_text,
            font=app.small_font,
            text_color="#CCCCCC",
        ).grid(row=row_idx, column=0, padx=8, pady=(2, 2), sticky="w")

        def _make_change_handler(
            var: ctk.StringVar,
            storage_key: str,
        ) -> Callable[..., None]:
            def _on_change(*_args: object) -> None:
                normalized, changed = skill_count_commit_changed(
                    var.get(),
                    app._skill_count_last_committed.get(storage_key),
                )
                if not changed:
                    return
                app._skill_count_last_committed[storage_key] = normalized
                if (var.get() or "").strip() != normalized:
                    var.set(normalized)
                if app._current_calculation_mode() == "multi_skill_search":
                    schedule_confirm()

            return _on_change

        on_change = _make_change_handler(value_var, key)
        entry = ctk.CTkEntry(
            frame,
            textvariable=value_var,
            width=72,
            font=app.small_font,
        )
        entry.grid(row=row_idx, column=1, padx=(4, 8), pady=(0, 2), sticky="e")
        entry.bind("<FocusOut>", on_change)
        entry.bind("<Return>", on_change)

    box_height = multi_skill_segment_box_height(len(specs))
    segment_box = getattr(app, "_multi_skill_segment_box", None)
    if segment_box is not None:
        segment_box.configure(height=box_height)


def apply_segment_counts_to_app(app: "DamageCalculatorApp", counts: dict[str, int]) -> None:
    """将段级次数写回动态输入框（预设导入用）。"""
    from calculation.multi_skill_search_eval import build_skill_scenarios_from_levels
    from calculation.skill_segments import normalize_manual_segment_counts

    rebuild_multi_skill_segment_rows(app)
    char_data = app.char_panel.get_selected_data() if app.char_panel else None
    skill_panel = app.char_panel.skill_level_panel if app.char_panel else None
    if not char_data or not skill_panel:
        return
    try:
        s1 = int(skill_panel.skill_1_level.get())
        s2 = int(skill_panel.skill_2_level.get())
        s3 = int(skill_panel.skill_3_level.get())
    except (TypeError, ValueError):
        s1 = s2 = s3 = 0
    scenarios = build_skill_scenarios_from_levels(
        char_data,
        skill_1_level=s1,
        skill_2_level=s2,
        skill_3_level=s3,
    )
    normalized = normalize_manual_segment_counts(counts, scenarios)
    segment_vars = getattr(app, "_segment_count_vars", None) or {}
    for key, var in segment_vars.items():
        var.set(str(normalized.get(key, 0)))
        app._skill_count_last_committed[key] = normalize_skill_count_text(var.get())


def place_multi_skill_section(
    app: "DamageCalculatorApp",
    parent: ctk.CTkFrame,
    *,
    wrap_label: Callable[[ctk.CTkLabel, ctk.CTkBaseClass], None],
    schedule_confirm: Callable[..., None],
) -> None:
    """在底栏右侧放置多技能次数开关与段级输入行。"""
    parent.grid_columnconfigure(0, weight=1)

    def _section(title: str, row: int) -> int:
        ctk.CTkLabel(
            parent,
            text=title,
            font=app.big_font,
            text_color="#FF6B6B",
        ).grid(row=row, column=0, padx=4, pady=(6, 2), sticky="w")
        return row + 1

    def _place(row: int, widget, *, pady: tuple[int, int] = (0, 4)) -> int:
        widget.grid(row=row, column=0, padx=4, pady=pady, sticky="ew")
        return row + 1

    mr = 0
    mr = _section("多技能次数", mr)
    count_switch = ctk.CTkSwitch(
        parent,
        text="使用手动次数",
        variable=app.use_manual_skill_counts_var,
        font=app.small_font,
        command=lambda: on_manual_skill_counts_switch_changed(app),
    )
    mr = _place(mr, count_switch, pady=(0, 6))

    segment_box = ctk.CTkFrame(
        parent,
        height=MULTI_SKILL_SEGMENT_BOX_MIN_HEIGHT,
        fg_color="transparent",
    )
    segment_box.grid(row=mr, column=0, columnspan=2, padx=4, pady=(4, 4), sticky="ew")
    segment_box.grid_propagate(False)
    segment_box.grid_columnconfigure(0, weight=1)
    segment_box.grid_rowconfigure(0, weight=1)
    app._multi_skill_segment_box = segment_box

    body = ctk.CTkScrollableFrame(
        segment_box,
        fg_color="transparent",
        scrollbar_button_color="#444444",
        scrollbar_button_hover_color="#666666",
    )
    body.grid(row=0, column=0, sticky="nsew", padx=2, pady=(4, 2))
    body.grid_columnconfigure(0, weight=1)
    body.grid_columnconfigure(1, weight=0, minsize=72)
    app._multi_skill_counts_body = body
    mr += 1

    hint_box = ctk.CTkFrame(parent, height=MULTI_SKILL_HINT_BOX_HEIGHT, fg_color="transparent")
    hint_box.grid(row=mr, column=0, columnspan=2, padx=4, pady=(0, 4), sticky="ew")
    hint_box.grid_propagate(False)
    hint_box.grid_columnconfigure(0, weight=1)
    hint_box.grid_rowconfigure(0, weight=1)
    multi_skill_hint = ctk.CTkLabel(
        hint_box,
        text=MULTI_SKILL_COUNTS_HINT,
        font=app.small_font,
        text_color="#888888",
        justify="left",
        anchor="nw",
    )
    multi_skill_hint.grid(row=0, column=0, sticky="nsew", padx=4, pady=2)
    wrap_label(multi_skill_hint, hint_box)
    mr += 1

    rebuild_multi_skill_segment_rows(app)


def on_manual_skill_counts_switch_changed(app: "DamageCalculatorApp") -> None:
    """
    切换「使用手动次数」时的轻量刷新。

    不 destroy 角色/武器属性列，避免整窗闪屏与底栏比例跳动；
    多技能预览模式下才重绘右侧列。
    """
    from gui_design.display_request import build_display_request
    from gui_design.display_view import refresh_right_column_from_request
    from gui_design.enhancement_controls import refresh_damage_snapshot
    from gui_design.loadout_state import read_loadout_from_app
    from gui_design.search_controls import refresh_search_estimate

    app._suppress_full_confirm_refresh = True
    try:
        loadout = read_loadout_from_app(app, ensure_segment_rows=False)
        if loadout is None:
            return

        app._confirm_refresh_signature = loadout.confirm_refresh_signature()
        refresh_damage_snapshot(app, loadout=loadout)
        refresh_search_estimate(app)

        if loadout.calculation_mode != "multi_skill_search":
            return
        if app.right_scroll is None:
            return

        request = build_display_request(
            loadout,
            app.game_data,
            preview_weapon_candidates=app._single_skill_preview_candidates(),
        )
        refresh_right_column_from_request(
            app.right_scroll,
            request,
            big_font=app.big_font,
            small_font=app.small_font,
        )
    finally:
        def _clear_suppress() -> None:
            app._suppress_full_confirm_refresh = False

        app.app.after(400, _clear_suppress)
