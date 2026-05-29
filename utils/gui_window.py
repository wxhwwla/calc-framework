#!/usr/bin/env python3
"""主窗口尺寸与启动全屏（最大化）。"""

from __future__ import annotations

import sys
from typing import Any


def apply_startup_maximized(window: Any) -> None:
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
        return False


def _geometry_fill_screen(window: Any) -> None:
    try:
        width = int(window.winfo_screenwidth())
        height = int(window.winfo_screenheight())
    except Exception:
        return
    if width < 400 or height < 300:
        return
    margin = 0 if sys.platform == "win32" else 32
    window.geometry(f"{max(400, width - margin)}x{max(300, height - margin)}+0+0")
