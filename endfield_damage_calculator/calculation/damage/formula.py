#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公式计算引擎

提供通用的成长曲线计算工具函数。

属性成长公式说明：
    基础公式（1-90级）：base + floor((growth * (lv - 1) + offset) / divisor)
    特殊公式（10-12级）：可配置固定值或继续使用基础公式

数据范围：
    - levels: 等级 1-90
    - talent: 潜能/精炼等级 0-5
    - trust: 信赖等级 0-4
"""

import math
from typing import List


# ==================== 通用常量 ====================

# 等级列表（1-90级）
levels = list(range(1, 91))

# 潜能/精炼等级列表（0-5级）
talent = list(range(0, 6))

# 信赖等级列表（0-4级）
trust = list(range(0, 5))

# 信赖加成列表（0-4级）
trust_add = [0, 10, 15, 15, 20]


def has_fractional_part(value: int | float) -> bool:
    """真小数（如 5.4、23.4）；整数值的 float（如 10.0）不算。"""
    return isinstance(value, float) and value != int(value)


def infer_decimal_mode(
    base: int | float,
    growth: int | float,
    divisor: int | float,
    offset: int | float = 0,
    *,
    special: List[float | int] | None = None,
    is_decimal: bool | None = None,
) -> bool:
    """
    是否启用「×10 → floor → ÷10」小数取整。

    - 曲线/参数含真小数（如 5.4、special 里 23.4）→ 小数模式
    - 纯整数或 10.0 这类整型 float → 直接 floor
    - 可显式传入 is_decimal 覆盖自动判断
    """
    if is_decimal is not None:
        return is_decimal
    for value in (base, growth, divisor, offset):
        if has_fractional_part(value):
            return True
    if special:
        return any(has_fractional_part(x) for x in special)
    return False


# ==================== 通用成长曲线计算器 ====================

def calculate_growth_curve(
    base: float | int,
    growth: float | int,
    divisor: float | int,
    offset: float | int = 0,
    max_level: int = 90
) -> List[float]:
    """
    计算属性成长曲线（通用公式）

    参数：
        base: 1级时的基础值（支持整数和小数）
        growth: 成长系数（支持整数和小数）
        divisor: 除数（用于控制成长速度，支持整数和小数）
        offset: 偏移量（微调成长曲线，支持整数和小数）
        max_level: 最大等级（默认90）

    公式：round(base + math.floor((growth * (lv - 1) + offset) / divisor), 1)

    返回：
        各等级属性值列表（索引0对应等级1，保留一位小数）

    异常：
        ValueError: 当divisor <= 0 或 max_level < 1时抛出
    """
    if divisor <= 0:
        raise ValueError("除数必须大于0")
    if max_level < 1:
        raise ValueError("最大等级必须大于等于1")

    return [
        round(base + math.floor((growth * (lv - 1) + offset) / divisor), 1)
        for lv in range(1, max_level + 1)
    ]


def calculate_skill_curve(
    base: float | int,
    growth: float | int,
    divisor: float | int,
    offset: float | int = 0,
    special_values: List[float | int] | None = None,
    use_floor: bool = True,
    is_decimal: bool | None = None
) -> List[float]:
    """
    计算技能倍率成长曲线（支持特殊值）

    数据处理规则：
    - 整数数据：直接按公式计算
    - 小数数据：乘10→整数计算→除10

    参数：
        base: 1级时的基础值（支持整数和小数）
        growth: 成长系数（支持整数和小数）
        divisor: 除数（支持整数和小数）
        offset: 偏移量（支持整数和小数）
        special_values: 特殊值列表（9级或10-12级，支持整数和小数）
        use_floor: 是否使用floor函数（True:整数数据，False:小数数据）
        is_decimal: 是否为小数数据（None表示自动检测）

    返回：
        各等级技能倍率列表（共12个值，索引0对应等级1，保留一位小数）

    异常：
        ValueError: 当divisor <= 0时抛出
    """
    if divisor <= 0:
        raise ValueError("除数必须大于0")

    if is_decimal is None:
        is_decimal = infer_decimal_mode(
            base, growth, divisor, offset, special=special_values
        )
    
    # 小数数据：乘10处理
    scale_factor = 10 if is_decimal else 1
    scaled_base = base * scale_factor
    scaled_growth = growth * scale_factor
    scaled_offset = offset * scale_factor

    curve = []
    
    # 1-9级使用公式计算
    for lv in range(1, 10):
        # 统一使用整数计算逻辑（floor）
        calculated = scaled_base + math.floor((scaled_growth * (lv - 1) + scaled_offset) / divisor)
        
        # 如果有特殊值且当前等级是9级，使用特殊值
        if special_values and len(special_values) == 1 and lv == 9:
            curve.append(round(special_values[0], 1))
        else:
            # 小数数据：除10还原
            curve.append(round(calculated / scale_factor, 1))

    # 10-12级使用特殊值或继续计算
    if special_values and len(special_values) >= 3:
        curve.extend([round(v, 1) for v in special_values[:3]])
    else:
        for lv in range(10, 13):
            calculated = scaled_base + math.floor((scaled_growth * (lv - 1) + scaled_offset) / divisor)
            curve.append(round(calculated / scale_factor, 1))

    return curve


def calculate_bonus_attribute(
    base: float | int,
    growth: float | int,
    divisor: float | int,
    offset: float | int = 0,
    special: List[float | int] | None = None,
    max_level: int = 9,
    is_decimal: bool | None = None
) -> List[float]:
    """
    计算附加属性成长曲线（潜能1-9级）

    数据处理规则：
    - 整数数据：直接按公式计算
    - 小数数据：乘10→整数计算→除10

    参数：
        base: 潜能1级时的基础值（支持整数和小数）
        growth: 成长系数（支持整数和小数）
        divisor: 除数（支持整数和小数）
        offset: 偏移量（支持整数和小数）
        special: 特殊值列表（第9级的特殊值），如 [23.4] 表示第9级使用23.4（支持整数和小数）
        max_level: 最大等级，默认9
        is_decimal: 是否为小数数据（None表示自动检测）

    返回：
        各潜能等级属性值列表（索引0对应潜能1，保留一位小数）
    """
    if divisor <= 0:
        raise ValueError("除数必须大于0")
    if max_level < 1:
        raise ValueError("最大等级必须大于等于1")

    if is_decimal is None:
        is_decimal = infer_decimal_mode(base, growth, divisor, offset, special=special)

    # 小数数据：乘10处理（使用round确保浮点数精度）
    scale_factor = 10 if is_decimal else 1
    scaled_base = round(base * scale_factor)
    scaled_growth = round(growth * scale_factor)
    scaled_offset = round(offset * scale_factor)

    # 前8级用公式计算
    curve = []
    for lv in range(1, min(9, max_level + 1)):
        # 统一使用整数计算逻辑（floor）
        calculated = scaled_base + math.floor((scaled_growth * (lv - 1) + scaled_offset) / divisor)
        # 小数数据：除10还原
        curve.append(round(calculated / scale_factor, 1))

    # 如果max_level>=9，需要计算第9级
    if max_level >= 9:
        if special and len(special) > 0:
            curve.append(round(special[0], 1))
        else:
            # 计算第9级（lv=9对应索引8）
            calculated = scaled_base + math.floor((scaled_growth * 8 + scaled_offset) / divisor)
            curve.append(round(calculated / scale_factor, 1))

    return curve
