#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""配装待确认状态：滑块/选项改动后仅更新按钮，三列等用户点「确认选择」。"""

from __future__ import annotations

from typing import TYPE_CHECKING

import customtkinter as ctk

from .loadout_state import read_loadout_from_app

if TYPE_CHECKING:
    from gui_design.shell.app import DamageCalculatorApp

CONFIRM_BTN_TEXT_DEFAULT = "确认选择"
CONFIRM_BTN_TEXT_PENDING = "确认选择（待更新）"
_PENDING_BUTTON_FG = "#7C3AED"
_PENDING_BUTTON_HOVER = "#6D28D9"


def display_pending_signature_now(app: "DamageCalculatorApp") -> tuple:
    """读取当前面板对应的展示签名。"""
    state = read_loadout_from_app(app, ensure_segment_rows=False)
    if state is None:
        return ()
    return state.display_pending_signature()


def is_loadout_pending_confirm(app: "DamageCalculatorApp") -> bool:
    """当前面板展示签名是否与上次确认不一致。"""
    confirmed = getattr(app, "_confirmed_display_signature", None)
    if confirmed is None:
        return False
    return display_pending_signature_now(app) != confirmed


def capture_confirmed_display_signature(app: "DamageCalculatorApp") -> None:
    """确认刷新成功后记录展示签名并清除待确认样式。"""
    app._confirmed_display_signature = display_pending_signature_now(app)
    sync_confirm_button_pending_state(app)


def _ensure_button_style_cache(app: "DamageCalculatorApp", button: ctk.CTkButton) -> None:
    """首次使用时缓存按钮默认配色，便于待确认后恢复。"""
    cache: dict[int, tuple] = getattr(app, "_confirm_button_default_styles", {})
    key = id(button)
    if key not in cache:
        cache[key] = (button.cget("fg_color"), button.cget("hover_color"))
        app._confirm_button_default_styles = cache


def _apply_button_pending_style(button: ctk.CTkButton, *, pending: bool) -> None:
    if pending:
        button.configure(
            text=CONFIRM_BTN_TEXT_PENDING,
            fg_color=_PENDING_BUTTON_FG,
            hover_color=_PENDING_BUTTON_HOVER,
        )
        return
    button.configure(text=CONFIRM_BTN_TEXT_DEFAULT)


def sync_confirm_button_pending_state(app: "DamageCalculatorApp") -> None:
    """同步计算页与高级页两个确认按钮的待确认样式。"""
    pending = is_loadout_pending_confirm(app)
    for attr in ("main_confirm_btn", "confirm_btn"):
        button = getattr(app, attr, None)
        if button is None:
            continue
        _ensure_button_style_cache(app, button)
        default_fg, default_hover = app._confirm_button_default_styles[id(button)]
        _apply_button_pending_style(button, pending=pending)
        if not pending:
            button.configure(fg_color=default_fg, hover_color=default_hover)


def mark_loadout_pending(app: "DamageCalculatorApp") -> None:
    """配装数值/选项变更：不刷新三列，仅合并 idle 后更新按钮待确认态。"""
    if getattr(app, "_pending_ui_after_id", None) is not None:
        return

    def _dispatch() -> None:
        app._pending_ui_after_id = None
        sync_confirm_button_pending_state(app)

    app._pending_ui_after_id = app.app.after_idle(_dispatch)
