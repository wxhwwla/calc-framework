#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""
damage 子包 — 伤害计算与公式相关模块。

公开以下子模块为模块对象，可通过 ``damage.formula``、``damage.types`` 等方式访问。
子模块采用延迟加载（``__getattr__``），避免 ``data_loading`` ↔ ``calc.core`` 之间的循环导入。
"""

from __future__ import annotations

import importlib
import sys
from typing import Any


def __getattr__(name: str) -> Any:
    """延迟加载子模块，避免包级循环导入。"""
    if name in _MODULES:
        full_name = f"{__name__}.{name}"
        if full_name not in sys.modules:
            importlib.import_module(full_name)
        return sys.modules[full_name]
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)


_MODULES = [
    "abnormal_attached",
    "break_defense",
    "combat_resources",
    "combo_bonus",
    "corrosion",
    "enemy_growth",
    "execute",
    "formula",
    "healing",
    "imbalance",
    "incoming",
    "originium_arts",
    "physical_abnormal_state",
    "special_damage",
    "types",
]

__all__ = list(_MODULES)
