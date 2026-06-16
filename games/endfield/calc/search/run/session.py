# SPDX-License-Identifier: AGPL-3.0
"""单技能搜索会话 — 流式任务 + 有界并行（线程/多进程）。"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from calc_framework.search import SearchResult

from games.endfield.calc.damage.engine import DamageContext
from games.endfield.calc.loadout.in_memory_optimizer import run_enumerated_optimizer_parallel
from games.endfield.calc.loadout.optimizer import (
    LoadoutScore,
    OptimizerConfig,
    OptimizerTask,
    WeaponCandidate,
)
from games.endfield.calc.search.run.parallel import ParallelBackend

from ..evaluate.context import SearchEvalContext
from ..persist.store import execute_search_with_resume
from .cancel import SearchCancelToken


@dataclass(frozen=True)
class SearchSessionResult:
    """搜索会话结果。"""

    top_results: tuple[LoadoutScore, ...]
    total_combinations: int
    processed_combinations: int
    cancelled: bool
    warnings: tuple[str, ...]
    skipped_preprocessed: int = 0

    def to_search_result(self) -> SearchResult:
        """转换为框架通用 SearchResult。"""
        return SearchResult(
            items=self.top_results,
            total_evaluated=self.processed_combinations,
            total_candidates=self.total_combinations,
            metadata={
                "cancelled": self.cancelled,
                "warnings": self.warnings,
                "skipped_preprocessed": self.skipped_preprocessed,
            },
        )


def run_search_session(
    *,
    base_context: DamageContext,
    weapons: list[WeaponCandidate],
    equipment_catalog: dict[str, list[dict[str, Any]]],
    config: OptimizerConfig,
    max_workers: int = 1,
    cancel_token: SearchCancelToken | None = None,
    progress_callback: Callable[[dict], None] | None = None,
    db_path: Path | None = None,
    run_signature: str | None = None,
    search_eval: SearchEvalContext | None = None,
    task_evaluator: Callable[[OptimizerTask], LoadoutScore] | None = None,
    search_job: Any | None = None,
    parallel_backend: ParallelBackend = "auto",
) -> SearchSessionResult:
    """执行单技能搜索。

    提供 db_path 与 run_signature 时走 SQLite 续跑（流式 + 有界并行）；
    否则仅内存 TopN。默认 ``parallel_backend=auto`` 在多 worker 时用多进程。
    """
    if db_path is not None and run_signature is not None:
        resume = execute_search_with_resume(
            db_path=db_path,
            run_signature=run_signature,
            base_context=base_context,
            weapons=weapons,
            equipment_catalog=equipment_catalog,
            config=config,
            max_workers=max_workers,
            cancel_token=cancel_token,
            progress_callback=progress_callback,
            search_eval=search_eval,
            task_evaluator=task_evaluator,
            search_job=search_job,
            parallel_backend=parallel_backend,
        )
        return SearchSessionResult(
            top_results=resume.top_results,
            total_combinations=resume.total_combinations,
            processed_combinations=resume.processed_combinations,
            cancelled=resume.cancelled,
            warnings=(),
            skipped_preprocessed=resume.skipped_preprocessed,
        )

    top_results, total, processed, cancelled, warnings = run_enumerated_optimizer_parallel(
        base_context=base_context,
        weapons=weapons,
        equipment_catalog=equipment_catalog,
        config=config,
        max_workers=max_workers,
        cancel_token=cancel_token,
        progress_callback=progress_callback,
        search_eval=search_eval,
        task_evaluator=task_evaluator,
        search_job=search_job,
        parallel_backend=parallel_backend,
    )
    return SearchSessionResult(
        top_results=top_results,
        total_combinations=total,
        processed_combinations=processed,
        cancelled=cancelled,
        warnings=warnings,
    )
