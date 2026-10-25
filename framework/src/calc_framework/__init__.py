#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""通用游戏数值计算框架。

提供游戏无关的 DAG 公式引擎、搜索/枚举引擎、声明式 UI、适配器管理
及图编辑器等核心模块。每款游戏以「适配器包」形式接入。

用法::

    from calc_framework import setup_logging, get_logger
    from calc_framework.dag import DAGService, DAGGraph
    from calc_framework.config import AdapterManager

    setup_logging()
    mgr = AdapterManager()
    adapter = mgr.load("endfield")
    result = adapter.dag_service.evaluate(context)
"""

from calc_framework.errors import CalcFrameworkError
from calc_framework.logging import get_logger, set_level, setup_logging

__all__ = [
    "CalcFrameworkError",
    "get_logger",
    "set_level",
    "setup_logging",
]
