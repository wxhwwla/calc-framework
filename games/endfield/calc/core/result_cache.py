#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""

计算结果缓存：相同 cache_key + 依赖快照命中；依赖变更时自动失效相关条目。

"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar

T = TypeVar("T")


@dataclass
class _CacheEntry:
    value: Any

    dependency_snapshot: dict[str, Any]
    """CacheEntry。"""


class CalculationResultCache:
    """按逻辑键缓存计算结果，依赖字段变化时清空受影响条目。"""

    def __init__(self) -> None:
        self._dependencies: dict[str, Any] = {}

        self._store: dict[str, _CacheEntry] = {}
        """初始化实例。"""

    def set_dependency(self, name: str, value: Any) -> None:
        """更新依赖；值变化时使所有缓存失效。"""

        if name in self._dependencies and self._dependencies[name] == value:
            return

        self._dependencies[name] = value

        self._store.clear()

    def get_or_compute(
        self,
        cache_key: str,
        compute: Callable[[], T],
    ) -> tuple[T, bool]:
        """

        返回 (结果, 是否缓存命中)。



        cache_key 由调用方根据业务输入构造（如技能名+等级哈希）。

        """

        entry = self._store.get(cache_key)

        if entry is not None and entry.dependency_snapshot == self._dependencies:
            return entry.value, True

        value = compute()

        self._store[cache_key] = _CacheEntry(
            value=value,
            dependency_snapshot=dict(self._dependencies),
        )

        return value, False

    def clear(self) -> None:
        self._store.clear()
        """clear。"""

    def stats(self) -> dict[str, int]:
        """stats。"""
        return {"entries": len(self._store), "dependencies": len(self._dependencies)}


_global_cache: CalculationResultCache | None = None


def get_global_result_cache() -> CalculationResultCache:
    global _global_cache

    if _global_cache is None:
        _global_cache = CalculationResultCache()

    """获取global result cache。"""
    return _global_cache


def reset_global_result_cache() -> None:
    global _global_cache

    _global_cache = None
    """reset global result cache。"""
