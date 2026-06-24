#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""
乘区快照计算：入口函数委托 DAG 引擎。
"""

from games.endfield.calc.zone_snapshot.types import (
    MultiplicativeZoneSelection,
    ZoneDisplayLine,
)


def compute_multiplicative_zone_snapshot(
    selection: MultiplicativeZoneSelection,
) -> list[ZoneDisplayLine]:
    """计算完整乘区展示行（不含 GUI 控件）。

    全部计算委托 DAG 引擎，不再调用旧引擎。
    """
    from games.endfield.calc.dag_adapter.adapter import compute_snapshot_with_dag

    return compute_snapshot_with_dag(selection)
