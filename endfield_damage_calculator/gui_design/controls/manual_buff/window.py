#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""手动场外 buff 编辑窗口。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Optional

from utils.platform_win32_patch import apply_platform_win32_patch

apply_platform_win32_patch()
import customtkinter as ctk

from calculation.manual_buff.model import (
    MANUAL_BUFF_ZONE_OPTIONS,
    build_active_keys_from_counts,
    empty_buff_dict,
    get_buffs_for_key,
    set_buffs_for_key,
)

if TYPE_CHECKING:
    from gui_design.shell.app import DamageCalculatorApp

_WINDOW_TITLE = "场外 Buff 微调"
_WINDOW_WIDTH = 900
_WINDOW_HEIGHT = 600
_LEFT_PANEL_WIDTH = 260
_BUFF_ROW_HEIGHT = 36


def _format_key_label(key: str) -> str:
    parts = key.rsplit(":", 1)
    if len(parts) == 2:
        return f"{parts[0]} 第{parts[1]}次"
    return key


def open_manual_buff_window(app: DamageCalculatorApp) -> None:
    store = getattr(app, "_manual_buff_store", None)
    if store is None:
        store = empty_buff_dict()
        app._manual_buff_store = store

    window = ctk.CTkToplevel(app.app)
    window.title(_WINDOW_TITLE)
    window.geometry(f"{_WINDOW_WIDTH}x{_WINDOW_HEIGHT}")
    window.minsize(700, 400)
    window.after(100, lambda: window.lift())

    window.grid_rowconfigure(0, weight=1)
    window.grid_columnconfigure(0, weight=0, minsize=_LEFT_PANEL_WIDTH)
    window.grid_columnconfigure(1, weight=1)

    _build_left_panel(window, app, store)
    _build_right_panel(window, app, store)

    _refresh_key_list(window, app)


def _read_all_counts(app: DamageCalculatorApp) -> tuple[dict[str, int], dict[str, int], dict[str, int]]:
    from gui_design.controls.multi_skill.rows import (
        read_manual_multi_skill_counts,
        read_manual_physical_abnormal_counts,
        read_manual_spell_abnormal_counts,
    )
    skill_counts = read_manual_multi_skill_counts(app)
    pab_counts = read_manual_physical_abnormal_counts(app)
    sab_counts = read_manual_spell_abnormal_counts(app)
    return skill_counts, pab_counts, sab_counts


def _refresh_key_list(window: ctk.CTkToplevel, app: DamageCalculatorApp) -> None:
    list_frame = getattr(window, "_left_list_frame", None)
    if list_frame is None:
        return
    for child in list_frame.winfo_children():
        child.destroy()

    skill_counts, pab_counts, sab_counts = _read_all_counts(app)
    keys = build_active_keys_from_counts(
        skill_counts=skill_counts,
        physical_abnormal_counts=pab_counts,
        spell_abnormal_counts=sab_counts,
    )
    if not keys:
        ctk.CTkLabel(
            list_frame,
            text="暂无已配置的段/异常次数\n请在高级页设置次数 > 0 后重试",
            font=app.small_font,
            text_color="#888888",
        ).pack(padx=12, pady=20)
        return

    store = getattr(app, "_manual_buff_store", {})

    for key in keys:
        frame = ctk.CTkFrame(list_frame, fg_color="transparent", height=32)
        frame.pack(fill="x", padx=4, pady=(1, 1))
        frame.pack_propagate(False)

        label_text = _format_key_label(key)
        has_buffs = bool(get_buffs_for_key(store, key))

        btn = ctk.CTkButton(
            frame,
            text=label_text,
            font=app.small_font,
            fg_color="#1f538d" if has_buffs else "transparent",
            hover_color="#2b6fb0",
            anchor="w",
            command=lambda k=key: _select_key(window, app, k),
        )
        btn.pack(fill="both", expand=True)


def _select_key(window: ctk.Toplevel, app: DamageCalculatorApp, key: str) -> None:
    window._selected_key = key
    _refresh_right_panel(window, app)


def _build_left_panel(window: ctk.CTkToplevel, app: DamageCalculatorApp, store: dict) -> None:
    left = ctk.CTkFrame(window, fg_color="#1a1a2e")
    left.grid(row=0, column=0, sticky="nsew")
    left.grid_rowconfigure(0, weight=0)
    left.grid_rowconfigure(1, weight=1)
    left.grid_columnconfigure(0, weight=1)

    header = ctk.CTkFrame(left, fg_color="transparent")
    header.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
    ctk.CTkLabel(
        header,
        text="段 / 异常",
        font=app.big_font,
        text_color="#FF6B6B",
    ).pack(side="left")

    refresh_btn = ctk.CTkButton(
        header,
        text="刷新",
        width=50,
        font=app.small_font,
        command=lambda: _refresh_key_list(window, app),
    )
    refresh_btn.pack(side="right")

    list_frame = ctk.CTkScrollableFrame(left, fg_color="transparent")
    list_frame.grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 8))
    window._left_list_frame = list_frame


def _build_right_panel(window: ctk.CTkToplevel, app: DamageCalculatorApp, store: dict) -> None:
    right = ctk.CTkFrame(window, fg_color="#1e1e30")
    right.grid(row=0, column=1, sticky="nsew")
    right.grid_rowconfigure(0, weight=0)
    right.grid_rowconfigure(1, weight=1)
    right.grid_columnconfigure(0, weight=1)

    header = ctk.CTkFrame(right, fg_color="transparent")
    header.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
    ctk.CTkLabel(
        header,
        text="选择左侧项目进行编辑",
        font=app.big_font,
        text_color="#4ECDC4",
    ).pack(side="left")

    edit_area = ctk.CTkScrollableFrame(right, fg_color="transparent")
    edit_area.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
    window._right_edit_area = edit_area
    window._right_header_label = header.winfo_children()[0]


def _refresh_right_panel(window: ctk.Toplevel, app: DamageCalculatorApp) -> None:
    edit_area = getattr(window, "_right_edit_area", None)
    header_label = getattr(window, "_right_header_label", None)
    if edit_area is None:
        return

    for child in edit_area.winfo_children():
        child.destroy()

    key = getattr(window, "_selected_key", None)
    if not key:
        return

    store = getattr(app, "_manual_buff_store", {})
    entries = get_buffs_for_key(store, key)

    if header_label:
        header_label.configure(text=f"{_format_key_label(key)} 的乘区微调")

    row_data: list[dict[str, Any]] = [
        {"var": ctk.StringVar(value=e["effect_type"]), "val": ctk.StringVar(value=str(e["value"] * 100))}
        for e in entries
    ]

    def _rebuild_rows() -> None:
        for child in edit_area.winfo_children():
            child.destroy()
        row_data.clear()
        saved = get_buffs_for_key(store, key)
        for e in saved:
            row_data.append({
                "var": ctk.StringVar(value=e["effect_type"]),
                "val": ctk.StringVar(value=str(e["value"] * 100)),
            })
        _render_rows()

    def _add_row() -> None:
        rd = {"var": ctk.StringVar(value=MANUAL_BUFF_ZONE_OPTIONS[0][0]), "val": ctk.StringVar(value="0")}
        row_data.append(rd)
        _render_rows()
        _commit(store, key, row_data)

    def _commit(store_: dict, key_: str, rd: list[dict[str, Any]]) -> None:
        result: list[dict[str, float]] = []
        for item in rd:
            et = (item["var"].get() or "").strip()
            try:
                val = float(item["val"].get() or "0")
            except (TypeError, ValueError):
                val = 0.0
            if et and val != 0:
                result.append({"effect_type": et, "value": val / 100.0})
        set_buffs_for_key(store_, key_, result)
        _refresh_key_list(window, app)

    def _render_rows() -> None:
        for child in edit_area.winfo_children():
            child.destroy()

        for idx, rd in enumerate(row_data):
            row = ctk.CTkFrame(edit_area, fg_color="transparent", height=_BUFF_ROW_HEIGHT)
            row.pack(fill="x", pady=(2, 2))
            row.pack_propagate(False)

            menu = ctk.CTkOptionMenu(
                row,
                values=[label for label, _ in MANUAL_BUFF_ZONE_OPTIONS],
                variable=rd["var"],
                font=app.small_font,
                width=140,
            )
            menu.pack(side="left", padx=(0, 6))

            ctk.CTkLabel(row, text="+", font=app.small_font, text_color="#CCCCCC").pack(side="left")

            entry = ctk.CTkEntry(
                row,
                textvariable=rd["val"],
                font=app.small_font,
                width=60,
            )
            entry.pack(side="left", padx=(4, 4))

            ctk.CTkLabel(row, text="%", font=app.small_font, text_color="#CCCCCC").pack(side="left")

            del_btn = ctk.CTkButton(
                row,
                text="×",
                width=28,
                font=app.small_font,
                fg_color="#8B0000",
                hover_color="#FF0000",
                command=lambda i=idx: (_delete_row(i), _commit(store, key, row_data)),
            )
            del_btn.pack(side="right", padx=(8, 0))

            entry.bind("<FocusOut>", lambda _e, s=store, k=key, rd=row_data: _commit(s, k, rd))
            entry.bind("<Return>", lambda _e, s=store, k=key, rd=row_data: _commit(s, k, rd))
            menu.configure(command=lambda _v, s=store, k=key, rd=row_data: _commit(s, k, rd))

        add_row = ctk.CTkButton(
            edit_area,
            text="+ 添加乘区",
            font=app.small_font,
            fg_color="#2d6a4f",
            hover_color="#40916c",
            command=_add_row,
        )
        add_row.pack(fill="x", pady=(8, 0))

    def _delete_row(idx: int) -> None:
        if 0 <= idx < len(row_data):
            row_data.pop(idx)

    _render_rows()
