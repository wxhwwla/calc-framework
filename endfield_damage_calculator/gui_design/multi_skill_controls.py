#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""底栏「多技能次数」区控件（与 search_controls 对称）。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Optional

from utils.platform_win32_patch import apply_platform_win32_patch

apply_platform_win32_patch()
import customtkinter as ctk

from calculation.skill_segments import list_segment_count_specs
from calculation.physical_abnormal import PHYSICAL_ABNORMAL_LEVELS, PHYSICAL_ABNORMAL_TYPES
from calculation.spell_abnormal import SPELL_ABNORMAL_LEVELS, SPELL_ABNORMAL_TYPES
from gui_design.confirm_refresh import normalize_skill_count_text, skill_count_commit_changed
from gui_design.gui_layout import (
    ANOMALY_MATRIX_LABEL_MINSIZE,
    multi_skill_segment_box_height,
)
from gui_design.label_layout import bind_wrapped_label
from gui_design.panel_hints import (
    MULTI_SKILL_COUNTS_HINT,
    PHYSICAL_ABNORMAL_HINT,
    SPELL_ABNORMAL_HINT,
)

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


def read_manual_physical_abnormal_counts(app: "DamageCalculatorApp") -> dict[str, int]:
    """读取 GUI 物理异常矩阵次数（键如 ``猛击:3``）。"""

    def _to_int(text: str) -> int:
        try:
            return max(0, int(float(text)))
        except (TypeError, ValueError):
            return 0

    counts: dict[str, int] = {}
    vars_map = getattr(app, "_physical_abnormal_count_vars", None) or {}
    for key, var in vars_map.items():
        counts[key] = _to_int(var.get())
    return counts


def read_manual_spell_abnormal_counts(app: "DamageCalculatorApp") -> dict[str, int]:
    """读取 GUI 法术异常矩阵次数（键如 ``灼热异常:2``）。"""

    def _to_int(text: str) -> int:
        try:
            return max(0, int(float(text)))
        except (TypeError, ValueError):
            return 0

    counts: dict[str, int] = {}
    vars_map = getattr(app, "_spell_abnormal_count_vars", None) or {}
    for key, var in vars_map.items():
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


def apply_physical_abnormal_counts_to_app(app: "DamageCalculatorApp", counts: dict[str, int]) -> None:
    """将物理异常次数写回矩阵输入框（预设导入用）。"""
    vars_map = getattr(app, "_physical_abnormal_count_vars", None) or {}
    for abnormal in PHYSICAL_ABNORMAL_TYPES:
        for level in PHYSICAL_ABNORMAL_LEVELS:
            key = f"{abnormal}:{level}"
            var = vars_map.get(key)
            if var is None:
                continue
            value = max(0, int(float(counts.get(key, 0))))
            var.set(str(value))


def apply_spell_abnormal_counts_to_app(app: "DamageCalculatorApp", counts: dict[str, int]) -> None:
    """将法术异常次数写回矩阵输入框（预设导入用）。"""
    vars_map = getattr(app, "_spell_abnormal_count_vars", None) or {}
    for abnormal in SPELL_ABNORMAL_TYPES:
        for level in SPELL_ABNORMAL_LEVELS:
            key = f"{abnormal}:{level}"
            var = vars_map.get(key)
            if var is None:
                continue
            value = max(0, int(float(counts.get(key, 0))))
            var.set(str(value))


def _spell_abnormal_row_label(abnormal_key: str) -> str:
    """法术异常矩阵行标签：窄列下用缩写避免裁切。"""
    if abnormal_key == "碎冰":
        return "碎冰"
    if abnormal_key.endswith("异常"):
        return f"{abnormal_key[:-2]}·异"
    if abnormal_key.endswith("爆发"):
        return f"{abnormal_key[:-2]}·爆"
    return abnormal_key


def clear_all_abnormal_counts(app: "DamageCalculatorApp") -> None:
    """一键清空物理与法术异常次数。"""
    for var in (getattr(app, "_physical_abnormal_count_vars", None) or {}).values():
        var.set("0")
    for var in (getattr(app, "_spell_abnormal_count_vars", None) or {}).values():
        var.set("0")
    schedule = getattr(app, "_schedule_confirm", None)
    if callable(schedule):
        schedule()


def clear_physical_abnormal_counts(app: "DamageCalculatorApp") -> None:
    """一键清空异常次数。"""
    for var in (getattr(app, "_physical_abnormal_count_vars", None) or {}).values():
        var.set("0")
    schedule = getattr(app, "_schedule_confirm", None)
    if callable(schedule):
        schedule()


def clear_spell_abnormal_counts(app: "DamageCalculatorApp") -> None:
    """一键清空法术异常次数。"""
    for var in (getattr(app, "_spell_abnormal_count_vars", None) or {}).values():
        var.set("0")
    schedule = getattr(app, "_schedule_confirm", None)
    if callable(schedule):
        schedule()


def place_multi_skill_section(
    app: "DamageCalculatorApp",
    parent: ctk.CTkFrame,
    *,
    wrap_label: Callable[[ctk.CTkLabel, ctk.CTkBaseClass], None],
    schedule_confirm: Callable[..., None],
) -> None:
    """在底栏右侧放置多技能次数开关与段级输入行。"""
    parent.grid_rowconfigure(0, weight=1)
    parent.grid_columnconfigure(0, weight=1)

    viewport = ctk.CTkScrollableFrame(parent, fg_color="transparent")
    viewport.grid(row=0, column=0, sticky="nsew")
    viewport.grid_columnconfigure(0, weight=1)
    app._multi_skill_controls_viewport = viewport
    content = viewport

    def _section(title: str, row: int) -> int:
        ctk.CTkLabel(
            content,
            text=title,
            font=app.big_font,
            text_color="#FF6B6B",
        ).grid(row=row, column=0, padx=4, pady=(6, 2), sticky="w")
        return row + 1

    def _place(row: int, widget, *, pady: tuple[int, int] = (0, 4)) -> int:
        widget.grid(row=row, column=0, padx=4, pady=pady, sticky="ew")
        return row + 1

    def _hint(row: int, text: str) -> int:
        """说明文案：以右侧列宽换行，避免 ScrollableFrame 内横向裁切。"""
        hint_label = ctk.CTkLabel(
            content,
            text=text,
            font=app.small_font,
            text_color="#888888",
            justify="left",
            anchor="nw",
        )
        hint_label.grid(row=row, column=0, padx=8, pady=(0, 6), sticky="ew")
        bind_wrapped_label(hint_label, content, viewport=parent, padding=28)
        return row + 1

    mr = 0
    mr = _section("多技能次数", mr)
    count_switch = ctk.CTkSwitch(
        content,
        text="使用手动次数",
        variable=app.use_manual_skill_counts_var,
        font=app.small_font,
        command=lambda: on_manual_skill_counts_switch_changed(app),
    )
    mr = _place(mr, count_switch, pady=(0, 6))

    body = ctk.CTkFrame(content, fg_color="transparent")
    body.grid(row=mr, column=0, columnspan=2, padx=4, pady=(4, 4), sticky="ew")
    body.grid_columnconfigure(0, weight=1)
    body.grid_columnconfigure(1, weight=0, minsize=72)
    app._multi_skill_counts_body = body
    mr += 1

    mr = _hint(mr, MULTI_SKILL_COUNTS_HINT)

    rebuild_multi_skill_segment_rows(app)

    mr = _section("物理异常", mr)
    mr = _hint(mr, PHYSICAL_ABNORMAL_HINT)

    mode_row = ctk.CTkFrame(content, fg_color="transparent")
    mode_row.grid(row=mr, column=0, padx=4, pady=(0, 4), sticky="ew")
    mode_row.grid_columnconfigure(1, weight=1)
    ctk.CTkLabel(
        mode_row,
        text="伤害口径",
        font=app.small_font,
        text_color="#CCCCCC",
    ).grid(row=0, column=0, padx=(0, 6), pady=0, sticky="w")
    ctk.CTkOptionMenu(
        mode_row,
        variable=app.damage_component_mode_var,
        values=["仅技能", "仅异常", "技能+异常"],
        font=app.small_font,
        command=lambda _v: schedule_confirm(),
    ).grid(row=0, column=1, padx=0, pady=0, sticky="ew")
    mr += 1

    expected_switch = ctk.CTkSwitch(
        content,
        text="期望伤害模式",
        variable=app.use_expected_crit_var,
        font=app.small_font,
        command=lambda: schedule_confirm(),
    )
    mr = _place(mr, expected_switch, pady=(0, 4))

    conditional_switch = ctk.CTkSwitch(
        content,
        text="装备条件暴击",
        variable=app.include_conditional_equipment_crit_var,
        font=app.small_font,
        command=lambda: schedule_confirm(),
    )
    mr = _place(mr, conditional_switch, pady=(0, 6))

    bonus_row = ctk.CTkFrame(content, fg_color="transparent")
    bonus_row.grid(row=mr, column=0, padx=4, pady=(0, 6), sticky="ew")
    bonus_row.grid_columnconfigure(1, weight=1)
    bonus_row.grid_columnconfigure(3, weight=1)
    ctk.CTkLabel(
        bonus_row,
        text="额外暴击率%",
        font=app.small_font,
        text_color="#CCCCCC",
    ).grid(row=0, column=0, padx=(0, 4), pady=0, sticky="w")
    crit_rate_entry = ctk.CTkEntry(
        bonus_row,
        textvariable=app.extra_crit_rate_percent_var,
        width=72,
        font=app.small_font,
    )
    crit_rate_entry.grid(row=0, column=1, padx=(0, 8), pady=0, sticky="ew")
    ctk.CTkLabel(
        bonus_row,
        text="额外暴伤%",
        font=app.small_font,
        text_color="#CCCCCC",
    ).grid(row=0, column=2, padx=(0, 4), pady=0, sticky="w")
    crit_damage_entry = ctk.CTkEntry(
        bonus_row,
        textvariable=app.extra_crit_damage_percent_var,
        width=72,
        font=app.small_font,
    )
    crit_damage_entry.grid(row=0, column=3, padx=0, pady=0, sticky="ew")
    crit_rate_entry.bind("<FocusOut>", lambda _e: schedule_confirm())
    crit_rate_entry.bind("<Return>", lambda _e: schedule_confirm())
    crit_damage_entry.bind("<FocusOut>", lambda _e: schedule_confirm())
    crit_damage_entry.bind("<Return>", lambda _e: schedule_confirm())
    mr += 1

    matrix = ctk.CTkFrame(content, fg_color="transparent")
    matrix.grid(row=mr, column=0, padx=4, pady=(0, 4), sticky="ew")
    matrix.grid_columnconfigure(0, weight=0, minsize=ANOMALY_MATRIX_LABEL_MINSIZE)
    for idx, level in enumerate(PHYSICAL_ABNORMAL_LEVELS, start=1):
        matrix.grid_columnconfigure(idx, weight=0, minsize=44)
        ctk.CTkLabel(
            matrix,
            text=f"L{level}",
            font=app.small_font,
            text_color="#BBBBBB",
        ).grid(row=0, column=idx, padx=(2, 2), pady=(0, 2), sticky="n")
    ctk.CTkLabel(
        matrix,
        text="异常",
        font=app.small_font,
        text_color="#BBBBBB",
    ).grid(row=0, column=0, padx=(0, 4), pady=(0, 2), sticky="w")

    app._physical_abnormal_count_vars = {}

    def _on_abnormal_commit(var: ctk.StringVar) -> None:
        normalized = normalize_skill_count_text(var.get())
        if var.get() != normalized:
            var.set(normalized)
        schedule_confirm()

    for row_idx, abnormal in enumerate(PHYSICAL_ABNORMAL_TYPES, start=1):
        ctk.CTkLabel(
            matrix,
            text=abnormal,
            font=app.small_font,
            text_color="#CCCCCC",
        ).grid(row=row_idx, column=0, padx=(0, 4), pady=(0, 2), sticky="w")
        for col_idx, level in enumerate(PHYSICAL_ABNORMAL_LEVELS, start=1):
            key = f"{abnormal}:{level}"
            var = ctk.StringVar(value="0")
            app._physical_abnormal_count_vars[key] = var
            entry = ctk.CTkEntry(
                matrix,
                textvariable=var,
                width=44,
                font=app.small_font,
                justify="center",
            )
            entry.grid(row=row_idx, column=col_idx, padx=2, pady=(0, 2), sticky="ew")
            entry.bind("<FocusOut>", lambda _e, _v=var: _on_abnormal_commit(_v))
            entry.bind("<Return>", lambda _e, _v=var: _on_abnormal_commit(_v))
    mr += 1

    mr = _section("法术异常", mr)
    mr = _hint(mr, SPELL_ABNORMAL_HINT)

    spell_matrix = ctk.CTkFrame(content, fg_color="transparent")
    spell_matrix.grid(row=mr, column=0, padx=4, pady=(0, 4), sticky="ew")
    spell_matrix.grid_columnconfigure(0, weight=0, minsize=ANOMALY_MATRIX_LABEL_MINSIZE)
    for idx, level in enumerate(SPELL_ABNORMAL_LEVELS, start=1):
        spell_matrix.grid_columnconfigure(idx, weight=0, minsize=44)
        ctk.CTkLabel(
            spell_matrix,
            text=f"L{level}",
            font=app.small_font,
            text_color="#BBBBBB",
        ).grid(row=0, column=idx, padx=(2, 2), pady=(0, 2), sticky="n")
    ctk.CTkLabel(
        spell_matrix,
        text="异常",
        font=app.small_font,
        text_color="#BBBBBB",
    ).grid(row=0, column=0, padx=(0, 4), pady=(0, 2), sticky="w")

    app._spell_abnormal_count_vars = {}
    for row_idx, abnormal in enumerate(SPELL_ABNORMAL_TYPES, start=1):
        ctk.CTkLabel(
            spell_matrix,
            text=_spell_abnormal_row_label(abnormal),
            font=app.small_font,
            text_color="#CCCCCC",
        ).grid(row=row_idx, column=0, padx=(0, 4), pady=(0, 2), sticky="w")
        for col_idx, level in enumerate(SPELL_ABNORMAL_LEVELS, start=1):
            key = f"{abnormal}:{level}"
            var = ctk.StringVar(value="0")
            app._spell_abnormal_count_vars[key] = var
            entry = ctk.CTkEntry(
                spell_matrix,
                textvariable=var,
                width=44,
                font=app.small_font,
                justify="center",
            )
            entry.grid(row=row_idx, column=col_idx, padx=2, pady=(0, 2), sticky="ew")
            entry.bind("<FocusOut>", lambda _e, _v=var: _on_abnormal_commit(_v))
            entry.bind("<Return>", lambda _e, _v=var: _on_abnormal_commit(_v))
    mr += 1

    clear_all_btn = ctk.CTkButton(
        content,
        text="清空全部异常次数",
        font=app.small_font,
        height=28,
        command=lambda: clear_all_abnormal_counts(app),
    )
    _place(mr, clear_all_btn, pady=(0, 8))


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
