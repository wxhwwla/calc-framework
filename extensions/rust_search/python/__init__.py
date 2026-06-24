# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""Rust 搜索加速桥接层。

提供 ``evaluate_search_damage`` 函数，与 Python 版 ``search_evaluate`` 接口完全一致。
Rust 扩展不可用时自动降级到 Python 版。
"""

from __future__ import annotations

from .rust_bridge import evaluate_search_damage

__all__ = ["evaluate_search_damage"]
