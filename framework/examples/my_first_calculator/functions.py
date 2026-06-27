# -*- coding: utf-8 -*-
"""自定义函数示例。"""


def clamp(value: float, min_val: float, max_val: float) -> float:
    """将值钳制在 [min_val, max_val] 范围内。

    Args:
        value: 输入值
        min_val: 最小值
        max_val: 最大值

    Returns:
        钳制后的值
    """
    return max(min_val, min(value, max_val))
