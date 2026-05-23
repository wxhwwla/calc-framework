#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全量遍历底栏：武器/装备范围、固定配装、并行参数、预估与搜索动作。

与 ``enhancement_controls`` 对称：控件布局与搜索线程编排集中于此，``gui`` 只保留委托。
"""

from __future__ import annotations

import threading
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import TYPE_CHECKING, Callable, Dict, Optional

from utils.platform_win32_patch import apply_platform_win32_patch

apply_platform_win32_patch()
import customtkinter as ctk

from calculation.loadout_optimizer import WeaponCandidate
from calculation.mvp_pipeline import MvpSearchOutcome
from calculation.search_cancel import SearchCancelToken
from calculation.search_controller import (
    SearchJobInputs,
    optimizer_config_for_search_job,
    prepare_search_job,
)
from calculation.single_skill_search_job import SingleSkillSearchJob
from calculation.single_skill_search_runner import (
    estimate_single_skill_search,
    run_exported_single_skill_search,
)
from gui_design.fixed_loadout_controls import (
    create_fixed_loadout_controls,
    refresh_all_fixed_slot_menus,
)
from gui_design.panel_hints import FIXED_LOADOUT_HINT
from gui_design.search_estimate_message import compose_search_estimate_message
from gui_design.search_results_lines import (
    build_search_results_report_lines,
    export_paths_to_strings,
)
from gui_design.search_results_view import show_search_results_dialog
from gui_design.search_settings import (
    build_worker_option_labels,
    format_parallel_workers_help,
    format_search_progress_text,
    get_cpu_parallel_info,
    resolve_parallel_workers,
    resolve_top_n,
)
from utils.app_paths import allocate_search_run_directory, default_search_output_root

if TYPE_CHECKING:
    from gui_design.gui import DamageCalculatorApp


def build_search_job_inputs(app: "DamageCalculatorApp") -> Optional[SearchJobInputs]:
    """从当前 GUI 刮取全量搜索输入（预估与实跑共用）。"""
    from gui_design.loadout_state import read_loadout_from_app

    state = read_loadout_from_app(app)
    if state is None:
        return None
    return state.to_search_job_inputs(
        all_weapons=app.all_weapons,
        equipment_catalog=app._single_skill_preview_equipment_catalog(),
    )


def place_search_section(
    app: "DamageCalculatorApp",
    parent: ctk.CTkFrame,
    *,
    wrap_label: Callable[[ctk.CTkLabel, ctk.CTkBaseClass], None],
) -> None:
    """在底栏「全量遍历」列放置搜索相关控件。"""
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

    sr = 0
    sr = _section("全量遍历", sr)
    sr = _place(
        sr,
        ctk.CTkLabel(parent, text="武器候选范围", font=app.small_font, text_color="#CCCCCC"),
        pady=(0, 2),
    )
    app.single_skill_scope_menu = ctk.CTkOptionMenu(
        parent,
        values=["当前武器", "同类型同星级", "同类型全部"],
        variable=app.single_skill_scope_var,
        font=app.small_font,
    )
    sr = _place(sr, app.single_skill_scope_menu)
    sr = _place(
        sr,
        ctk.CTkLabel(parent, text="装备范围", font=app.small_font, text_color="#CCCCCC"),
        pady=(0, 2),
    )
    app.single_skill_equipment_scope_menu = ctk.CTkOptionMenu(
        parent,
        values=["全部装备", "仅套装装备", "仅散件装备"],
        variable=app.single_skill_equipment_scope_var,
        font=app.small_font,
    )
    sr = _place(sr, app.single_skill_equipment_scope_menu)
    fixed_intro = ctk.CTkLabel(
        parent,
        text="固定配装（0–4 件）",
        font=app.small_font,
        text_color="#CCCCCC",
    )
    sr = _place(sr, fixed_intro, pady=(4, 2))
    app._fixed_loadout_frame = ctk.CTkFrame(parent, fg_color="transparent")
    app._fixed_loadout_frame.grid(row=sr, column=0, padx=4, pady=(0, 4), sticky="ew")
    sr += 1
    app._fixed_loadout_slots = create_fixed_loadout_controls(
        app._fixed_loadout_frame,
        small_font=app.small_font,
        on_change=lambda: on_fixed_loadout_changed(app),
    )
    fixed_hint = ctk.CTkLabel(
        parent,
        text=FIXED_LOADOUT_HINT,
        font=app.small_font,
        text_color="#888888",
        justify="left",
        anchor="w",
    )
    sr = _place(sr, fixed_hint, pady=(0, 6))
    wrap_label(fixed_hint, parent)

    def _on_search_scope_change(_value: str = "") -> None:
        app._refresh_fixed_loadout_menus()
        refresh_search_estimate(app)
        app._schedule_confirm()

    app.single_skill_scope_menu.configure(command=_on_search_scope_change)
    app.single_skill_equipment_scope_menu.configure(command=_on_search_scope_change)

    app.search_estimate_label = ctk.CTkLabel(
        parent,
        text="预计组合数：—",
        font=app.small_font,
        text_color="#AAAAAA",
        justify="left",
        anchor="w",
    )
    sr = _place(sr, app.search_estimate_label, pady=(0, 6))
    wrap_label(app.search_estimate_label, parent)

    btn_row = ctk.CTkFrame(parent, fg_color="transparent")
    btn_row.grid(row=sr, column=0, padx=4, pady=(0, 4), sticky="ew")
    btn_row.grid_columnconfigure(0, weight=1)
    btn_row.grid_columnconfigure(1, weight=1)
    sr += 1
    app.full_search_btn = ctk.CTkButton(
        btn_row,
        text="全量遍历(弹窗结果)",
        font=app.small_font,
        command=lambda: on_run_full_search(app),
    )
    app.full_search_btn.grid(row=0, column=0, padx=(0, 4), sticky="ew")
    app.mvp_search_btn = ctk.CTkButton(
        btn_row,
        text="实验：MVP搜索并导出",
        font=app.small_font,
        command=lambda: on_run_mvp_search(app),
    )
    app.mvp_search_btn.grid(row=0, column=1, padx=(4, 0), sticky="ew")

    search_param_row = ctk.CTkFrame(parent, fg_color="transparent")
    search_param_row.grid(row=sr, column=0, padx=4, pady=(0, 4), sticky="ew")
    search_param_row.grid_columnconfigure(0, weight=1)
    search_param_row.grid_columnconfigure(1, weight=1)
    sr += 1
    ctk.CTkLabel(
        search_param_row, text="并行线程", font=app.small_font, text_color="#CCCCCC"
    ).grid(row=0, column=0, sticky="w")
    ctk.CTkLabel(
        search_param_row, text="Top 条数", font=app.small_font, text_color="#CCCCCC"
    ).grid(row=0, column=1, sticky="w")
    app.search_workers_menu = ctk.CTkOptionMenu(
        search_param_row,
        values=build_worker_option_labels(),
        variable=app.search_workers_var,
        font=app.small_font,
        command=lambda _v: (
            refresh_parallel_workers_hint(app),
            refresh_search_estimate(app),
        ),
    )
    app.search_workers_menu.grid(row=1, column=0, padx=(0, 4), pady=(0, 2), sticky="ew")
    app.search_top_n_menu = ctk.CTkOptionMenu(
        search_param_row,
        values=["3", "5", "10", "20", "50"],
        variable=app.search_top_n_var,
        font=app.small_font,
    )
    app.search_top_n_menu.grid(row=1, column=1, padx=(4, 0), pady=(0, 2), sticky="ew")

    app.search_workers_hint_label = ctk.CTkLabel(
        parent,
        text="",
        font=app.small_font,
        text_color="#777777",
        justify="left",
        anchor="w",
    )
    sr = _place(sr, app.search_workers_hint_label, pady=(0, 4))
    wrap_label(app.search_workers_hint_label, parent)
    refresh_parallel_workers_hint(app)

    app.search_cancel_btn = ctk.CTkButton(
        parent,
        text="取消搜索",
        font=app.small_font,
        state="disabled",
        fg_color="#8B3A3A",
        hover_color="#A04848",
        command=lambda: on_cancel_search(app),
    )
    sr = _place(sr, app.search_cancel_btn, pady=(0, 4))
    app.mvp_status_label = ctk.CTkLabel(
        parent,
        text="搜索状态：未开始",
        font=app.small_font,
        text_color="#888888",
        justify="left",
        anchor="w",
    )
    sr = _place(sr, app.mvp_status_label)
    wrap_label(app.mvp_status_label, parent)


def set_mvp_status(app: "DamageCalculatorApp", text: str) -> None:
    if app.mvp_status_label is not None:
        app.mvp_status_label.configure(text=text)


def set_search_buttons_enabled(app: "DamageCalculatorApp", enabled: bool) -> None:
    state = "normal" if enabled else "disabled"
    if app.mvp_search_btn is not None:
        app.mvp_search_btn.configure(state=state)
    if app.full_search_btn is not None:
        app.full_search_btn.configure(state=state)
    if app.search_workers_menu is not None:
        app.search_workers_menu.configure(state=state)
    if app.search_top_n_menu is not None:
        app.search_top_n_menu.configure(state=state)
    if app.search_cancel_btn is not None:
        app.search_cancel_btn.configure(state="normal" if not enabled else "disabled")


def refresh_parallel_workers_hint(app: "DamageCalculatorApp") -> None:
    if app.search_workers_hint_label is None:
        return
    info = get_cpu_parallel_info()
    workers = resolve_parallel_workers(app.search_workers_var.get())
    app.search_workers_hint_label.configure(
        text=format_parallel_workers_help(info, selected_workers=workers)
    )


def refresh_search_estimate(app: "DamageCalculatorApp") -> None:
    """刷新「预计组合数/耗时」标签。"""
    if app.search_estimate_label is None:
        return
    assert app.char_panel is not None
    assert app.weapon_panel is not None
    has_char = bool(app.char_panel.get_selected_data())
    has_weapon = bool(app.weapon_panel.get_selected_data())
    scope_label = str(app.single_skill_equipment_scope_var.get())
    catalog_err: Optional[str] = None
    if has_char and has_weapon:
        catalog_err = app.game_data.catalog_search_error(scope_label)
    weapons_empty = False
    job_error: Optional[str] = None
    estimate_text: Optional[str] = None
    if has_char and has_weapon and not catalog_err:
        weapons = app._single_skill_preview_candidates()
        weapons_empty = not weapons
        if not weapons_empty:
            inputs = build_search_job_inputs(app)
            if inputs is None:
                job_error = "请先选择角色和武器"
            else:
                preview_job, err = prepare_search_job(inputs)
                if err or preview_job is None:
                    job_error = err or "无法预估"
                else:
                    estimate = estimate_single_skill_search(
                        preview_job,
                        max_workers=resolve_parallel_workers(app.search_workers_var.get()),
                        top_n=resolve_top_n(app.search_top_n_var.get()),
                    )
                    app._search_estimated_total_seconds = estimate.estimated_seconds
                    estimate_text = estimate.text
    text = compose_search_estimate_message(
        has_char=has_char,
        has_weapon=has_weapon,
        catalog_err=catalog_err,
        weapons_empty=weapons_empty,
        job_error=job_error,
        estimate_text=estimate_text,
    )
    app.search_estimate_label.configure(text=text)


def compute_search_estimate_text(app: "DamageCalculatorApp", job: SingleSkillSearchJob) -> str:
    estimate = estimate_single_skill_search(
        job,
        max_workers=resolve_parallel_workers(app.search_workers_var.get()),
        top_n=resolve_top_n(app.search_top_n_var.get()),
    )
    app._search_estimated_total_seconds = estimate.estimated_seconds
    return estimate.text


def prepare_single_skill_search_job(app: "DamageCalculatorApp") -> Optional[SingleSkillSearchJob]:
    inputs = build_search_job_inputs(app)
    if inputs is None:
        if not app.char_panel or not app.char_panel.get_selected_data():
            messagebox.showwarning("全量遍历", "请先选择有效角色。", parent=app.app)
        else:
            messagebox.showwarning("全量遍历", "请先选择有效武器。", parent=app.app)
        return None
    job, err = prepare_search_job(inputs)
    if err:
        messagebox.showwarning("全量遍历", err, parent=app.app)
        return None
    return job


def on_fixed_loadout_changed(app: "DamageCalculatorApp") -> None:
    catalog = app._single_skill_preview_equipment_catalog()
    refresh_all_fixed_slot_menus(catalog, app._fixed_loadout_slots)
    refresh_search_estimate(app)
    app._schedule_confirm()


def on_cancel_search(app: "DamageCalculatorApp") -> None:
    if app._search_cancel_token is not None:
        app._search_cancel_token.cancel()
        set_mvp_status(app, "搜索状态：正在取消…")


def show_search_result_popup(
    app: "DamageCalculatorApp",
    *,
    mode_label: str,
    job: SingleSkillSearchJob,
    outcome: MvpSearchOutcome,
    export_paths: Optional[Dict[str, str]] = None,
) -> None:
    damage_metric = "加权总伤" if job.multi_skill_eval is not None else "伤害"
    lines = build_search_results_report_lines(
        mode_label=mode_label,
        skill_label=str(job.skill_label),
        scope_labels=(str(job.weapon_scope), str(job.equipment_scope)),
        processed_combinations=int(outcome.processed_combinations),
        total_combinations=int(outcome.total_combinations),
        top_results=outcome.top_results,
        export_paths=export_paths,
        cancelled=bool(outcome.cancelled),
        damage_metric=damage_metric,
    )
    show_search_results_dialog(app.app, title=mode_label, lines=lines)


def start_search_worker(
    app: "DamageCalculatorApp",
    *,
    mode_label: str,
    export_root: Path,
    job: SingleSkillSearchJob,
    status_running: str,
    status_done_prefix: str,
) -> None:
    top_n = resolve_top_n(app.search_top_n_var.get())
    max_workers = resolve_parallel_workers(app.search_workers_var.get())
    config = optimizer_config_for_search_job(job, top_n=top_n)
    app._search_cancel_token = SearchCancelToken()
    progress_prefix = status_done_prefix
    estimate_text = compute_search_estimate_text(app, job)

    def _progress_callback(info: dict) -> None:
        text = format_search_progress_text(
            prefix=progress_prefix,
            processed=int(info.get("processed", 0)),
            total=int(info.get("total", 0)),
            eta_seconds=float(info.get("eta_seconds", 0.0)),
            estimated_total_seconds=app._search_estimated_total_seconds,
        )

        def _update_status() -> None:
            set_mvp_status(app, text)

        app.app.after(0, _update_status)

    set_search_buttons_enabled(app, False)
    if app.search_estimate_label is not None:
        app.search_estimate_label.configure(text=estimate_text)
    set_mvp_status(
        app,
        f"{status_running}\n导出目录：{export_root}\n\n{estimate_text}",
    )

    def _worker() -> None:
        try:
            outcome = run_exported_single_skill_search(
                job,
                export_root=export_root,
                config=config,
                max_workers=max_workers,
                cancel_token=app._search_cancel_token,
                progress_callback=_progress_callback,
            )
        except Exception as exc:

            def _report_failure(error: BaseException = exc) -> None:
                app._search_cancel_token = None
                detail = str(error)
                set_mvp_status(app, f"{status_done_prefix}：失败\n{detail}")
                messagebox.showerror(mode_label, detail, parent=app.app)
                set_search_buttons_enabled(app, True)

            app.app.after(0, _report_failure)
            return

        export_paths = export_paths_to_strings(outcome.exports or {})
        export_paths["数据库"] = str(outcome.db_path)
        export_paths["导出目录"] = str(outcome.export_dir)

        def _finish() -> None:
            app._search_cancel_token = None
            suffix = "（已取消）" if outcome.cancelled else "：完成"
            set_mvp_status(
                app,
                f"{status_done_prefix}{suffix}（{outcome.processed_combinations}/"
                f"{outcome.total_combinations}）",
            )
            set_search_buttons_enabled(app, True)
            show_search_result_popup(
                app,
                mode_label=mode_label,
                job=job,
                outcome=outcome,
                export_paths=export_paths,
            )

        app.app.after(0, _finish)

    threading.Thread(target=_worker, daemon=True).start()


def on_run_full_search(app: "DamageCalculatorApp") -> None:
    job = prepare_single_skill_search_job(app)
    if not job:
        return
    estimate_text = compute_search_estimate_text(app, job)
    if app._search_estimated_total_seconds >= 120:
        if not messagebox.askyesno(
            "确认全量遍历",
            f"{estimate_text}\n\n组合较多，是否仍要开始？",
            parent=app.app,
        ):
            return
    export_root = allocate_search_run_directory(purpose="full_search")
    mode_label = (
        "多技能加权全量遍历"
        if job.multi_skill_eval is not None
        else "单技能全量遍历"
    )
    start_search_worker(
        app,
        mode_label=mode_label,
        export_root=export_root,
        job=job,
        status_running="全量遍历：计算中，请稍候…",
        status_done_prefix="全量遍历",
    )


def on_run_mvp_search(app: "DamageCalculatorApp") -> None:
    job = prepare_single_skill_search_job(app)
    if not job:
        return
    output_dir = filedialog.askdirectory(
        parent=app.app,
        title="选择MVP搜索导出目录",
        initialdir=str(default_search_output_root()),
    )
    if not output_dir:
        export_root = allocate_search_run_directory(purpose="mvp_search")
    else:
        export_root = Path(output_dir)
    start_search_worker(
        app,
        mode_label="MVP搜索并导出",
        export_root=export_root,
        job=job,
        status_running="MVP搜索状态：计算中，请稍候...",
        status_done_prefix="MVP搜索状态",
    )
