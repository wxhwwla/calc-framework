#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""最近计算历史（内存环形缓冲，供侧边栏恢复参数）。"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class HistoryEntry:
    """单条历史：展示文案 + 可恢复的预设快照。"""

    label: str
    summary: str
    preset_snapshot: dict[str, Any]


class CalculationHistory:
    """保留最近 N 次计算记录（默认 10）。"""

    def __init__(self, *, max_entries: int = 10) -> None:
        self._max = max(1, int(max_entries))
        self._entries: deque[HistoryEntry] = deque(maxlen=self._max)

    def push(self, entry: HistoryEntry) -> None:
        self._entries.append(entry)

    def list_entries(self) -> tuple[HistoryEntry, ...]:
        return tuple(reversed(self._entries))

    def get_snapshot(self, index: int) -> dict[str, Any] | None:
        """index 0 为最新一条。"""
        items = self.list_entries()
        if index < 0 or index >= len(items):
            return None
        return dict(items[index].preset_snapshot)


def get_app_calculation_history(app: Any) -> CalculationHistory:
    """从 app 实例获取/创建 CalculationHistory。"""
    history = getattr(app, "_calc_history", None)
    if history is None:
        history = CalculationHistory(max_entries=10)
        app._calc_history = history
    return history
