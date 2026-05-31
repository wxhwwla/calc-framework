# SPDX-License-Identifier: AGPL-3.0
"""卡牌RPG适配器 — DAG 表达式自定义函数。"""


def clamp(value: float, min_val: float, max_val: float) -> float:
    """将 value 约束在 [min_val, max_val] 区间内。"""
    return max(min_val, min(max_val, value))
