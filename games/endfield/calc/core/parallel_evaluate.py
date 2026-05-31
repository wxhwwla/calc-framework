#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""使用 concurrent.futures 并行评估多条配装方案（与全量搜索线程池语义一致）。"""

from __future__ import annotationsfrom collections.abc import Callable, Sequencefrom concurrent.futures import ThreadPoolExecutorfrom typing import TypeVarfrom games.endfield.calc.loadout.optimizer import OptimizerTaskT = TypeVar("T")
U = TypeVar("U")


def evaluate_parallel(
    items: Sequence[T],
    evaluator: Callable[[T], U],
    *,
    max_workers: int = 1,
) -> list[U]:
    """
    并行调用 evaluator，返回与 items 同序的结果列表。

    max_workers<=1 时串行执行，便于单测与调试。
    """
    if not items:
        return []
    workers = max(1, int(max_workers))
    if workers == 1:
        return [evaluator(item) for item in items]

    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(evaluator, items, chunksize=max(1, len(items) // workers)))


def evaluate_tasks_parallel(
    tasks: Sequence[OptimizerTask],
    evaluator: Callable[[OptimizerTask], T],
    *,
    max_workers: int = 1,
) -> list[T]:
    """并行评估配装任务（``evaluate_parallel`` 的 OptimizerTask 特化别名）。"""
    return evaluate_parallel(tasks, evaluator, max_workers=max_workers)
