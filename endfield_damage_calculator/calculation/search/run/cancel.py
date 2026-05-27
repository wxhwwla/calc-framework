#!/usr/bin/env python3
"""搜索取消令牌。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SearchCancelToken:
    """搜索取消令牌。"""

    cancel_after: int | None = None
    _cancelled: bool = False

    def cancel(self) -> None:
        self._cancelled = True

    def should_cancel(self, processed_count: int) -> bool:
        if self._cancelled:
            return True
        return bool(self.cancel_after is not None and processed_count >= self.cancel_after)
