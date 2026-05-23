#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""单技能搜索会话：有界并行 + 可选 SQLite 续跑。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
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
from calculation.search_persistence import execute_search_with_resume


@dataclass(frozen=True)
class SearchSessionResult:
    """搜索会话结果。"""

    top_results: tuple[LoadoutScore, ...]
    total_combinations: int
    processed_combinations: int
    cancelled: bool
    warnings: tuple[str, ...]
    skipped_preprocessed: int = 0


def run_search_session(
    *,
    base_context: DamageContext,
    weapons: list[WeaponCandidate],
    equipment_catalog: dict[str, list[dict[str, Any]]],
    config: OptimizerConfig,
    max_workers: int = 1,
    cancel_token: Optional[SearchCancelToken] = None,
    progress_callback: Optional[Callable[[dict], None]] = None,
    db_path: Optional[Path] = None,
    run_signature: Optional[str] = None,
) -> SearchSessionResult:
    """
    执行单技能搜索。

    提供 db_path 与 run_signature 时走 SQLite 续跑；否则仅内存 TopN。
    """
    if db_path is not None and run_signature is not None:
        resume = execute_search_with_resume(
            db_path=Path(db_path),
            run_signature=str(run_signature),
            base_context=base_context,
            weapons=weapons,
            equipment_catalog=equipment_catalog,
            config=config,
            max_workers=max_workers,
            cancel_token=cancel_token,
            progress_callback=progress_callback,
        )
        return SearchSessionResult(
            top_results=resume.top_results,
            total_combinations=resume.total_combinations,
            processed_combinations=resume.processed_combinations,
            cancelled=resume.cancelled,
            warnings=(),
            skipped_preprocessed=resume.skipped_preprocessed,
        )

    tasks, total_combinations, _pruned, warnings = enumerate_optimizer_tasks(
        base_context=base_context,
        weapons=weapons,
        equipment_catalog=equipment_catalog,
        config=config,
    )
    if total_combinations == 0:
        return SearchSessionResult(
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
    return SearchSessionResult(
        top_results=top_results,
        total_combinations=total_combinations,
        processed_combinations=processed,
        cancelled=cancelled,
        warnings=warnings,
    )
