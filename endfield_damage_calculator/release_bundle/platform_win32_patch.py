#!/usr/bin/env python3
"""兼容 re-export：实现已迁至 ``utils.platform_win32_patch``。"""

from utils.platform_win32_patch import apply_platform_win32_patch

__all__ = ["apply_platform_win32_patch"]
