# SPDX-License-Identifier: AGPL-3.0
"""动作RPG模板自定义函数。"""


def clamp(value: float, lo: float, hi: float) -> float:
    """钳制函数：限制 value 在 [lo, hi] 区间内。"""
    return max(lo, min(hi, value))


def lerp(a: float, b: float, t: float) -> float:
    """线性插值：a + (b - a) * t。"""
    return a + (b - a) * t
