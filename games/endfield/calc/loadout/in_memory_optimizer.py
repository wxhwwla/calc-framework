#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""内存 TopN 配装搜索（无 SQLite 续跑）。

支持 Rust 批量化加速（batch_size > 1 时自动启用）。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from utils.frozen_runtime import frozen_use_rust_batch, frozen_use_search_job_batch
from utils.search_diagnostics import log_search_config

from games.endfield.calc.damage.engine import DamageContext
from games.endfield.calc.loadout.optimizer import (
    LoadoutScore,
    OptimizerConfig,
    WeaponCandidate,
    build_optimizer_search_plan,
    enumerate_optimizer_tasks,
    evaluate_task,
)
from games.endfield.calc.loadout.optimizer.evaluate import evaluate_task_batch
from games.endfield.calc.search.evaluate.context import SearchEvalContext
from games.endfield.calc.search.evaluate.full_batch_eval import (
    can_run_full_batch_search,
    try_run_full_batch_from_plan,
)
from games.endfield.calc.search.evaluate.process_worker import (
    ProcessWorkerPayload,
    evaluate_optimizer_task_in_process,
)
from games.endfield.calc.search.evaluate.task import make_loadout_task_evaluator
from games.endfield.calc.search.evaluate.task_batch import can_batch_search_job_eval, make_loadout_task_evaluator_batch
from games.endfield.calc.search.plan.job import SingleSkillSearchJob
from games.endfield.calc.search.run.cancel import SearchCancelToken
from games.endfield.calc.search.run.parallel import ParallelBackend, run_bounded_parallel

# Rust 批量化默认 batch 大小
_DEFAULT_BATCH_SIZE = 1000


def run_enumerated_optimizer_parallel(
    *,
    base_context: DamageContext,
    weapons: list[WeaponCandidate],
    equipment_catalog: dict[str, list[dict[str, Any]]],
    config: OptimizerConfig,
    max_workers: int = 1,
    cancel_token: SearchCancelToken | None = None,
    progress_callback: Callable[[dict], None] | None = None,
    search_eval: SearchEvalContext | None = None,
    task_evaluator: Callable[[tuple[WeaponCandidate, tuple[dict, dict, dict, dict]]], LoadoutScore] | None = None,
    search_job: SingleSkillSearchJob | None = None,
    parallel_backend: ParallelBackend = "auto",
    batch_size: int = _DEFAULT_BATCH_SIZE,
) -> tuple[tuple[LoadoutScore, ...], int, int, bool, tuple[str, ...]]:
    """枚举全部配装任务并在内存中保留 TopN。

    新增 ``batch_size`` 参数（默认 1000）：>1 时启用 Rust 批量化加速。
    组合数 ≤ batch_size 时不批量（便于 cancel_after 精确取消）。
    PyInstaller 冻结 exe（``sys.frozen``）下强制线程池，避免 ProcessPool 反复 spawn onefile。

    Returns:
        (top_results, total_combinations, processed_combinations, cancelled, warnings)
    """
    # Tier-4 全批量：在枚举任务前先建 plan，以便复用固定配装与过滤后的目录
    if can_run_full_batch_search(
        search_eval=search_eval,
        search_job=search_job,
        task_evaluator=task_evaluator,
    ):
        assert search_eval is not None
        plan = build_optimizer_search_plan(
            weapons=weapons,
            equipment_catalog=equipment_catalog,
            config=config,
        )
        if plan.total_combinations > 0:
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
            if scores is not None:
                log_search_config(
                    phase="memory_full_batch",
                    total=plan.total_combinations,
                    max_workers=1,
                    parallel_backend="full_batch",
                    batch_size=plan.total_combinations,
                    use_batch=True,
                    use_job_batch=False,
                    use_full_batch=True,
                )
                cancelled = bool(cancel_token is not None and getattr(cancel_token, "is_cancelled", False))
                top = tuple(scores[: config.top_n])
                return top, plan.total_combinations, plan.total_combinations, cancelled, plan.warnings

    tasks, total_combinations, _pruned, warnings = enumerate_optimizer_tasks(
        base_context=base_context,
        weapons=weapons,
        equipment_catalog=equipment_catalog,
        config=config,
    )
    if total_combinations == 0:
        return (), 0, 0, False, warnings

    effective_evaluator = task_evaluator
    if effective_evaluator is None and search_job is not None:
        effective_evaluator = make_loadout_task_evaluator(
            search_job,
            crit_mode=config.crit_mode,
            search_eval=search_eval,
        )

    def _thread_evaluator(task):
        if effective_evaluator is not None:
            return effective_evaluator(task)
        return evaluate_task(
            base_context=base_context,
            crit_mode=config.crit_mode,
            task=task,
            search_eval=search_eval,
        )

    process_payload: ProcessWorkerPayload | None = None
    if effective_evaluator is None:
        process_payload = ProcessWorkerPayload(
            config=config,
            search_eval=search_eval,
            search_job=search_job,
            base_context=base_context if search_job is None else None,
        )

    backend: ParallelBackend = "thread" if effective_evaluator is not None else parallel_backend

    # ── Rust 批量化：裸 evaluate_task（phase≥4）或 search_job 单技能（phase≥3） ──
    use_naked_batch = (
        batch_size > 1 and effective_evaluator is None and total_combinations > batch_size and frozen_use_rust_batch()
    )
    use_job_batch = (
        batch_size > 1
        and search_job is not None
        and effective_evaluator is not None
        and total_combinations > batch_size
        and frozen_use_search_job_batch()
        and can_batch_search_job_eval(search_job)
    )
    use_batch = use_naked_batch or use_job_batch

    log_search_config(
        phase="memory",
        total=total_combinations,
        max_workers=max_workers,
        parallel_backend=backend,
        batch_size=batch_size,
        use_batch=use_batch,
        use_job_batch=use_job_batch,
    )

    if use_job_batch:
        assert search_job is not None
        batch_eval = make_loadout_task_evaluator_batch(
            search_job,
            crit_mode=config.crit_mode,
            search_eval=search_eval,
        )
        top_results, processed, cancelled = run_bounded_parallel(
            work_items=tasks,
            total=total_combinations,
            evaluate=_thread_evaluator,
            max_workers=max_workers,
            cancel_token=cancel_token,
            progress_callback=progress_callback,
            top_n=config.top_n,
            top_key=lambda score: score.final_damage,
            parallel_backend=backend,
            batch_size=batch_size,
            batch_evaluate=batch_eval,
            process_payload=process_payload,
        )
    elif use_naked_batch:
        batch_eval = evaluate_task_batch(
            base_context=base_context,
            crit_mode=config.crit_mode,
            search_eval=search_eval,
        )

        top_results, processed, cancelled = run_bounded_parallel(
            work_items=tasks,
            total=total_combinations,
            evaluate=_thread_evaluator,  # unused in batch mode
            max_workers=max_workers,
            cancel_token=cancel_token,
            progress_callback=progress_callback,
            top_n=config.top_n,
            top_key=lambda score: score.final_damage,
            parallel_backend=backend,
            batch_size=batch_size,
            batch_evaluate=batch_eval,
            process_payload=process_payload,
        )
    else:
        top_results, processed, cancelled = run_bounded_parallel(
            work_items=tasks,
            total=total_combinations,
            evaluate=_thread_evaluator,
            max_workers=max_workers,
            cancel_token=cancel_token,
            progress_callback=progress_callback,
            top_n=config.top_n,
            top_key=lambda score: score.final_damage,
            parallel_backend=backend,
            process_payload=process_payload,
            process_evaluate=evaluate_optimizer_task_in_process if process_payload else None,
        )
    return top_results, total_combinations, processed, cancelled, warnings
