#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""搜索过程中维护 TopN 结果 — 向后兼容重导出。



实际实现在 ``calc_framework.search.TopNTracker``。

"""

from __future__ import annotations

from calc_framework.search import TopNTracker

__all__ = ["TopNTracker"]
