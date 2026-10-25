# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""开发者工具箱 — 统一入口，整合所有框架开发工具。"""

from __future__ import annotations

__all__: list[str] = [
    "DevToolkitWindow",
    "main",
]

from . import pages  # type: ignore[unused-import]
from .main_window import DevToolkitWindow, main
