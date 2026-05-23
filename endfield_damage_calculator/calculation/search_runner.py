#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""并行搜索执行器（无续跑）；续跑请用 search_session。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from calculation.damage_engine import DamageContext
from calculation.loadout_optimizer import LoadoutScore, OptimizerConfig, WeaponCandidate
from calculation.search_cancel import SearchCancelToken
from calculation.search_session import SearchSessionResult, run_search_session

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
    weapons: list[WeaponCandidate],
    equipment_catalog,
    config: OptimizerConfig,
    max_workers: int = 1,
    cancel_token: Optional[SearchCancelToken] = None,
    progress_callback: Optional[Callable[[dict], None]] = None,
) -> ParallelSearchResult:
    """并行执行单技能搜索（无 SQLite 续跑）。"""
    session = run_search_session(
        base_context=base_context,
        weapons=weapons,
        equipment_catalog=equipment_catalog,
        config=config,
        max_workers=max_workers,
        cancel_token=cancel_token,
        progress_callback=progress_callback,
    )
    return _session_to_parallel(session)


def _session_to_parallel(session: SearchSessionResult) -> ParallelSearchResult:
    return ParallelSearchResult(
        top_results=session.top_results,
        total_combinations=session.total_combinations,
        processed_combinations=session.processed_combinations,
        cancelled=session.cancelled,
        warnings=session.warnings,
    )
