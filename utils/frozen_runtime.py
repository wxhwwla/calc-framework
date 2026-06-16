# SPDX-License-Identifier: AGPL-3.0
"""PyInstaller 冻结 exe 运行时安全默认值（须在 rust_bridge / evaluate 导入前调用）。"""

from __future__ import annotations

import os
import sys


def apply_frozen_runtime_defaults() -> bool:
    """设置打包 exe 下的安全默认环境变量。返回是否处于 frozen 模式。"""
    frozen = bool(getattr(sys, "frozen", False))
    if not frozen:
        return False
    # native rust_search.pyd 在 onefile 下调用易 segfault
    os.environ.setdefault("RUST_SEARCH_FALLBACK", "1")
    os.environ.setdefault("CALC_SEARCH_LOG_LEVEL", "DEBUG")
    return True


def is_frozen_exe() -> bool:
    """是否 PyInstaller 冻结 exe。"""
    return bool(getattr(sys, "frozen", False))


def use_rust_search_accel() -> bool:
    """是否允许加载/调用 Rust 搜索加速（frozen 恒为 False）。"""
    if is_frozen_exe():
        return False
    return os.environ.get("RUST_SEARCH_FALLBACK", "").strip() not in ("1", "true", "yes")
