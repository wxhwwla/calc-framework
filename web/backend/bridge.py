# SPDX-License-Identifier: AGPL-3.0
"""Web 后端框架桥接层 — 统一导入 calc_framework 的入口。

所有 Web 后端模块应通过此模块访问 calc_framework，而非直接 import。
"""

from calc_framework.config.adapter import AdapterPackage
from calc_framework.config.manager import AdapterManager
from calc_framework.logging import get_logger, setup_logging

__all__ = [
    "AdapterManager",
    "AdapterPackage",
    "get_logger",
    "setup_logging",
]
