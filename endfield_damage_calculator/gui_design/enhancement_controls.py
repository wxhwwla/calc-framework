#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""增强功能 UI：预设导入导出、日志、历史、可视化仪表盘。"""

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
    return state.to_loadout_preset()


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
    app.skill_count_1_var.set(str(preset.multi_skill_counts.get("战技", 0)))
    app.skill_count_2_var.set(str(preset.multi_skill_counts.get("连携技", 0)))
    app.skill_count_3_var.set(str(preset.multi_skill_counts.get("终结技", 0)))
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

        row = place_fn(
            parent,
            row,
            ctk.CTkLabel(parent, text="插件敌人", font=app.small_font, text_color="#CCCCCC"),
            pady=(0, 2),
        )
        menu = ctk.CTkOptionMenu(
            parent,
            values=labels,
            variable=app._plugin_enemy_var,
            font=app.small_font,
            command=_on_enemy_change,
        )
        row = place_fn(parent, row, menu, pady=(0, 4))
        app._plugin_enemy_id = id_by_label.get(app._plugin_enemy_var.get(), "")
        app._enemy_defense = resolve_enemy_defense(app._plugin_enemy_id)
    else:
        app._plugin_enemy_id = ""
        app._enemy_defense = resolve_enemy_defense("")

    for text, cmd in (
        ("导出配装(.json)", _export_preset),
        ("导入配装(.json)", _import_preset),
        ("多方案对比", _compare_presets),
        ("导出操作日志", _export_log),
        ("计算历史", _show_history),
        ("伤害仪表盘", _show_charts),
    ):
        btn = ctk.CTkButton(parent, text=text, font=app.small_font, command=cmd)
        row = place_fn(parent, row, btn, pady=(0, 4))
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
    rotation_damage = {
        name: snap.skill_damage.get(name, 0.0) * snap.skill_counts.get(name, 0)
        for name in snap.skill_damage
        if snap.skill_counts.get(name, 0) > 0
    }
    pie_slices = damage_breakdown_from_skill_map(rotation_damage)
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
