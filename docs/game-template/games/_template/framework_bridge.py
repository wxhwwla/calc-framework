# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""框架桥接入口 — 导入 calc-framework 核心模块。

集中管理框架依赖，方便在打包/重构时追踪所有框架引用。
GUI 层只通过此模块间接访问框架，不直接 from calc_framework。
"""

from __future__ import annotations

from calc_framework.config.adapter import AdapterPackage
from calc_framework.data.context import make_context
from calc_framework.data.loader import DataContextLoader
from calc_framework.logging import get_logger
from calc_framework.ui.compute_sheet import ComputeSheet
from calc_framework.ui.layout import load_layout_json

__all__ = [
    "AdapterPackage",
    "ComputeSheet",
    "DataContextLoader",
    "get_logger",
    "load_layout_json",
    "make_context",
]
