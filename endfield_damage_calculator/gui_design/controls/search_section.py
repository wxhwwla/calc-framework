#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全量搜索区 UI。"""

from __future__ import annotations

import threading
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import TYPE_CHECKING, Callable, Dict, Optional

from utils.platform_win32_patch import apply_platform_win32_patch

# Windows：PyInstaller 会单独 import 本模块，须在 CTk 之前打 WMI 补丁
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
from .fixed_loadout_controls import (
    create_fixed_loadout_controls,
    refresh_all_fixed_slot_menus,
)
from gui_design.gui_layout import (
    FIXED_LOADOUT_HINT_BOX_HEIGHT,
    PRIMARY_ACTION_BUTTON_HEIGHT,
    SEARCH_ESTIMATE_BOX_HEIGHT,
    search_action_button_texts,
    SEARCH_STATUS_BOX_HEIGHT,
    SEARCH_WORKERS_HINT_BOX_HEIGHT,
    SECONDARY_ACTION_BUTTON_HEIGHT,
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
    from .search_actions import (
        on_run_full_search,
        on_run_mvp_search,
        refresh_search_estimate,
    )

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
    fixed_hint_box = ctk.CTkFrame(
        parent, height=FIXED_LOADOUT_HINT_BOX_HEIGHT, fg_color="transparent"
    )
    fixed_hint_box.grid(row=sr, column=0, padx=4, pady=(0, 6), sticky="ew")
    fixed_hint_box.grid_propagate(False)
    fixed_hint_box.grid_columnconfigure(0, weight=1)
    fixed_hint_box.grid_rowconfigure(0, weight=1)
    sr += 1
    fixed_hint = ctk.CTkLabel(
        fixed_hint_box,
        text=FIXED_LOADOUT_HINT,
        font=app.small_font,
        text_color="#888888",
        justify="left",
        anchor="nw",
    )
    fixed_hint.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
    wrap_label(fixed_hint, fixed_hint_box)

    def _on_search_scope_change(_value: str = "") -> None:
        app._refresh_fixed_loadout_menus()
        refresh_search_estimate(app)

    app.single_skill_scope_menu.configure(command=_on_search_scope_change)
    app.single_skill_equipment_scope_menu.configure(command=_on_search_scope_change)

    estimate_box = ctk.CTkFrame(parent, height=SEARCH_ESTIMATE_BOX_HEIGHT, fg_color="transparent")
    estimate_box.grid(row=sr, column=0, padx=4, pady=(0, 6), sticky="ew")
    estimate_box.grid_propagate(False)
    estimate_box.grid_columnconfigure(0, weight=1)
    estimate_box.grid_rowconfigure(0, weight=1)
    app.search_estimate_label = ctk.CTkLabel(
        estimate_box,
        text="预计组合数：—",
        font=app.small_font,
        text_color="#AAAAAA",
        justify="left",
        anchor="nw",
    )
    app.search_estimate_label.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
    wrap_label(app.search_estimate_label, estimate_box)
    sr += 1

    btn_row = ctk.CTkFrame(parent, fg_color="transparent")
    btn_row.grid(row=sr, column=0, padx=4, pady=(0, 4), sticky="ew")
    btn_row.grid_columnconfigure(0, weight=1)
    btn_row.grid_columnconfigure(1, weight=1)
    sr += 1
    full_text, mvp_text = search_action_button_texts(compact=False)
    app.full_search_btn = ctk.CTkButton(
        btn_row,
        text=full_text,
        font=app.small_font,
        height=PRIMARY_ACTION_BUTTON_HEIGHT,
        command=lambda: on_run_full_search(app),
    )
    app.full_search_btn.grid(row=0, column=0, padx=(0, 4), sticky="ew")
    app.mvp_search_btn = ctk.CTkButton(
        btn_row,
        text=mvp_text,
        font=app.small_font,
        height=PRIMARY_ACTION_BUTTON_HEIGHT,
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

    workers_hint_box = ctk.CTkFrame(
        parent, height=SEARCH_WORKERS_HINT_BOX_HEIGHT, fg_color="transparent"
    )
    workers_hint_box.grid(row=sr, column=0, padx=4, pady=(0, 4), sticky="ew")
    workers_hint_box.grid_propagate(False)
    workers_hint_box.grid_columnconfigure(0, weight=1)
    workers_hint_box.grid_rowconfigure(0, weight=1)
    sr += 1
    app.search_workers_hint_label = ctk.CTkLabel(
        workers_hint_box,
        text="",
        font=app.small_font,
        text_color="#777777",
        justify="left",
        anchor="nw",
    )
    app.search_workers_hint_label.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
    wrap_label(app.search_workers_hint_label, workers_hint_box)
    refresh_parallel_workers_hint(app)

    status_box = ctk.CTkFrame(
        parent, height=SEARCH_STATUS_BOX_HEIGHT, fg_color="transparent"
    )
    status_box.grid(row=sr, column=0, padx=4, pady=(0, 4), sticky="ew")
    status_box.grid_propagate(False)
    status_box.grid_columnconfigure(0, weight=1)
    status_box.grid_rowconfigure(0, weight=1)
    sr += 1
    app.mvp_status_label = ctk.CTkLabel(
        status_box,
        text="搜索状态：未开始",
        font=app.small_font,
        text_color="#888888",
        justify="left",
        anchor="nw",
    )
    app.mvp_status_label.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
    wrap_label(app.mvp_status_label, status_box)

    app.search_cancel_btn = ctk.CTkButton(
        parent,
        text="取消搜索",
        font=app.small_font,
        height=SECONDARY_ACTION_BUTTON_HEIGHT,
        state="disabled",
        fg_color="#8B3A3A",
        hover_color="#A04848",
        command=lambda: on_cancel_search(app),
    )
    _place(sr, app.search_cancel_btn, pady=(0, 4))


