# SPDX-License-Identifier: AGPL-3.0
"""框架桥接层 — GUI 只通过此模块导入 calc_framework。

集中所有框架依赖引用，使 GUI 层不再直接依赖 calc_framework.*。
当框架 API 变化时，只需修改此桥接层，无需逐文件更新 GUI。
"""

from calc_framework.config.adapter import AdapterPackage
from calc_framework.logging import get_logger, setup_logging
from calc_framework.ui.compute_sheet import ComputeSheet
from calc_framework.ui.layout import load_layout_json

__all__ = [
    "AdapterPackage",
    "ComputeSheet",
    "get_logger",
    "load_layout_json",
    "setup_logging",
]
