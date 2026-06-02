# SPDX-License-Identifier: AGPL-3.0
"""搜索取消令牌 — 支持超时取消和主动取消。"""

from __future__ import annotations

from dataclasses import dataclass


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
        return self._cancelled

    def should_cancel(self, processed_count: int) -> bool:
        if self._cancelled:
            return True
        if self.cancel_after is not None and processed_count >= self.cancel_after:
            self._cancelled = True
            return True
        return False
