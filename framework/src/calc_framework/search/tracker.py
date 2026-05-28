"""Top-N 结果追踪器 — 保留评分最高的 N 条记录。"""

from __future__ import annotations

import heapq
from collections.abc import Callable
from typing import Generic, TypeVar

T = TypeVar("T")


class TopNTracker(Generic[T]):
    """按 key_fn 保留最大的 top_n 条记录。

    内部使用最小堆，空间 O(n)，插入 O(log n)。适合在遍历大量候选时
    只关心最优结果的场景（如配装搜索）。

    用法::

        tracker = TopNTracker(10, key_fn=lambda r: r.score)
        for item in all_candidates:
            tracker.offer(item)
        best = tracker.results()
    """

    def __init__(self, top_n: int, *, key_fn: Callable[[T], float]) -> None:
        self._top_n = max(1, int(top_n))
        self._key_fn = key_fn
        self._heap: list[tuple[float, int, T]] = []
        self._seq = 0

    def offer(self, item: T) -> None:
        score = float(self._key_fn(item))
        self._seq += 1
        entry = (score, self._seq, item)
        if len(self._heap) < self._top_n:
            heapq.heappush(self._heap, entry)
            return
        if score > self._heap[0][0]:
            heapq.heapreplace(self._heap, entry)

    @property
    def top_n(self) -> int:
        return self._top_n

    @property
    def count(self) -> int:
        return len(self._heap)

    def results(self) -> tuple[T, ...]:
        return tuple(item for _score, _seq, item in sorted(self._heap, reverse=True))
