#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""并行搜索执行器。"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Callable, Optional

from calculation.damage_engine import DamageContext
from calculation.loadout_optimizer import (
    LoadoutScore,
    OptimizerConfig,
    enumerate_optimizer_tasks,
    evaluate_task,
)


@dataclass
class SearchCancelToken:
    """搜索取消令牌。"""

    cancel_after: Optional[int] = None
    _cancelled: bool = False

    def cancel(self) -> None:
        self._cancelled = True

    def should_cancel(self, processed_count: int) -> bool:
        if self._cancelled:
            return True
        if self.cancel_after is not None and processed_count >= self.cancel_after:
            return True
        return False


@dataclass(frozen=True)
class ParallelSearchResult:
    """并行搜索结果。"""

    top_results: tuple[LoadoutScore, ...]
    total_combinations: int
    processed_combinations: int
    cancelled: bool
    warnings: tuple[str, ...]


def _top_n(scores: list[LoadoutScore], top_n: int) -> tuple[LoadoutScore, ...]:
    return tuple(sorted(scores, key=lambda s: s.final_damage, reverse=True)[: max(1, top_n)])


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

    token = cancel_token or SearchCancelToken()
    started_at = time.perf_counter()
    processed = 0
    cancelled = False
    scores: list[LoadoutScore] = []
    with ThreadPoolExecutor(max_workers=max(1, int(max_workers))) as executor:
        futures = {
            executor.submit(
                evaluate_task,
                base_context=base_context,
                crit_mode=config.crit_mode,
                task=task,
            ): task
            for task in tasks
        }
        for future in as_completed(futures):
            if token.should_cancel(processed):
                cancelled = True
                for pending in futures:
                    pending.cancel()
                break
            try:
                score = future.result()
            except Exception:
                continue
            scores.append(score)
            processed += 1
            elapsed = max(1e-6, time.perf_counter() - started_at)
            speed = processed / elapsed
            remain = max(0, total_combinations - processed)
            eta = remain / speed if speed > 0 else 0.0
            if progress_callback:
                progress_callback(
                    {
                        "processed": processed,
                        "total": total_combinations,
                        "speed_per_sec": speed,
                        "eta_seconds": eta,
                    }
                )

    return ParallelSearchResult(
        top_results=_top_n(scores, config.top_n),
        total_combinations=total_combinations,
        processed_combinations=processed,
        cancelled=cancelled,
        warnings=warnings,
    )
