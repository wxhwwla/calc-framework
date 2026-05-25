#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""增强功能 UI：预设导入导出、日志、历史、可视化仪表盘、启动页策略。"""

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


def _label_for_mode(mode_id: str) -> str:
    for label, mid in CALC_MODE_OPTIONS:
        if mid == mode_id:
            return label
    return mode_id


def _lists_for_preset_compare(app: "DamageCalculatorApp") -> tuple[list, list, list]:
    """多方案对比用的角色/武器/装备列表（优先 app.game_data）。"""
    game_data = getattr(app, "game_data", None)
    if isinstance(game_data, GameDataFacade):
        return (
            game_data.characters,
            game_data.weapons,
            game_data.equipment_rows,
        )
    return get_characters(), get_weapons(), get_equipments()


def build_preset_from_app(app: "DamageCalculatorApp") -> LoadoutPreset:
    """从当前 GUI 状态组装可导出预设。"""
    from gui_design.loadout_state import read_loadout_from_app

    state = read_loadout_from_app(app)
    if state is None:
        raise ValueError("请先选择有效角色和武器")
    preset = state.to_loadout_preset()
    char_var = getattr(getattr(app, "char_panel", None), "_show_advanced_params_var", None)
    weapon_var = getattr(getattr(app, "weapon_panel", None), "_show_advanced_params_var", None)
    more_var = getattr(app, "_show_more_settings_var", None)
    ui_state = {
        "char_advanced_expanded": bool(char_var.get()) if char_var is not None else False,
        "weapon_advanced_expanded": bool(weapon_var.get()) if weapon_var is not None else False,
        "more_settings_expanded": bool(more_var.get()) if more_var is not None else False,
        "current_page": str(app.page_tabs.get()) if getattr(app, "page_tabs", None) is not None else "计算页",
    }
    return LoadoutPreset(
        char_name=preset.char_name,
        weapon_name=preset.weapon_name,
        char_level=preset.char_level,
        weapon_level=preset.weapon_level,
        trust_level=preset.trust_level,
        skill_levels=preset.skill_levels,
        calculation_mode=preset.calculation_mode,
        weapon_scope=preset.weapon_scope,
        equipment_scope=preset.equipment_scope,
        fixed_equipment_names=preset.fixed_equipment_names,
        multi_skill_counts=preset.multi_skill_counts,
        use_manual_multi_skill_counts=preset.use_manual_multi_skill_counts,
        physical_abnormal_counts=preset.physical_abnormal_counts,
        spell_abnormal_counts=preset.spell_abnormal_counts,
        damage_component_mode=preset.damage_component_mode,
        use_expected_crit=preset.use_expected_crit,
        include_conditional_equipment_crit=preset.include_conditional_equipment_crit,
        extra_crit_rate=preset.extra_crit_rate,
        extra_crit_damage=preset.extra_crit_damage,
        ui_state=ui_state,
        note=preset.note,
    )


def _refresh_more_settings_visibility(app: "DamageCalculatorApp") -> None:
    """按 app._show_more_settings_var 刷新「更多设置」折叠区显隐。"""
    toggle_btn = getattr(app, "_more_settings_toggle_btn", None)
    body = getattr(app, "_more_settings_body", None)
    var = getattr(app, "_show_more_settings_var", None)
    expanded = bool(var.get()) if var is not None else False
    if toggle_btn is not None:
        toggle_btn.configure(text="更多设置（收起）" if expanded else "更多设置（展开）")
    if body is not None:
        if expanded:
            body.grid()
        else:
            body.grid_remove()


def _select_panel_by_name(panel, name: str) -> bool:
    if not name or not panel.list_c_w:
        return False
    match = next((row for row in panel.list_c_w if row.get("名称") == name), None)
    if not match:
        return False
    panel.selected_type.set(str(match.get("类型", "")))
    panel.selected_star.set(str(match.get("星级", "")))
    panel.selected_name.set(name)
    return True


def apply_preset_to_app(app: "DamageCalculatorApp", preset: LoadoutPreset) -> None:
    """将预设写回 GUI（名称须存在于当前数据列表）。"""
    if not _select_panel_by_name(app.char_panel, preset.char_name):
        raise ValueError(f"未找到角色: {preset.char_name}")
    app._on_char_name_change()
    if not _select_panel_by_name(app.weapon_panel, preset.weapon_name):
        raise ValueError(f"未找到武器: {preset.weapon_name}")
    app.char_panel.selected_level.set(str(preset.char_level))
    app.weapon_panel.selected_level.set(str(preset.weapon_level))
    if app.char_panel.trust_panel:
        app.char_panel.trust_panel.trust_level.set(str(preset.trust_level))
    if app.char_panel.skill_level_panel:
        s = app.char_panel.skill_level_panel
        s.skill_1_level.set(str(preset.skill_levels[0]))
        s.skill_2_level.set(str(preset.skill_levels[1]))
        s.skill_3_level.set(str(preset.skill_levels[2]))
    app.calc_mode_var.set(_label_for_mode(preset.calculation_mode))
    app.single_skill_scope_var.set(preset.weapon_scope)
    app.single_skill_equipment_scope_var.set(preset.equipment_scope)
    app.use_manual_skill_counts_var.set(preset.use_manual_multi_skill_counts)
    from gui_design.multi_skill_controls import (
        apply_physical_abnormal_counts_to_app,
        apply_spell_abnormal_counts_to_app,
        apply_segment_counts_to_app,
    )

    apply_segment_counts_to_app(app, preset.multi_skill_counts)
    apply_physical_abnormal_counts_to_app(app, preset.physical_abnormal_counts)
    apply_spell_abnormal_counts_to_app(app, getattr(preset, "spell_abnormal_counts", {}))
    if hasattr(app, "damage_component_mode_var"):
        if preset.damage_component_mode == "skill_only":
            app.damage_component_mode_var.set("仅技能")
        elif preset.damage_component_mode == "abnormal_only":
            app.damage_component_mode_var.set("仅异常")
        else:
            app.damage_component_mode_var.set("技能+异常")
    if hasattr(app, "use_expected_crit_var"):
        app.use_expected_crit_var.set(bool(preset.use_expected_crit))
    if hasattr(app, "include_conditional_equipment_crit_var"):
        app.include_conditional_equipment_crit_var.set(
            bool(preset.include_conditional_equipment_crit)
        )
    if hasattr(app, "extra_crit_rate_percent_var"):
        app.extra_crit_rate_percent_var.set(str(float(preset.extra_crit_rate) * 100.0))
    if hasattr(app, "extra_crit_damage_percent_var"):
        app.extra_crit_damage_percent_var.set(str(float(preset.extra_crit_damage) * 100.0))
    ui_state = preset.ui_state or {}
    char_panel = getattr(app, "char_panel", None)
    if char_panel is not None and hasattr(char_panel, "_show_advanced_params_var"):
        char_panel._show_advanced_params_var.set(bool(ui_state.get("char_advanced_expanded", False)))
        if hasattr(char_panel, "_refresh_advanced_params_visibility"):
            char_panel._refresh_advanced_params_visibility()
    weapon_panel = getattr(app, "weapon_panel", None)
    if weapon_panel is not None and hasattr(weapon_panel, "_show_advanced_params_var"):
        weapon_panel._show_advanced_params_var.set(bool(ui_state.get("weapon_advanced_expanded", False)))
        if hasattr(weapon_panel, "_refresh_advanced_params_visibility"):
            weapon_panel._refresh_advanced_params_visibility()
    if hasattr(app, "_show_more_settings_var"):
        app._show_more_settings_var.set(bool(ui_state.get("more_settings_expanded", False)))
        _refresh_more_settings_visibility(app)
    if getattr(app, "page_tabs", None) is not None:
        target_page = str(ui_state.get("current_page", "计算页"))
        if target_page in ("计算页", "高级页"):
            if hasattr(app, "_set_current_page"):
                app._set_current_page(target_page)
            else:
                app.page_tabs.set(target_page)
    app._refresh_fixed_loadout_menus()
    app._schedule_confirm(force=True)


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
            app._schedule_confirm(force=True)

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


def get_app_calculation_history(app: "DamageCalculatorApp") -> CalculationHistory:
    history = getattr(app, "_calc_history", None)
    if history is None:
        history = CalculationHistory(max_entries=10)
        app._calc_history = history
    return history


def record_calculation_history(app: "DamageCalculatorApp", *, summary: str) -> None:
    """确认选择后记录一条历史。"""
    preset = build_preset_from_app(app)
    label = f"{preset.char_name} / {preset.weapon_name}"
    get_app_calculation_history(app).push(
        HistoryEntry(
            label=label,
            summary=summary,
            preset_snapshot=preset.to_dict(),
        )
    )


def show_calculation_history_dialog(app: "DamageCalculatorApp") -> None:
    dialog = ctk.CTkToplevel(app.app)
    dialog.title("计算历史（最近10次）")
    dialog.geometry("520x420")
    dialog.transient(app.app)
    scroll = ctk.CTkScrollableFrame(dialog)
    scroll.pack(fill="both", expand=True, padx=12, pady=12)
    entries = get_app_calculation_history(app).list_entries()
    if not entries:
        ctk.CTkLabel(scroll, text="暂无历史记录", font=app.small_font).pack(anchor="w")
        return

    for idx, entry in enumerate(entries):

        def _restore(i: int = idx) -> None:
            snap = get_app_calculation_history(app).get_snapshot(i)
            if not snap:
                return
            try:
                apply_preset_to_app(app, LoadoutPreset.from_dict(snap))
                dialog.destroy()
            except Exception as exc:
                messagebox.showerror("恢复失败", str(exc), parent=dialog)

        frame = ctk.CTkFrame(scroll, fg_color="#2a2a2a")
        frame.pack(fill="x", pady=4)
        ctk.CTkLabel(
            frame,
            text=f"{entry.label}\n{entry.summary}",
            font=app.small_font,
            justify="left",
        ).pack(anchor="w", padx=8, pady=(6, 0))
        ctk.CTkButton(
            frame, text="恢复此配置", font=app.small_font, width=120, command=_restore
        ).pack(anchor="e", padx=8, pady=6)


def refresh_damage_snapshot(
    app: "DamageCalculatorApp",
    *,
    loadout: Optional["LoadoutState"] = None,
) -> None:
    """根据 LoadoutState 重建伤害快照（确认后调用）。"""
    from gui_design.loadout_evaluation import build_snapshot_from_loadout
    from gui_design.loadout_state import LoadoutState, read_loadout_from_app

    if loadout is None:
        loadout = read_loadout_from_app(app)
    if loadout is None:
        return
    store_snapshot_on_app(app, build_snapshot_from_loadout(loadout))


def show_preset_compare_dialog(app: "DamageCalculatorApp") -> None:
    """选择多个预设 JSON，并行评估并展示排名。"""
    paths = filedialog.askopenfilenames(
        parent=app.app,
        title="多方案对比 — 选择一个或多个配装预设 JSON",
        filetypes=[("JSON", "*.json")],
    )
    if not paths:
        return

    presets: list[LoadoutPreset] = []
    try:
        for path in paths:
            presets.extend(import_presets_from_json_text(Path(path).read_text(encoding="utf-8")))
        presets.insert(0, build_preset_from_app(app))
    except Exception as exc:
        messagebox.showerror("读取预设失败", str(exc), parent=app.app)
        return

    if len(presets) < 2:
        messagebox.showinfo(
            "需要至少 2 条方案",
            "已自动包含当前配置；请再选一个或多个预设 JSON 文件。",
            parent=app.app,
        )
        return

    workers_var = getattr(app, "search_workers_var", None)
    worker_label = workers_var.get() if workers_var is not None else "1"
    max_workers = resolve_parallel_workers(worker_label)

    characters, weapons, equipments = _lists_for_preset_compare(app)
    rows = compare_presets_parallel(
        presets,
        characters=characters,
        weapons=weapons,
        equipments=equipments,
        enemy_defense=float(getattr(app, "_enemy_defense", 100.0)),
        max_workers=max_workers,
    )
    get_session_operation_log().record(
        LogLevel.USER,
        "preset_compare",
        {"count": len(presets), "workers": max_workers},
    )

    dialog = ctk.CTkToplevel(app.app)
    dialog.title("多方案对比结果")
    dialog.geometry("640x480")
    dialog.transient(app.app)
    scroll = ctk.CTkScrollableFrame(dialog)
    scroll.pack(fill="both", expand=True, padx=12, pady=12)

    ctk.CTkLabel(
        scroll,
        text=f"共 {len(presets)} 条方案（含当前配置），并行线程≈{max_workers}",
        font=app.small_font,
        text_color="#CCCCCC",
    ).pack(anchor="w", pady=(0, 8))

    for idx, row in enumerate(rows, start=1):
        if row.error:
            body = f"#{idx} {row.label}\n错误: {row.error}"
            color = "#FF6B6B"
        else:
            body = f"#{idx} {row.label}\n伤害: {row.final_damage:.1f}\n{row.loadout_summary}"
            color = "#B8B8B8"
        ctk.CTkLabel(scroll, text=body, font=app.small_font, text_color=color, justify="left").pack(
            anchor="w", pady=4
        )


def show_damage_dashboard_dialog(app: "DamageCalculatorApp") -> None:
    if not is_matplotlib_available():
        messagebox.showwarning(
            "需要 matplotlib",
            f"请安装:\n{matplotlib_install_hint()}",
            parent=app.app,
        )
        return
    snap = get_snapshot_from_app(app)
    if snap is None:
        refresh_damage_snapshot(app)
        snap = get_snapshot_from_app(app)
    if snap is None:
        messagebox.showinfo(
            "暂无数据",
            "请先选择角色与武器并点击「确认选择」。",
            parent=app.app,
        )
        return
    from calculation.skill_segments import segment_display_label

    rotation_damage = dict(snap.segment_totals)
    pie_slices = damage_breakdown_from_skill_map(
        {
            segment_display_label(key): value
            for key, value in rotation_damage.items()
            if value > 0
        }
    )
    fig = build_damage_pie_figure(pie_slices, title="轮转伤害构成")
    zone_items = tuple(
        sorted(snap.zone_share_percent.items(), key=lambda item: -item[1])
    )
    bar_fig = build_improvement_bar_figure(
        zone_items,
        title="乘区构成占比",
        ylabel="占比 %",
    )
    try:
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        import matplotlib.pyplot as plt

        dialog = ctk.CTkToplevel(app.app)
        dialog.title("伤害仪表盘")
        dialog.geometry("960x480")
        dialog.transient(app.app)
        canvas1 = FigureCanvasTkAgg(fig, master=dialog)
        canvas1.get_tk_widget().pack(side="left", fill="both", expand=True)
        canvas2 = FigureCanvasTkAgg(bar_fig, master=dialog)
        canvas2.get_tk_widget().pack(side="right", fill="both", expand=True)

        def _on_close() -> None:
            plt.close(fig)
            plt.close(bar_fig)
            dialog.destroy()

        dialog.protocol("WM_DELETE_WINDOW", _on_close)
    except Exception as exc:
        messagebox.showerror("图表失败", str(exc), parent=app.app)
