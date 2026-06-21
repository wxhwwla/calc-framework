#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""equipment 子包 — 装备数据链路、词条、显示修正与裁剪。"""

from . import affix as affix
from . import display_corrections as display_corrections
from . import prune as prune
from . import system as system

__all__ = [
    "affix",
    "display_corrections",
    "prune",
    "system",
]
