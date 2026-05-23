#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""内存 TopN 配装搜索（无 SQLite 续跑）。"""

from __future__ import annotations

from typing import Any, Callable, Optional

from calculation.damage_engine import DamageContext
from calculation.loadout_optimizer import (
    LoadoutScore,
    OptimizerConfig,
    WeaponCandidate,
    enumerate_optimizer_tasks,
    evaluate_task,
)
from calculation.parallel_search import run_bounded_parallel
from calculation.search_cancel import SearchCancelToken
from calculation.search_eval_context import SearchEvalContext


def run_enumerated_optimizer_parallel(
    *,
    base_context: DamageContext,
    weapons: list[WeaponCandidate],
    equipment_catalog: dict[str, list[dict[str, Any]]],
    config: OptimizerConfig,
    max_workers: int = 1,
    cancel_token: Optional[SearchCancelToken] = None,
    progress_callback: Optional[Callable[[dict], None]] = None,
    search_eval: Optional[SearchEvalContext] = None,
    task_evaluator: Optional[
        Callable[[tuple[WeaponCandidate, tuple[dict, dict, dict, dict]]], LoadoutScore]
    ] = None,
) -> tuple[tuple[LoadoutScore, ...], int, int, bool, tuple[str, ...]]:
    """
    枚举全部配装任务并在内存中保留 TopN。

    返回 (top_results, total_combinations, processed_combinations, cancelled, warnings)。
    """
    tasks, total_combinations, _pruned, warnings = enumerate_optimizer_tasks(
        base_context=base_context,
        weapons=weapons,
        equipment_catalog=equipment_catalog,
        config=config,
    )
    if total_combinations == 0:
        return (), 0, 0, False, warnings

    def evaluator(task):
        if task_evaluator is not None:
            return task_evaluator(task)
        return evaluate_task(
            base_context=base_context,
            crit_mode=config.crit_mode,
            task=task,
            search_eval=search_eval,
        )
    top_results, processed, cancelled = run_bounded_parallel(
        work_items=tasks,
        total=total_combinations,
        evaluate=evaluator,
        max_workers=max_workers,
        cancel_token=cancel_token,
        progress_callback=progress_callback,
        top_n=config.top_n,
        top_key=lambda score: score.final_damage,
    )
    return top_results, total_combinations, processed, cancelled, warnings
