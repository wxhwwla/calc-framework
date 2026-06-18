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


# from cancel.py
@dataclass
class SearchCancelToken:
    """搜索取消令牌，可检查是否已取消或超量。

    用法::

        cancel = SearchCancelToken(cancel_after=5000)

        for i, item in enumerate(items):

            if cancel.should_cancel(i):

                break

            process(item)



        # 主动取消

        cancel.cancel()

    """

    cancel_after: int | None = None
    _cancelled: bool = False

    def cancel(self) -> None:
        self._cancelled = True

    @property
    def is_cancelled(self) -> bool:
        """is_cancelled。"""
        return self._cancelled

    def should_cancel(self, processed_count: int) -> bool:
        if self._cancelled:
            return True
        if self.cancel_after is not None and processed_count >= self.cancel_after:
            self._cancelled = True
            return True
        return False
