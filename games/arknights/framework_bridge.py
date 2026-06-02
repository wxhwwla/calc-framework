# SPDX-License-Identifier: AGPL-3.0
"""框架桥接层 — GUI 只通过此模块导入 calc_framework。

框架-游戏桥接规范（ADR-0023）：每个游戏包必须有一个 framework_bridge.py，
集中管理所有 calc_framework 导入，使 GUI 层与框架解耦。
"""

from calc_framework.config.adapter import AdapterPackage
from calc_framework.logging import get_logger
from calc_framework.ui.compute_sheet import ComputeSheet
from calc_framework.ui.layout import load_layout_json

__all__ = [
    "AdapterPackage",
    "ComputeSheet",
    "get_logger",
    "load_layout_json",
]
