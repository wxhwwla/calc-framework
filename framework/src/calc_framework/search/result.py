# SPDX-License-Identifier: AGPL-3.0
"""通用搜索结果类型。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

T = TypeVar("T")


@dataclass
class SearchResult(Generic[T]):
    """一次搜索/枚举会话的结果。

    ``items`` 为具体结果类型（如 LoadoutScore）的元组，
    游戏适配器可继承或包装此类型添加专属字段。
    """

    items: tuple[T, ...] = field(default_factory=tuple)
    total_evaluated: int = 0
    total_candidates: int = 0
    elapsed_seconds: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParallelProgress:
    """并行执行的进度信息。"""

    processed: int = 0
    total: int = 0
    elapsed: float = 0.0
    estimated_remaining: float = 0.0
