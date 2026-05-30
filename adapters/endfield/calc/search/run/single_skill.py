#!/usr/bin/env python3
"""
单技能全量搜索编排（无 GUI 依赖）。

- ``estimate_single_skill_search``：与全量共用 ``optimizer_config_for_character``，保证预估组合数与实跑一致；
- ``run_exported_single_skill_search``：在 ``export_root`` 下写 ``search_runs.db`` 并调用 ``mvp_pipeline``。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from adapters.endfield.calc.loadout.optimizer import OptimizerConfig, optimizer_config_for_character
from utils.search_format import format_workload_estimate_line

from ..plan.controller import optimizer_config_for_search_job
from ..plan.estimate import (
    SearchDurationEstimate,
    SearchWorkloadPreview,
    estimate_search_duration,
    preview_search_workload,
)
from ..plan.job import SingleSkillSearchJob
from .cancel import SearchCancelToken
from .mvp import MvpSearchOutcome, run_mvp_search_from_job


@dataclass(frozen=True)
class SingleSkillSearchEstimate:
    """全量遍历预估摘要。"""

    text: str
    estimated_seconds: float
    workload: SearchWorkloadPreview
    duration: SearchDurationEstimate


def estimate_single_skill_search(
    job: SingleSkillSearchJob,
    *,
    max_workers: int,
    top_n: int,
) -> SingleSkillSearchEstimate:
    """根据作业计算预计组合数/耗时文案。"""
    if job.multi_skill_eval is not None:
        priority_types = job.multi_skill_eval.priority_skill_types
    else:
        priority_types = (str(job.base_context.skill_type or job.skill_label),)
    workload = preview_search_workload(
        weapons=list(job.weapon_candidates),
        equipment_catalog=job.equipment_catalog,
        config=optimizer_config_for_character(
            job.char_data,
            priority_skill_types=priority_types,
            fixed_loadout=job.fixed_loadout,
            top_n=top_n,
            warn_on_unfiltered=False,
            prune_non_beneficial=True,
        ),
    )
    duration = estimate_search_duration(
        total_combinations=workload.total_combinations,
        max_workers=max_workers,
    )
    return SingleSkillSearchEstimate(
        text=format_workload_estimate_line(workload=workload, duration=duration),
        estimated_seconds=duration.estimated_seconds,
        workload=workload,
        duration=duration,
    )


def run_exported_single_skill_search(
    job: SingleSkillSearchJob,
    *,
    export_root: Path,
    config: OptimizerConfig | None = None,
    top_n: int = 10,
    max_workers: int = 1,
    cancel_token: SearchCancelToken | None = None,
    progress_callback: Callable[[dict], None] | None = None,
) -> MvpSearchOutcome:
    """在 export_root 下执行续跑搜索并导出 MVP 结果。"""
    if config is None:
        config = optimizer_config_for_search_job(job, top_n=top_n)
    db_path = Path(export_root) / "search_runs.db"
    export_dir = Path(export_root) / "mvp_exports"
    return run_mvp_search_from_job(
        job,
        db_path=db_path,
        export_dir=export_dir,
        config=config,
        max_workers=max_workers,
        cancel_token=cancel_token,
        progress_callback=progress_callback,
    )
