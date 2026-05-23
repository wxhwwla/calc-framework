#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""底栏「多技能次数」区控件（与 search_controls 对称）。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

import customtkinter as ctk

from gui_design.confirm_refresh import normalize_skill_count_text, skill_count_commit_changed
from gui_design.panel_hints import MULTI_SKILL_COUNTS_HINT

if TYPE_CHECKING:
    from gui_design.gui import DamageCalculatorApp


def read_manual_multi_skill_counts(app: "DamageCalculatorApp") -> dict[str, int]:
    """读取 GUI 手动技能次数。"""

    def _to_int(text: str) -> int:
        try:
            return max(0, int(float(text)))
        except (TypeError, ValueError):
            return 0

    return {
        "战技": _to_int(app.skill_count_1_var.get()),
        "连携技": _to_int(app.skill_count_2_var.get()),
        "终结技": _to_int(app.skill_count_3_var.get()),
    }


def place_multi_skill_section(
    app: "DamageCalculatorApp",
    parent: ctk.CTkFrame,
    *,
    wrap_label: Callable[[ctk.CTkLabel, ctk.CTkBaseClass], None],
    schedule_confirm: Callable[..., None],
) -> None:
    """在底栏右侧放置多技能次数开关与输入行。"""
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
        command=schedule_confirm,
    )
    mr = _place(mr, count_switch, pady=(0, 6))
    parent.grid_columnconfigure(1, weight=0, minsize=72)

    for label_text, value_var, storage_key in (
        ("战技次数", app.skill_count_1_var, "战技"),
        ("连携技次数", app.skill_count_2_var, "连携技"),
        ("终结技次数", app.skill_count_3_var, "终结技"),
    ):
        _place_skill_count_row(
            app,
            parent=parent,
            row=mr,
            label_text=label_text,
            value_var=value_var,
            storage_key=storage_key,
            schedule_confirm=schedule_confirm,
        )
        mr += 1

    multi_skill_hint = ctk.CTkLabel(
        parent,
        text=MULTI_SKILL_COUNTS_HINT,
        font=app.small_font,
        text_color="#888888",
        justify="left",
        anchor="w",
    )
    mr = _place(mr, multi_skill_hint)
    wrap_label(multi_skill_hint, parent)


def _place_skill_count_row(
    app: "DamageCalculatorApp",
    *,
    parent: ctk.CTkFrame,
    row: int,
    label_text: str,
    value_var: ctk.StringVar,
    storage_key: str,
    schedule_confirm: Callable[..., None],
) -> None:
    ctk.CTkLabel(
        parent,
        text=label_text,
        font=app.small_font,
        text_color="#CCCCCC",
    ).grid(row=row, column=0, padx=8, pady=(0, 2), sticky="w")

    app._skill_count_last_committed[storage_key] = normalize_skill_count_text(value_var.get())

    def _on_change(*_args: object) -> None:
        normalized, changed = skill_count_commit_changed(
            value_var.get(),
            app._skill_count_last_committed.get(storage_key),
        )
        if not changed:
            return
        app._skill_count_last_committed[storage_key] = normalized
        if (value_var.get() or "").strip() != normalized:
            value_var.set(normalized)
        if app._current_calculation_mode() == "multi_skill_search":
            schedule_confirm()

    entry = ctk.CTkEntry(
        parent,
        textvariable=value_var,
        width=72,
        font=app.small_font,
    )
    entry.grid(row=row, column=1, padx=(4, 8), pady=(0, 2), sticky="e")
    entry.bind("<FocusOut>", _on_change)
    entry.bind("<Return>", _on_change)
