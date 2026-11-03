# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""adapter_creator — 兼容层，实际实现已迁移到 ``calc_framework.config.scaffold``。

该模块保留原有导入路径，供 GUI 与旧调用方继续使用。
新代码请直接 ``from calc_framework.config.scaffold import ...``。
"""

from __future__ import annotations

from calc_framework.config.scaffold import (
    AdapterScaffoldConfig,
    ScaffoldResult,
    scaffold_adapter_directory,
)

__all__ = [
    "AdapterScaffoldConfig",
    "ScaffoldResult",
    "scaffold_adapter_directory",
]
