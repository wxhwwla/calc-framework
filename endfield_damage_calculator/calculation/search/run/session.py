#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""单技能搜索会话：有界并行 + 可选 SQLite 续跑。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

from calculation.damage.engine import DamageContext
from calculation.loadout.in_memory_optimizer import run_enumerated_optimizer_parallel
from calculation.loadout.optimizer import (
    LoadoutScore,
    OptimizerConfig,
    OptimizerTask,
    WeaponCandidate,
)
from ..evaluate.context import SearchEvalContext
from .cancel import SearchCancelToken
from ..persist.store import execute_search_with_resume


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
    search_eval: Optional[SearchEvalContext] = None,
    task_evaluator: Optional[Callable[[OptimizerTask], LoadoutScore]] = None,
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
            search_eval=search_eval,
            task_evaluator=task_evaluator,
        )
        return SearchSessionResult(
            top_results=resume.top_results,
            total_combinations=resume.total_combinations,
            processed_combinations=resume.processed_combinations,
            cancelled=resume.cancelled,
            warnings=(),
            skipped_preprocessed=resume.skipped_preprocessed,
        )

    top_results, total_combinations, processed, cancelled, warnings = (
        run_enumerated_optimizer_parallel(
            base_context=base_context,
            weapons=weapons,
            equipment_catalog=equipment_catalog,
            config=config,
            max_workers=max_workers,
            cancel_token=cancel_token,
            progress_callback=progress_callback,
            search_eval=search_eval,
            task_evaluator=task_evaluator,
        )
    )
    return SearchSessionResult(
        top_results=top_results,
        total_combinations=total_combinations,
        processed_combinations=processed,
        cancelled=cancelled,
        warnings=warnings,
    )
