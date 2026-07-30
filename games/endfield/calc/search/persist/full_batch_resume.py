# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""SQLite 续跑路径上的 Rust 全批量快捷通道。

仅在「尚无已处理键」的全新 run 上尝试；成功后写入 TopN 并标记 completed。
部分续跑（已有 processed keys）仍走 SoA / 并行路径。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from utils.search_diagnostics import log_search_config

from games.endfield.calc.damage.engine import DamageContext
from games.endfield.calc.loadout.optimizer import LoadoutScore, OptimizerConfig
from games.endfield.calc.loadout.optimizer.types import OptimizerSearchPlan
from games.endfield.calc.search.evaluate.context import SearchEvalContext
from games.endfield.calc.search.evaluate.full_batch_eval import (
    can_run_full_batch_search,
    try_run_full_batch_from_plan,
)
from games.endfield.calc.search.plan.job import SingleSkillSearchJob
from games.endfield.calc.search.run.cancel import SearchCancelToken

from .schema import ResumeExecutionResult


def try_resume_via_full_batch(
    *,
    store: Any,
    run_signature: str,
    plan: OptimizerSearchPlan,
    config: OptimizerConfig,
    base_context: DamageContext,
    search_eval: SearchEvalContext | None,
    search_job: SingleSkillSearchJob | None,
    task_evaluator: Callable[..., LoadoutScore] | None,
    progress_callback: Callable[[dict], None] | None,
    cancel_token: SearchCancelToken | None,
) -> ResumeExecutionResult | None:
    """全新续跑尝试全批量；不满足条件或失败时返回 None。"""
    if not can_run_full_batch_search(
        search_eval=search_eval,
        search_job=search_job,
        task_evaluator=task_evaluator,
    ):
        return None
    if search_eval is None or plan.total_combinations <= 0:
        return None

    scores = try_run_full_batch_from_plan(
        weapons=list(plan.weapons),
        equipment_catalog=dict(plan.equipment_catalog),
        config=config,
        fixed_loadout=plan.fixed_loadout,
        base_context=base_context,
        search_eval=search_eval,
        top_n=config.top_n,
        progress_callback=progress_callback,
        cancel_token=cancel_token,
    )
    if scores is None:
        return None

    cancelled = bool(cancel_token is not None and getattr(cancel_token, "is_cancelled", False))
    top = tuple(scores[: config.top_n])
    store.replace_top_scores(run_signature, top)
    store.mark_run_status(run_signature, "cancelled" if cancelled else "completed")

    log_search_config(
        phase="resume_full_batch",
        run_signature=run_signature,
        total=plan.total_combinations,
        max_workers=1,
        parallel_backend="full_batch",
        batch_size=plan.total_combinations,
        use_batch=True,
        use_job_batch=False,
        use_full_batch=True,
        skipped=0,
    )

    return ResumeExecutionResult(
        top_results=top,
        total_combinations=plan.total_combinations,
        processed_combinations=plan.total_combinations,
        processed_this_run=0 if cancelled else plan.total_combinations,
        skipped_preprocessed=0,
        cancelled=cancelled,
    )


def completed_run_short_circuit(
    *,
    store: Any,
    run_signature: str,
    total_combinations: int,
    top_n: int,
) -> ResumeExecutionResult | None:
    """若 run 已 completed，直接返回持久化 TopN，避免重复枚举。"""
    if store.run_status(run_signature) != "completed":
        return None
    top = store.load_top_scores(run_signature, top_n)
    return ResumeExecutionResult(
        top_results=top,
        total_combinations=total_combinations,
        processed_combinations=total_combinations,
        processed_this_run=0,
        skipped_preprocessed=total_combinations,
        cancelled=False,
    )


__all__ = [
    "completed_run_short_circuit",
    "try_resume_via_full_batch",
]
