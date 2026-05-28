#!/usr/bin/env python3
"""搜索取消令牌 — 向后兼容重导出。

实际实现在 ``calc_framework.search.SearchCancelToken``。
"""

from __future__ import annotations

from calc_framework.search import SearchCancelToken  # noqa: F401

__all__ = ["SearchCancelToken"]
