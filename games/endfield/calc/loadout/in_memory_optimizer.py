#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""内存 TopN 配装搜索（无 SQLite 续跑）。

支持 Rust 批量化加速（batch_size > 1 时自动启用）。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from utils.search_diagnostics import log_search_config

from games.endfield.calc.damage.engine import DamageContext
from games.endfield.calc.loadout.optimizer import (
    LoadoutScore,
    OptimizerConfig,
    WeaponCandidate,
    enumerate_optimizer_tasks,
    evaluate_task,
)
from games.endfield.calc.loadout.optimizer.evaluate import evaluate_task_batch
from games.endfield.calc.search.evaluate.context import SearchEvalContext
from games.endfield.calc.search.evaluate.process_worker import (
    ProcessWorkerPayload,
    evaluate_optimizer_task_in_process,
)
from games.endfield.calc.search.evaluate.task import make_loadout_task_evaluator
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
    search_job: Any | None = None,
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

    # ── Rust 批量化路径（仅裸 evaluate_task；有 search_job 时逐条评估） ──
    use_batch = batch_size > 1 and effective_evaluator is None and total_combinations > batch_size

    log_search_config(
        phase="memory",
        total=total_combinations,
        max_workers=max_workers,
        parallel_backend=backend,
        batch_size=batch_size,
        use_batch=use_batch,
    )

    if use_batch:
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
