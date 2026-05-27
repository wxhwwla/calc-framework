#!/usr/bin/env python3
"""
全量遍历执行统一入口（内存 TopN 与 SQLite 续跑）。

``search_session.run_search_session`` 为实际实现；本模块提供稳定命名接缝。
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from calculation.damage.engine import DamageContext
from calculation.loadout.optimizer import LoadoutScore, OptimizerConfig, OptimizerTask, WeaponCandidate

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
    ) -> SearchSessionResult:
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
        )
