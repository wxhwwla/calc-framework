#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""主窗口尺寸与启动全屏（最大化）。"""

from __future__ import annotations

import sys
from typing import Any

from calc_framework.logging import get_logger

_logger = get_logger(__name__)


def apply_startup_maximized(window: Any) -> None:
    """

    启动后将主窗口最大化（Windows 为 zoomed，其它平台尽量铺满工作区）。



    在 mainloop 前调用；内部用 after_idle 等待窗口完成初次布局。

    """

    def _apply() -> None:
        window.update_idletasks()

        if _try_zoomed_state(window):
            return

        if _try_zoomed_attribute(window):
            return

        _geometry_fill_screen(window)

    try:
        window.after_idle(_apply)
    except Exception:
        _logger.warning("apply_startup_maximized fallback", exc_info=True)
        _apply()


def _try_zoomed_state(window: Any) -> bool:
    try:
        window.state("zoomed")

        return True

    except Exception:
        return False


def _try_zoomed_attribute(window: Any) -> bool:
    try:
        window.attributes("-zoomed", True)
        return True
    except Exception:
        _logger.debug("zoomed attribute not supported")
        return False


def _geometry_fill_screen(window: Any) -> None:
    try:
        width = int(window.winfo_screenwidth())
        height = int(window.winfo_screenheight())
    except Exception:
        _logger.debug("winfo_screenwidth/height not available")
        return

    if width < 400 or height < 300:
        return

    # 非 Windows 有时任务栏占一条边，略留边距

    margin = 0 if sys.platform == "win32" else 32

    window.geometry(f"{max(400, width - margin)}x{max(300, height - margin)}+0+0")
