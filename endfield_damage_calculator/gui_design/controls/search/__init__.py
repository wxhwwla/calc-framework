#!/usr/bin/env python3
"""全量搜索控件。"""

from .actions import (
    compute_search_estimate_text,
    on_cancel_search,
    on_fixed_loadout_changed,
    on_run_full_search,
    on_run_mvp_search,
    prepare_single_skill_search_job,
    refresh_parallel_workers_hint,
    refresh_search_estimate,
    set_mvp_status,
    set_search_buttons_enabled,
    show_search_result_popup,
    start_search_worker,
)
from .section import build_search_job_inputs, place_search_section

__all__ = [
    "build_search_job_inputs",
    "compute_search_estimate_text",
    "on_cancel_search",
    "on_fixed_loadout_changed",
    "on_run_full_search",
    "on_run_mvp_search",
    "place_search_section",
    "prepare_single_skill_search_job",
    "refresh_parallel_workers_hint",
    "refresh_search_estimate",
    "set_mvp_status",
    "set_search_buttons_enabled",
    "show_search_result_popup",
    "start_search_worker",
]
