# SPDX-License-Identifier: AGPL-3.0
"""框架桥接入口 — 导入 calc-framework 核心模块。

集中管理框架依赖，方便在打包/重构时追踪所有框架引用。
"""

from __future__ import annotations

from calc_framework.logging import get_logger  # noqa: F401
from calc_framework.data.loader import DataContextLoader  # noqa: F401
from calc_framework.data.context import make_context  # noqa: F401
from calc_framework.config.adapter import AdapterPackage  # noqa: F401
