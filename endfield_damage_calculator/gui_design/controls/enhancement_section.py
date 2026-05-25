#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""工具与分享折叠区布局。"""

from __future__ import annotations

from pathlib import Path
from tkinter import filedialog, messagebox
from typing import TYPE_CHECKING, Any, Callable, Optional

from utils.platform_win32_patch import apply_platform_win32_patch

apply_platform_win32_patch()
import customtkinter as ctk

from gui_design.calc_history import CalculationHistory, HistoryEntry
from gui_design.calc_mode_labels import CALC_MODE_OPTIONS
from gui_design.damage_snapshot import get_snapshot_from_app, store_snapshot_on_app
from gui_design.damage_visualization import (
    build_damage_pie_figure,
    build_improvement_bar_figure,
    damage_breakdown_from_skill_map,
    is_matplotlib_available,
)
from utils.optional_deps import matplotlib_install_hint
from data.enemy_params import list_plugin_enemy_choices, resolve_enemy_defense
from gui_design.loadout_preset import (
    LoadoutPreset,
    export_preset_json,
    import_preset_json,
    import_presets_from_json_text,
)
from gui_design.preset_batch_compare import compare_presets_parallel
from data.game_data_facade import GameDataFacade
from data.loader import get_characters, get_equipments, get_weapons
from gui_design.search_settings import resolve_parallel_workers
from gui_design.gui_layout import (
    MORE_SETTINGS_VIEWPORT_HEIGHT,
    SECONDARY_ACTION_BUTTON_HEIGHT,
)
from gui_design.ui_preferences import (
    STARTUP_MODE_ALWAYS_MAIN,
    STARTUP_MODE_REMEMBER_LAST,
    save_ui_preferences,
)
from utils.gui_fonts import default_ui_font
from utils.operation_log import LogLevel, get_session_operation_log

if TYPE_CHECKING:
    from gui_design.gui import DamageCalculatorApp
    from gui_design.loadout_state import LoadoutState

from .enhancement_preset import (
    apply_preset_to_app,
    build_preset_from_app,
    _refresh_more_settings_visibility,
)

def place_enhancement_section(
    app: "DamageCalculatorApp",
    parent: ctk.CTkFrame,
    *,
    start_row: int,
    place_fn: Callable[..., int],
) -> int:
    """在操作列追加增强功能按钮，返回下一可用 row。"""
    row = start_row
    row = place_fn(
        parent,
        row,
        ctk.CTkLabel(parent, text="工具与分享", font=app.small_font, text_color="#FF6B6B"),
        pady=(8, 2),
    )

    if not hasattr(app, "_show_more_settings_var"):
        app._show_more_settings_var = ctk.BooleanVar(value=False)

    app._more_settings_toggle_btn = ctk.CTkButton(
        parent,
        text="更多设置（展开）",
        font=app.small_font,
        command=lambda: (
            app._show_more_settings_var.set(not bool(app._show_more_settings_var.get())),
            _refresh_more_settings_visibility(app),
        ),
    )
    row = place_fn(parent, row, app._more_settings_toggle_btn, pady=(0, 4))

    app._more_settings_viewport = ctk.CTkFrame(
        parent,
        height=MORE_SETTINGS_VIEWPORT_HEIGHT,
        fg_color="transparent",
    )
    app._more_settings_viewport.grid(row=row, column=0, padx=4, pady=(0, 2), sticky="ew")
    app._more_settings_viewport.grid_propagate(False)
    app._more_settings_viewport.grid_columnconfigure(0, weight=1)
    app._more_settings_viewport.grid_rowconfigure(0, weight=1)
    app._more_settings_body = ctk.CTkFrame(app._more_settings_viewport, fg_color="transparent")
    app._more_settings_body.grid(row=0, column=0, sticky="ew")
    app._more_settings_body.grid_columnconfigure(0, weight=1)
    row += 1

    body_row = 0

    def _place_body(widget, *, pady: tuple[int, int] = (0, 4)) -> None:
        nonlocal body_row
        widget.grid(row=body_row, column=0, padx=0, pady=pady, sticky="ew")
        body_row += 1

    def _export_preset() -> None:
        path = filedialog.asksaveasfilename(
            parent=app.app,
            title="导出配装预设",
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
        )
        if not path:
            return
        preset = build_preset_from_app(app)
        Path(path).write_text(export_preset_json(preset), encoding="utf-8")
        get_session_operation_log().record(LogLevel.USER, "export_preset", {"path": path})
        messagebox.showinfo("导出成功", f"已保存:\n{path}", parent=app.app)

    def _import_preset() -> None:
        path = filedialog.askopenfilename(
            parent=app.app,
            title="导入配装预设",
            filetypes=[("JSON", "*.json")],
        )
        if not path:
            return
        try:
            preset = import_preset_json(Path(path).read_text(encoding="utf-8"))
            apply_preset_to_app(app, preset)
            get_session_operation_log().record(LogLevel.USER, "import_preset", {"path": path})
            messagebox.showinfo("导入成功", "已恢复预设参数，请核对固定配装装备名。", parent=app.app)
        except Exception as exc:
            messagebox.showerror("导入失败", str(exc), parent=app.app)

    def _export_log() -> None:
        path = filedialog.asksaveasfilename(
            parent=app.app,
            title="导出操作日志",
            defaultextension=".json",
            initialfile="operation_log.json",
            filetypes=[("JSON", "*.json")],
        )
        if not path:
            return
        get_session_operation_log().export_to_file(Path(path))
        messagebox.showinfo("日志已导出", path, parent=app.app)

    def _show_history() -> None:
        show_calculation_history_dialog(app)

    def _show_charts() -> None:
        show_damage_dashboard_dialog(app)

    def _compare_presets() -> None:
        show_preset_compare_dialog(app)

    enemy_choices = list_plugin_enemy_choices()
    if len(enemy_choices) > 1:
        if not hasattr(app, "_plugin_enemy_var"):
            app._plugin_enemy_var = ctk.StringVar(value=enemy_choices[0][0])
        labels = [c[0] for c in enemy_choices]
        id_by_label = {c[0]: c[1] for c in enemy_choices}

        def _on_enemy_change(choice: str) -> None:
            enemy_id = id_by_label.get(choice, "")
            app._plugin_enemy_id = enemy_id
            app._enemy_defense = resolve_enemy_defense(enemy_id)
            app._mark_loadout_pending()

        _place_body(
            ctk.CTkLabel(
                app._more_settings_body,
                text="插件敌人",
                font=app.small_font,
                text_color="#CCCCCC",
            ),
            pady=(0, 2),
        )
        menu = ctk.CTkOptionMenu(
            app._more_settings_body,
            values=labels,
            variable=app._plugin_enemy_var,
            font=app.small_font,
            command=_on_enemy_change,
        )
        _place_body(menu, pady=(0, 4))
        app._plugin_enemy_id = id_by_label.get(app._plugin_enemy_var.get(), "")
        app._enemy_defense = resolve_enemy_defense(app._plugin_enemy_id)
    else:
        app._plugin_enemy_id = ""
        app._enemy_defense = resolve_enemy_defense("")

    grouped_actions = (
        ("导入导出", (("导出配装(.json)", _export_preset), ("导入配装(.json)", _import_preset))),
        ("分析工具", (("多方案对比", _compare_presets), ("伤害仪表盘", _show_charts))),
        ("维护工具", (("导出操作日志", _export_log), ("计算历史", _show_history))),
    )
    for title, actions in grouped_actions:
        _place_body(
            ctk.CTkLabel(
                app._more_settings_body,
                text=title,
                font=app.small_font,
                text_color="#CCCCCC",
            ),
            pady=(4, 2),
        )
        for text, cmd in actions:
            btn = ctk.CTkButton(
                app._more_settings_body,
                text=text,
                font=app.small_font,
                height=SECONDARY_ACTION_BUTTON_HEIGHT,
                command=cmd,
            )
            _place_body(btn, pady=(0, 4))

    mode_label_to_value = {
        "启动总是计算页": STARTUP_MODE_ALWAYS_MAIN,
        "启动记住上次页面": STARTUP_MODE_REMEMBER_LAST,
    }
    mode_value_to_label = {value: label for label, value in mode_label_to_value.items()}
    preferences = getattr(app, "_ui_preferences", {}) or {}
    current_mode = str(preferences.get("startup_page_mode", STARTUP_MODE_ALWAYS_MAIN))
    current_label = mode_value_to_label.get(current_mode, "启动总是计算页")
    if not hasattr(app, "_startup_page_mode_var"):
        app._startup_page_mode_var = ctk.StringVar(value=current_label)
    else:
        app._startup_page_mode_var.set(current_label)

    def _on_startup_page_mode_change(label: str) -> None:
        mode = mode_label_to_value.get(str(label), STARTUP_MODE_ALWAYS_MAIN)
        app._ui_preferences = dict(getattr(app, "_ui_preferences", {}) or {})
        app._ui_preferences["startup_page_mode"] = mode
        save_ui_preferences(app._ui_preferences)

    app._on_startup_page_mode_change = _on_startup_page_mode_change
    _place_body(
        ctk.CTkLabel(
            app._more_settings_body,
            text="启动页面策略",
            font=app.small_font,
            text_color="#CCCCCC",
        ),
        pady=(4, 2),
    )
    app._startup_page_mode_menu = ctk.CTkOptionMenu(
        app._more_settings_body,
        values=list(mode_label_to_value.keys()),
        variable=app._startup_page_mode_var,
        font=app.small_font,
        command=_on_startup_page_mode_change,
    )
    _place_body(app._startup_page_mode_menu, pady=(0, 4))
    app._startup_page_mode_hint_label = ctk.CTkLabel(
        app._more_settings_body,
        text="仅影响下次启动，当前页面不会立刻切换",
        font=app.small_font,
        text_color="#888888",
        justify="left",
        anchor="w",
    )
    _place_body(app._startup_page_mode_hint_label, pady=(0, 4))

    _refresh_more_settings_visibility(app)
    return row


