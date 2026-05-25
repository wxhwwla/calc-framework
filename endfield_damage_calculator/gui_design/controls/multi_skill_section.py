#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""多技能高级页区块。"""

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

from .multi_skill_rows import (
    _spell_abnormal_row_label,
    clear_all_abnormal_counts,
    rebuild_multi_skill_segment_rows,
)

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

    def _hint(row: int, text: str, *, box_height: int) -> int:
        """说明文案：固定高度容器 + 以高级页整宽换行，避免 ScrollableFrame 裁切。"""
        hint_box = ctk.CTkFrame(content, height=box_height, fg_color="transparent")
        hint_box.grid(row=row, column=0, padx=4, pady=(0, 6), sticky="ew")
        hint_box.grid_propagate(False)
        hint_box.grid_columnconfigure(0, weight=1)
        hint_box.grid_rowconfigure(0, weight=1)
        hint_label = ctk.CTkLabel(
            hint_box,
            text=text,
            font=app.small_font,
            text_color="#888888",
            justify="left",
            anchor="nw",
        )
        hint_label.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        wrap_label(hint_label, hint_box)
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

    mr = _hint(mr, MULTI_SKILL_COUNTS_HINT, box_height=MULTI_SKILL_HINT_BOX_HEIGHT)

    rebuild_multi_skill_segment_rows(app)

    mr = _section("物理异常", mr)
    mr = _hint(mr, PHYSICAL_ABNORMAL_HINT, box_height=PHYSICAL_ABNORMAL_HINT_BOX_HEIGHT)

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
    mr = _hint(mr, SPELL_ABNORMAL_HINT, box_height=SPELL_ABNORMAL_HINT_BOX_HEIGHT)

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
    """切换「使用手动次数」：不即时重绘三列，仅标记待确认。"""
    mark = getattr(app, "_mark_loadout_pending", None)
    if callable(mark):
        mark()
