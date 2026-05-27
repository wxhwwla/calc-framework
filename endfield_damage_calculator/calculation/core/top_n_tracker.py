#!/usr/bin/env python3
"""搜索过程中维护 TopN 结果（不保留全量得分）。"""

from __future__ import annotations

import heapq
from collections.abc import Callable
from typing import Generic, TypeVar

T = TypeVar("T")


class TopNTracker(Generic[T]):
    """按 key_fn 保留最大的 top_n 条记录。"""

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

    def results(self) -> tuple[T, ...]:
        return tuple(item for _score, _seq, item in sorted(self._heap, reverse=True))
