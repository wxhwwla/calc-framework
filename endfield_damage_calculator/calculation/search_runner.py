#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""并行搜索执行器。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from calculation.damage_engine import DamageContext
from calculation.loadout_optimizer import (
    LoadoutScore,
    OptimizerConfig,
    enumerate_optimizer_tasks,
    evaluate_task,
)
from calculation.parallel_search import run_bounded_parallel
from calculation.search_cancel import SearchCancelToken

__all__ = ("SearchCancelToken", "ParallelSearchResult", "run_search_parallel")


@dataclass(frozen=True)
class ParallelSearchResult:
    """并行搜索结果。"""

    top_results: tuple[LoadoutScore, ...]
    total_combinations: int
    processed_combinations: int
    cancelled: bool
    warnings: tuple[str, ...]


def run_search_parallel(
    *,
    base_context: DamageContext,
    weapons,
    equipment_catalog,
    config: OptimizerConfig,
    max_workers: int = 1,
    cancel_token: Optional[SearchCancelToken] = None,
    progress_callback: Optional[Callable[[dict], None]] = None,
) -> ParallelSearchResult:
    """并行执行单技能搜索，支持进度回调与取消。"""
    tasks, total_combinations, _pruned, warnings = enumerate_optimizer_tasks(
        base_context=base_context,
        weapons=weapons,
        equipment_catalog=equipment_catalog,
        config=config,
    )
    if total_combinations == 0:
        return ParallelSearchResult(
            top_results=(),
            total_combinations=0,
            processed_combinations=0,
            cancelled=False,
            warnings=warnings,
        )

    evaluator = lambda task: evaluate_task(
        base_context=base_context,
        crit_mode=config.crit_mode,
        task=task,
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

    return ParallelSearchResult(
        top_results=top_results,
        total_combinations=total_combinations,
        processed_combinations=processed,
        cancelled=cancelled,
        warnings=warnings,
    )
