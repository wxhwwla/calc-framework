#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""loadout 子包 — 配装搜索、内存优化与攻击力求值。

子模块采用延迟加载（``__getattr__``），避免与 ``loadout.optimizer`` 内部的循环导入。
"""

from __future__ import annotations

import importlib
import sys
from typing import Any


def __getattr__(name: str) -> Any:
    """延迟加载子模块。"""
    if name in _MODULES:
        full_name = f"{__name__}.{name}"
        if full_name not in sys.modules:
            importlib.import_module(full_name)
        return sys.modules[full_name]
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)


_MODULES = [
    "attack_eval",
    "in_memory_optimizer",
    "slot_search",
]

__all__ = list(_MODULES)
