#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""搜索取消令牌。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


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
