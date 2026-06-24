# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""DAG 自定义函数 — DAG 表达式中通过 expr 节点调用的纯函数。

所有顶层函数通过函数名自动注册到 DAG 沙箱。
"""

from __future__ import annotations


def clamp(value: float, min_val: float, max_val: float) -> float:
    """将 value 约束在 [min_val, max_val] 区间内。"""
    return max(min_val, min(max_val, value))


def lerp(a: float, b: float, t: float) -> float:
    """线性插值：a + (b - a) * t"""
    return a + (b - a) * t
