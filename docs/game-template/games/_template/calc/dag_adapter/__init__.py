# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""TEMPLATE（{Game}）DAG 适配器 — 数据加载与 DAG 计算入口。

替换说明：
  - {Game}ContextLoader → YourGameContextLoader
  - compute_snapshot_with_dag 函数名可按游戏习惯调整
"""

from __future__ import annotations

from .adapter import compute_snapshot_with_dag
from .loader import TEMPLATEContextLoader

__all__ = [
    "TEMPLATEContextLoader",
    "compute_snapshot_with_dag",
]
