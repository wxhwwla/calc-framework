#!/usr/bin/env python3
"""历史/对比/仪表盘弹窗。"""

from __future__ import annotations

from pathlib import Path
from tkinter import filedialog, messagebox
from typing import TYPE_CHECKING

from utils.platform_win32_patch import apply_platform_win32_patch

apply_platform_win32_patch()
import customtkinter as ctk

from gui_design.app.loadout_preset import (
    LoadoutPreset,
    import_presets_from_json_text,
)
from gui_design.presentation.damage_snapshot import get_snapshot_from_app, store_snapshot_on_app
from gui_design.search_ui.search_settings import resolve_parallel_workers
from gui_design.shared.calc_history import CalculationHistory, HistoryEntry
from gui_design.shared.damage_visualization import (
    build_damage_pie_figure,
    build_improvement_bar_figure,
    damage_breakdown_from_skill_map,
    is_matplotlib_available,
)
from gui_design.shared.preset_batch_compare import compare_presets_parallel
from utils.operation_log import LogLevel, get_session_operation_log
from utils.optional_deps import matplotlib_install_hint

if TYPE_CHECKING:
    from typing import Any

    from gui_design.app.loadout_state import LoadoutState
    from gui_design.shell.app import DamageCalculatorApp

from .preset import (
    _lists_for_preset_compare,
    apply_preset_to_app,
    build_preset_from_app,
)


def get_app_calculation_history(app: Any) -> CalculationHistory:
    history = getattr(app, "_calc_history", None)
    if history is None:
        history = CalculationHistory(max_entries=10)
        app._calc_history = history
    return history


def record_calculation_history(app: DamageCalculatorApp, *, summary: str) -> None:
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


def show_calculation_history_dialog(app: DamageCalculatorApp) -> None:
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
        ctk.CTkButton(frame, text="恢复此配置", font=app.small_font, width=120, command=_restore).pack(
            anchor="e", padx=8, pady=6
        )


def refresh_damage_snapshot(
    app: Any,
    *,
    loadout: LoadoutState | None = None,
) -> None:
    """根据 LoadoutState 重建伤害快照（确认后调用）。"""
    from gui_design.app.loadout_evaluation import build_snapshot_from_loadout
    from gui_design.app.loadout_state import read_loadout_from_app

    if loadout is None:
        loadout = read_loadout_from_app(app)
    if loadout is None:
        return
    store_snapshot_on_app(app, build_snapshot_from_loadout(loadout))


def show_preset_compare_dialog(app: DamageCalculatorApp) -> None:
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
        ctk.CTkLabel(scroll, text=body, font=app.small_font, text_color=color, justify="left").pack(anchor="w", pady=4)


def show_damage_dashboard_dialog(app: DamageCalculatorApp) -> None:
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
    from calculation.skills.segments import segment_display_label

    rotation_damage = dict(snap.segment_totals)
    pie_slices = damage_breakdown_from_skill_map(
        {segment_display_label(key): value for key, value in rotation_damage.items() if value > 0}
    )
    fig = build_damage_pie_figure(pie_slices, title="轮转伤害构成")
    zone_items = tuple(sorted(snap.zone_share_percent.items(), key=lambda item: -item[1]))
    bar_fig = build_improvement_bar_figure(
        zone_items,
        title="乘区构成占比",
        ylabel="占比 %",
    )
    try:
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

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
