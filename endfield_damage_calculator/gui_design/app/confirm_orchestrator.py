#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""确认刷新编排：签名去重、idle 合并、乘区/快照/历史副作用。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .display_request import build_display_request
from .loadout_state import read_loadout_from_app
from gui_design.search_controls import refresh_search_estimate
from utils.operation_log import LogLevel, get_session_operation_log

if TYPE_CHECKING:
    from gui_design.gui import DamageCalculatorApp

# 窗口从最小化/隐藏恢复后，等待布局稳定再重排或确认刷新（毫秒）
WINDOW_RESTORE_SETTLE_MS = 80


def is_window_iconified(app: "DamageCalculatorApp") -> bool:
    try:
        return str(app.app.state()) == "iconic"
    except Exception:
        return False


def confirm_signature_now(app: "DamageCalculatorApp") -> tuple:
    state = read_loadout_from_app(app)
    if state is None:
        return ()
    return state.confirm_refresh_signature()


def is_restore_settling(app: "DamageCalculatorApp") -> bool:
    """窗口刚恢复显示，布局尚未稳定。"""
    return bool(getattr(app, "_restore_settling", False))


def handle_confirm(app: "DamageCalculatorApp", *, force: bool = False) -> None:
    """合并去重后执行一次确认刷新。"""
    if not force and getattr(app, "_suppress_full_confirm_refresh", False):
        return
    if force:
        get_session_operation_log().record(
            LogLevel.USER,
            "confirm_selection",
            {"mode": app._current_calculation_mode()},
        )
    if not force and is_window_iconified(app):
        return
    if not force and is_restore_settling(app):
        schedule_confirm(app)
        return
    signature = confirm_signature_now(app)
    if not force and signature == app._confirm_refresh_signature:
        return
    app._confirm_refresh_signature = signature
    if not force:
        get_session_operation_log().record(
            LogLevel.USER,
            "confirm_selection",
            {"mode": app._current_calculation_mode()},
        )
    run_confirm_refresh(app)


def schedule_confirm(app: "DamageCalculatorApp", *, force: bool = False) -> None:
    """将确认刷新合并到下一 idle。"""
    if not force and getattr(app, "_suppress_full_confirm_refresh", False):
        return
    if force:
        if app._confirm_after_id is not None:
            try:
                app.app.after_cancel(app._confirm_after_id)
            except Exception:
                pass
            app._confirm_after_id = None
        handle_confirm(app, force=True)
        return
    if app._confirm_after_id is not None:
        return

    def _dispatch() -> None:
        app._confirm_after_id = None
        if is_window_iconified(app):
            app._confirm_after_id = app.app.after(WINDOW_RESTORE_SETTLE_MS, _dispatch)
            return
        if is_restore_settling(app):
            app._confirm_after_id = app.app.after(WINDOW_RESTORE_SETTLE_MS, _dispatch)
            return
        handle_confirm(app, force=False)

    app._confirm_after_id = app.app.after_idle(_dispatch)


def run_confirm_refresh(app: "DamageCalculatorApp") -> None:
    """执行属性列、右侧乘区、快照与搜索预估刷新。"""
    from gui_design.display_view import confirm_from_display_request
    from gui_design.enhancement_controls import (
        record_calculation_history,
        refresh_damage_snapshot,
    )

    assert app.char_attr_scroll is not None
    assert app.weapon_attr_scroll is not None
    assert app.right_scroll is not None

    loadout = read_loadout_from_app(app)
    if loadout is None:
        return

    request = build_display_request(
        loadout,
        app.game_data,
        preview_weapon_candidates=app._single_skill_preview_candidates(),
    )
    confirm_from_display_request(
        app.char_attr_scroll,
        app.weapon_attr_scroll,
        app.right_scroll,
        request,
        big_font=app.big_font,
        small_font=app.small_font,
    )
    refresh_damage_snapshot(app, loadout=loadout)
    refresh_search_estimate(app)
    record_calculation_history(
        app,
        summary=f"模式 {app._current_calculation_mode_label()}",
    )
    from .loadout_pending import capture_confirmed_display_signature

    capture_confirmed_display_signature(app)
