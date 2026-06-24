#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""全量遍历执行统一入口（内存 TopN 与 SQLite 续跑）。

``search_session.run_search_session`` 为实际实现；本模块提供稳定命名接缝。
``run_with_engine()`` 使用框架泛型 ``SearchEngine`` 接口（Phase 3 抽象）。
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from calc_framework.search import SearchConfig, SearchEngine
from calc_framework.search.result import SearchResult

from games.endfield.calc.damage.engine import DamageContext
from games.endfield.calc.loadout.optimizer import LoadoutScore, OptimizerConfig, OptimizerTask, WeaponCandidate

from ..evaluate.context import SearchEvalContext
from .cancel import SearchCancelToken
from .session import SearchSessionResult, run_search_session


class SearchRunner:
    """全量/MVP 搜索执行门面（深模块接口）。"""

    @staticmethod
    def run(
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
    ) -> SearchSessionResult:
        """执行全量搜索（委托 run_search_session）。"""
        return run_search_session(
            base_context=base_context,
            weapons=weapons,
            equipment_catalog=equipment_catalog,
            config=config,
            max_workers=max_workers,
            cancel_token=cancel_token,
            progress_callback=progress_callback,
            db_path=db_path,
            run_signature=run_signature,
            search_eval=search_eval,
            task_evaluator=task_evaluator,
            search_job=search_job,
        )

    @staticmethod
    def run_with_engine(
        engine: SearchEngine[OptimizerTask, LoadoutScore],
        *,
        top_n: int = 10,
        max_workers: int = 4,
        cancel_token: SearchCancelToken | None = None,
        progress_callback: Callable[[dict], None] | None = None,
    ) -> SearchResult[LoadoutScore]:
        """使用框架泛型 SearchEngine 执行搜索。

        示例::

            from games.endfield.calc.search.adapter import EndfieldSearchEngine
            from games.endfield.calc.search.run.runner import SearchRunner

            engine = EndfieldSearchEngine.from_job(job)
            result = SearchRunner.run_with_engine(
                engine, top_n=20, max_workers=4,
                progress_callback=my_progress_fn,
            )
        """

        config = SearchConfig(top_n=top_n, max_workers=max_workers)

        def _progress(p):
            """将框架进度回调转换为 GUI 兼容格式。"""
            if progress_callback is not None:
                progress_callback(
                    {
                        "processed": p.processed,
                        "total": p.total,
                        "speed_per_sec": p.processed / max(p.elapsed, 0.001),
                        "eta_seconds": p.estimated_remaining,
                    }
                )

        return engine.run(
            config=config,
            cancel_token=cancel_token,
            progress_callback=_progress if progress_callback else None,
        )
