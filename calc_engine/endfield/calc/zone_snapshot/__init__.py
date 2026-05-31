#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""
乘区快照：生产入口与展示类型。

拆分自 ``multiplicative_zones.zone_snapshot``，消除与 ``dag_adapter/`` 之间的包级循环。
"""

from calc_engine.endfield.calc.zone_snapshot.compute import compute_multiplicative_zone_snapshot
from calc_engine.endfield.calc.zone_snapshot.types import (
    MultiplicativeZoneSelection,
    WeaponBonusSelection,
    ZoneDisplayLine,
)

__all__ = [
    "MultiplicativeZoneSelection",
    "WeaponBonusSelection",
    "ZoneDisplayLine",
    "compute_multiplicative_zone_snapshot",
]
