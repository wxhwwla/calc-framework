#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全量遍历执行统一入口（内存 TopN 与 SQLite 续跑）。

``search_session.run_search_session`` 为实际实现；本模块提供稳定命名接缝。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Optional

from calculation.damage_engine import DamageContext
from calculation.loadout_optimizer import LoadoutScore, OptimizerConfig, OptimizerTask, WeaponCandidate
from .run_cancel import SearchCancelToken
from .evaluate_context import SearchEvalContext
from .run_session import SearchSessionResult, run_search_session


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
        cancel_token: Optional[SearchCancelToken] = None,
        progress_callback: Optional[Callable[[dict], None]] = None,
        db_path: Optional[Path] = None,
        run_signature: Optional[str] = None,
        search_eval: Optional[SearchEvalContext] = None,
        task_evaluator: Optional[Callable[[OptimizerTask], LoadoutScore]] = None,
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
