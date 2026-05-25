#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""段级次数与异常行。"""

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
    MULTI_SKILL_HINT_BOX_HEIGHT,
    PHYSICAL_ABNORMAL_HINT_BOX_HEIGHT,
    SPELL_ABNORMAL_HINT_BOX_HEIGHT,
    multi_skill_segment_box_height,
)
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
    signature = segment_rows_signature(specs)
    if getattr(app, "_segment_row_signature", None) == signature:
        return
    app._segment_row_signature = signature
    rebuild_multi_skill_segment_rows(app)


def segment_rows_signature(specs: list[dict[str, object]]) -> tuple[tuple[str, str], ...]:
    """段列表签名：键 + 展示标签（含倍率%），技能等级变化时也会触发重建。"""
    return tuple((str(spec["key"]), str(spec["label"])) for spec in specs)


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

    schedule_confirm = getattr(app, "_mark_loadout_pending", app._schedule_confirm)

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

    app._segment_row_signature = segment_rows_signature(specs)


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
    schedule = getattr(app, "_mark_loadout_pending", None)
    if callable(schedule):
        schedule()


def clear_physical_abnormal_counts(app: "DamageCalculatorApp") -> None:
    """一键清空异常次数。"""
    for var in (getattr(app, "_physical_abnormal_count_vars", None) or {}).values():
        var.set("0")
    schedule = getattr(app, "_mark_loadout_pending", None)
    if callable(schedule):
        schedule()


def clear_spell_abnormal_counts(app: "DamageCalculatorApp") -> None:
    """一键清空法术异常次数。"""
    for var in (getattr(app, "_spell_abnormal_count_vars", None) or {}).values():
        var.set("0")
    schedule = getattr(app, "_mark_loadout_pending", None)
    if callable(schedule):
        schedule()


