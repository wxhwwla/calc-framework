# SPDX-License-Identifier: AGPL-3.0
"""单技能搜索会话 — 委托框架 SearchSession。

``run_search_session`` 将终末地特有输入转换为 ``EndfieldSearchEngine``，
通过框架 ``SearchSession`` 执行搜索，支持内存 TopN 和 SQLite 续跑。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from calc_framework.search import SearchConfig, SearchResult, SearchSession

from games.endfield.calc.damage.engine import DamageContext
from games.endfield.calc.loadout.optimizer import (
    LoadoutScore,
    OptimizerConfig,
    OptimizerTask,
    WeaponCandidate,
)

from ..adapter import EndfieldSearchEngine
from ..evaluate.context import SearchEvalContext
from ..persist.store import SearchRunStore
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


def _build_engine(
    *,
    base_context: DamageContext,
    weapons: list[WeaponCandidate],
    equipment_catalog: dict[str, list[dict[str, Any]]],
    config: OptimizerConfig,
    search_eval: SearchEvalContext | None = None,
    task_evaluator: Callable[[OptimizerTask], LoadoutScore] | None = None,
) -> EndfieldSearchEngine:
    return EndfieldSearchEngine(
        base_context=base_context,
        weapons=weapons,
        equipment_catalog=equipment_catalog,
        config=config,
        search_eval=search_eval,
        task_evaluator=task_evaluator,
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
) -> SearchSessionResult:
    """
    执行单技能搜索。

    提供 db_path 与 run_signature 时走 SQLite 续跑；否则仅内存 TopN。
    内部使用框架 ``SearchSession`` + ``EndfieldSearchEngine`` 执行。
    """
    engine = _build_engine(
        base_context=base_context,
        weapons=weapons,
        equipment_catalog=equipment_catalog,
        config=config,
        search_eval=search_eval,
        task_evaluator=task_evaluator,
    )

    progress_adapter: Any = _build_progress_adapter(progress_callback)

    if db_path is not None and run_signature is not None:
        return _run_with_persist(
            engine=engine,
            config=config,
            max_workers=max_workers,
            cancel_token=cancel_token,
            progress_callback=progress_adapter,
            db_path=db_path,
            run_signature=run_signature,
        )

    return _run_in_memory(
        engine=engine,
        config=config,
        max_workers=max_workers,
        cancel_token=cancel_token,
        progress_callback=progress_adapter,
    )


def _build_progress_adapter(
    progress_callback: Callable[[dict], None] | None,
) -> Any:
    """将框架 ParallelProgress 回调适配为端侧 dict 回调。"""
    if progress_callback is None:
        return None

    def _adapter(p: Any) -> None:
        if hasattr(p, "processed"):
            progress_callback({
                "processed": p.processed,
                "total": p.total,
                "speed_per_sec": p.processed / max(getattr(p, "elapsed", 0.001), 0.001),
                "eta_seconds": getattr(p, "estimated_remaining", 0.0),
            })
        else:
            progress_callback(dict(p))

    return _adapter


def _run_in_memory(
    *,
    engine: EndfieldSearchEngine,
    config: OptimizerConfig,
    max_workers: int,
    cancel_token: SearchCancelToken | None,
    progress_callback: Any | None,
) -> SearchSessionResult:
    """内存 TopN 搜索（无 SQLite 续跑）。"""
    cfg = SearchConfig(top_n=config.top_n, max_workers=max_workers)
    session = SearchSession(engine)
    result = session.run(cfg, cancel_token=cancel_token, progress_callback=progress_callback)
    cancelled = bool(result.metadata.get("cancelled", False))
    return SearchSessionResult(
        top_results=tuple(result.items) if result.items else (),
        total_combinations=result.total_candidates,
        processed_combinations=result.total_evaluated,
        cancelled=cancelled,
        warnings=(),
    )


def _run_with_persist(
    *,
    engine: EndfieldSearchEngine,
    config: OptimizerConfig,
    max_workers: int,
    cancel_token: SearchCancelToken | None,
    progress_callback: Any | None,
    db_path: Path,
    run_signature: str,
) -> SearchSessionResult:
    """SQLite 续跑搜索。"""
    store = SearchRunStore(db_path)
    cfg = SearchConfig(top_n=config.top_n, max_workers=max_workers)
    session = SearchSession(engine, store=store)
    result = session.run(
        cfg,
        cancel_token=cancel_token,
        progress_callback=progress_callback,
        run_signature=run_signature,
    )
    cancelled = bool(result.metadata.get("cancelled", False))
    skipped_preprocessed = int(result.metadata.get("skipped_preprocessed", 0))

    top_scores: tuple[LoadoutScore, ...] = tuple(result.items) if result.items else ()
    if top_scores:
        store.replace_top_scores(run_signature, top_scores)

    return SearchSessionResult(
        top_results=top_scores,
        total_combinations=result.total_candidates,
        processed_combinations=result.total_evaluated,
        cancelled=cancelled,
        warnings=(),
        skipped_preprocessed=skipped_preprocessed,
    )
