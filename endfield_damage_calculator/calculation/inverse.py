#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
反向计算公式参数模块

用于通过给定的等级数据，反向推导出属性成长公式和技能倍率公式的参数。

公式：base + floor((growth * (lv - 1) + offset) / divisor)

输入支持：
- 属性数据：90或94个数据（等级1-90）
- 技能倍率：9或12个数据（等级1-9或1-12）
- 支持整数和小数百分比格式
"""

import math
import os
from typing import List, Tuple, Sequence, Optional


def _inverse_verbose() -> bool:
    """调试输出开关：环境变量 INVERSE_FIT_VERBOSE=1。"""
    return os.environ.get("INVERSE_FIT_VERBOSE", "").strip().lower() in ("1", "true", "yes")


def _inv_print(*args: object, **kwargs: object) -> None:
    if _inverse_verbose():
        _inv_print(*args, **kwargs)


# ==================== 内部辅助函数 ====================

def _is_decimal_data(data: Sequence[int | float]) -> bool:
    """
    判断数据是否包含小数（非整数的浮点数）
    
    参数：
        data: 数据序列
    
    返回：
        是否为小数数据
    """
    return any(isinstance(x, float) and x != int(x) for x in data)


def _scale_data(data: Sequence[int | float], scale_factor: int = 10) -> Tuple[List[int], int]:
    """
    缩放数据（小数乘10转换为整数）
    
    参数：
        data: 原始数据序列
        scale_factor: 缩放因子（默认10）
    
    返回：
        (缩放后的数据, 实际使用的缩放因子)
    """
    is_decimal = _is_decimal_data(data)
    actual_scale = scale_factor if is_decimal else 1
    
    if is_decimal:
        scaled = [int(round(x * actual_scale)) for x in data]
    else:
        scaled = [int(x) for x in data]
    
    return scaled, actual_scale


def _restore_param(value: float | int, scale_factor: int) -> int | float:
    """
    将反推参数还原为录入格式。

    整数曲线在 scale_factor==1 时必须返回 int，否则 calculate_bonus_attribute
    会把 float 误判为小数模式（×10），与 weapons.json / seed 不一致。
    """
    if scale_factor != 1:
        return value
    rounded = round(float(value))
    if abs(float(value) - rounded) < 1e-9:
        return int(rounded)
    return value


def _params_sort_key(
    growth: int,
    divisor: int,
    offset: int,
) -> Tuple[int, int, int]:
    """等价参数间按 growth → divisor → |offset| 取最小（便于录入）。"""
    return (growth, divisor, abs(offset))


def _gcd_normalize_params(
    growth: int,
    divisor: int,
    offset: int,
    scaled_data: List[int],
    scaled_base: int,
) -> Tuple[int, int, int]:
    """若 growth/divisor 有公因子且仍精确拟合，则约分到更小的整数参数。"""
    factor = math.gcd(growth, divisor)
    while factor > 1:
        ng, nd = growth // factor, divisor // factor
        if all(
            scaled_base + math.floor((ng * (lv - 1) + offset) / nd) == scaled_data[lv - 1]
            for lv in range(1, len(scaled_data) + 1)
        ):
            growth, divisor = ng, nd
            factor = math.gcd(growth, divisor)
        else:
            break
    return growth, divisor, offset


def _offset_bounds_for_pair(
    scaled_data: List[int],
    scaled_base: int,
    growth: int,
    divisor: int,
    num_levels: int,
) -> Tuple[bool, int, int]:
    """计算使 floor 公式在各等级成立的 offset 整数区间。"""
    offset_lower = -10**18
    offset_upper = 10**18
    for lv in range(1, num_levels + 1):
        target = scaled_data[lv - 1] - scaled_base
        lower = target * divisor - growth * (lv - 1)
        upper = (target + 1) * divisor - growth * (lv - 1) - 1
        offset_lower = max(offset_lower, math.ceil(lower))
        offset_upper = min(offset_upper, math.floor(upper))
        if offset_lower > offset_upper:
            return False, 0, 0
    return True, int(offset_lower), int(offset_upper)


def _find_best_params(
    scaled_data: List[int],
    base: int | float,
    scaled_base: int,
    scale_factor: int,
    num_levels: int,
    divisor_range: Tuple[int, int] = (1, 501),
    growth_range: Tuple[int, int] = (1, 1001),
    offset_search_limit: int = 500
) -> Optional[Tuple[int | float, int, int | float]]:
    """
    查找最佳拟合参数（核心算法）
    
    参数：
        scaled_data: 缩放后的数据
        base: 原始基础值
        scaled_base: 缩放后的基础值
        scale_factor: 缩放因子
        num_levels: 要拟合的等级数量
        divisor_range: 除数搜索范围
        growth_range: 成长值搜索范围
        offset_search_limit: offset搜索限制
    
    返回：
        (growth, divisor, offset) 或 None

    多条等价参数时，按 growth → divisor → |offset| 取字典序最小的一组。
    """
    best_params: Tuple[int, int, int] | None = None
    best_key: Tuple[int, int, int] | None = None
    best_error = float('inf')

    def _consider(growth: int, divisor: int, offset: int, error: float) -> None:
        nonlocal best_params, best_key, best_error
        key = _params_sort_key(growth, divisor, offset)
        if error < 0.001:
            if best_key is None or key < best_key:
                best_key = key
                best_params = (growth, divisor, offset)
                best_error = 0.0
            return
        if best_error < 0.001:
            return
        if error < best_error or (error == best_error and (best_key is None or key < best_key)):
            best_error = error
            best_key = key
            best_params = (growth, divisor, offset)

    # 精确解：growth → divisor → offset 递增扫描，首个精确解即最小字典序
    for growth in range(*growth_range):
        for divisor in range(*divisor_range):
            valid, offset_lower, offset_upper = _offset_bounds_for_pair(
                scaled_data, scaled_base, growth, divisor, num_levels
            )
            if not valid:
                continue
            for offset in range(offset_lower, offset_upper + 1):
                error = 0
                for lv in range(1, num_levels + 1):
                    calculated = scaled_base + math.floor(
                        (growth * (lv - 1) + offset) / divisor
                    )
                    error += abs(calculated - scaled_data[lv - 1])
                if error < 0.001:
                    growth, divisor, offset = _gcd_normalize_params(
                        growth, divisor, offset, scaled_data, scaled_base
                    )
                    return (
                        _restore_param(growth / scale_factor, scale_factor),
                        divisor,
                        _restore_param(offset / scale_factor, scale_factor),
                    )

    # 无精确解：最小二乘，并在同误差下取最小字典序参数
    for growth in range(*growth_range):
        for divisor in range(*divisor_range):
            total_offset = sum(
                (scaled_data[lv - 1] - scaled_base) * divisor - growth * (lv - 1)
                for lv in range(1, num_levels + 1)
            )
            offset = round(total_offset / num_levels)
            error = sum(
                abs(
                    scaled_base
                    + math.floor((growth * (lv - 1) + offset) / divisor)
                    - scaled_data[lv - 1]
                )
                for lv in range(1, num_levels + 1)
            )
            _consider(growth, divisor, int(offset), float(error))

            valid, offset_lower, offset_upper = _offset_bounds_for_pair(
                scaled_data, scaled_base, growth, divisor, num_levels
            )
            if not valid:
                continue
            offset_end = min(offset_upper + 1, offset_lower + offset_search_limit)
            for offset in range(offset_lower, offset_end):
                error = sum(
                    abs(
                        scaled_base
                        + math.floor((growth * (lv - 1) + offset) / divisor)
                        - scaled_data[lv - 1]
                    )
                    for lv in range(1, num_levels + 1)
                )
                _consider(growth, divisor, offset, float(error))

    if best_params is None or best_error >= num_levels * 0.1:
        return None

    growth, divisor, offset = best_params
    if best_error < 0.001:
        growth, divisor, offset = _gcd_normalize_params(
            growth, divisor, offset, scaled_data, scaled_base
        )
    return (
        _restore_param(growth / scale_factor, scale_factor),
        divisor,
        _restore_param(offset / scale_factor, scale_factor),
    )


# ==================== 属性成长反向计算 ====================

def remove_duplicates(data: Sequence[int | float]) -> List[int | float]:
    """
    移除重复数据（第20,40,60,80级重复）
    重复位置：索引19-20, 40-41, 61-62, 82-83
    移除重复中后面的那个：索引20, 41, 62, 83
    """
    if len(data) != 94:
        raise ValueError(f"输入数据长度应为94，实际为{len(data)}")

    duplicate_indices = [20, 41, 62, 83]
    return [data[i] for i in range(94) if i not in duplicate_indices]


def fit_attribute_formula(data: Sequence[int | float]) -> Tuple[int | float, int | float, int, int | float]:
    """
    拟合属性成长公式参数：base + floor((growth * (lv - 1) + offset) / divisor)

    数据处理规则：
    - 整数数据: 直接使用 floor 公式
    - 小数数据: 乘10→整数计算→除10
    """
    if len(data) != 90:
        raise ValueError(f"数据长度应为90，实际为{len(data)}")

    base = data[0]
    _inv_print(f"\n数据长度: 90")
    _inv_print(f"base = {base}")

    # 缩放数据
    scaled_data, scale_factor = _scale_data(data)
    scaled_base = int(base * scale_factor)
    _inv_print(f"数据类型: {'小数' if scale_factor == 10 else '整数'}")

    # 计算差分
    diffs = [scaled_data[i] - scaled_data[i-1] for i in range(1, 90)]
    _inv_print(f"差分: 平均={sum(diffs)/len(diffs):.3f}, 最大={max(diffs)}, 最小={min(diffs)}")

    # 查找最佳参数
    params = _find_best_params(
        scaled_data, base, scaled_base, scale_factor,
        num_levels=90,
        divisor_range=(1, 201),
        growth_range=(1, 301),
        offset_search_limit=200
    )
    
    assert params is not None, "无法找到合适的公式参数"
    return (base, params[0], params[1], params[2])


def validate_attribute_formula(base: int | float, growth: int | float, divisor: int, offset: int | float, data: Sequence[int | float]) -> bool:
    """验证属性成长公式"""
    from calculation.formula import calculate_growth_curve
    
    calculated = calculate_growth_curve(base, growth, divisor, offset)
    for i, val in enumerate(data):
        if abs(calculated[i] - val) > 0.001:
            return False
    return True


# ==================== 技能倍率反向计算 ====================

def fit_skill_formula(data: Sequence[int | float]) -> Tuple[int | float, int | float, int, int | float, List[int | float]]:
    """
    拟合技能倍率公式参数：base + floor((growth * (lv - 1) + offset) / divisor)

    数据处理规则：
    - 整数数据: 直接使用 floor 公式
    - 小数数据: 乘10→整数计算→除10

    特殊值（10-12级）直接从输入数据获取
    """
    if len(data) != 12:
        raise ValueError(f"技能倍率数据长度应为12，实际为{len(data)}")

    special_values = list(data[9:12])
    base_data = data[:9]
    base = base_data[0]

    _inv_print(f"\nbase = {base}")

    # 缩放数据
    scaled_base_data, scale_factor = _scale_data(base_data)
    scaled_base = int(base * scale_factor)
    _inv_print(f"数据类型: {'小数' if scale_factor == 10 else '整数'}")

    # 计算差分
    diffs = [scaled_base_data[i] - scaled_base_data[i-1] for i in range(1, 9)]
    if diffs:
        _inv_print(f"差分(1-9级): 平均={sum(diffs)/len(diffs):.3f}, 最大={max(diffs)}, 最小={min(diffs)}")
    _inv_print(f"特殊值(10-12级): {special_values}")

    # 查找最佳参数
    params = _find_best_params(
        scaled_base_data, base, scaled_base, scale_factor,
        num_levels=9,
        divisor_range=(1, 501),
        growth_range=(1, 601),
        offset_search_limit=500
    )
    
    assert params is not None, "无法找到合适的公式参数"
    return (base, params[0], params[1], params[2], special_values)


def fit_skill_formula_no_special(data: Sequence[int | float]) -> Tuple[int | float, int | float, int, int | float, List[int | float]]:
    """
    拟合技能倍率公式参数（9个元素版本）

    数据处理规则：
    - 整数数据: 直接使用 floor 公式: base + floor((growth * (lv - 1) + offset) / divisor)
    - 小数数据: 乘10→整数计算→除10

    返回的参数适用于 calculate_bonus_attribute 函数调用。

    首先尝试将全部9个数据用公式拟合，如果找不到完美匹配，则将第9个作为特殊值
    """
    if len(data) != 9:
        raise ValueError(f"技能倍率数据长度应为9，实际为{len(data)}")

    base = data[0]
    _inv_print(f"\nbase = {base}")

    # 计算差分
    diffs = [data[i] - data[i-1] for i in range(1, 9)]
    if diffs:
        _inv_print(f"差分(1-9级): 平均={sum(diffs)/len(diffs):.3f}, 最大={max(diffs)}, 最小={min(diffs)}")

    # 缩放数据
    scaled_data, scale_factor = _scale_data(data)
    scaled_base = int(base * scale_factor)
    _inv_print(f"数据类型: {'小数' if scale_factor == 10 else '整数'}")

    # 首先尝试拟合全部9个数据
    params = _find_best_params(
        scaled_data, base, scaled_base, scale_factor,
        num_levels=9,
        divisor_range=(1, 501),
        growth_range=(1, 1001),
        offset_search_limit=500
    )
    
    if params:
        _inv_print(f"\n[OK] 找到完全匹配的参数!")
        _inv_print(f"公式: base + floor((growth * (lv - 1) + offset) / divisor)")
        _inv_print(f"参数: base={base}, growth={params[0]}, divisor={params[1]}, offset={params[2]}")
        return (base, params[0], params[1], params[2], [])

    # 如果全部9个数据无法拟合，则尝试将第9个作为特殊值
    _inv_print("\n[INFO] 无法拟合全部9个数据，尝试将第9个作为特殊值...")
    special_values = [data[8]]
    scaled_base_data = scaled_data[:8]
    _inv_print(f"特殊值(9级): {special_values}")

    # 使用前8级数据拟合
    params = _find_best_params(
        scaled_base_data, base, scaled_base, scale_factor,
        num_levels=8,
        divisor_range=(1, 501),
        growth_range=(1, 1001),
        offset_search_limit=500
    )
    
    assert params is not None, "无法找到合适的公式参数"
    _inv_print(f"\n[OK] 找到完全匹配的参数!")
    _inv_print(f"公式: base + floor((growth * (lv - 1) + offset) / divisor)")
    _inv_print(f"参数: base={base}, growth={params[0]}, divisor={params[1]}, offset={params[2]}")
    return (base, params[0], params[1], params[2], special_values)


def validate_skill_formula(base: int | float, growth: int | float, divisor: int, offset: int | float, special_values: List[int | float], data: Sequence[int | float]) -> bool:
    """验证技能倍率公式（含特殊值）"""
    from calculation.formula import calculate_skill_curve
    
    calculated = calculate_skill_curve(base, growth, divisor, offset, special_values)
    for i, val in enumerate(data):
        if abs(calculated[i] - val) > 0.001:
            return False
    return True


def validate_skill_formula_no_special(base: int | float, growth: int | float, divisor: int, offset: int | float, special_values: List[int | float], data: Sequence[int | float]) -> bool:
    """验证技能倍率公式（9个元素版本）"""
    from calculation.formula import calculate_bonus_attribute

    use_decimal = _is_decimal_data(data)
    calculated = calculate_bonus_attribute(
        base, growth, divisor, offset, special_values, is_decimal=use_decimal
    )
    for i, val in enumerate(data):
        if abs(calculated[i] - val) > 0.001:
            return False
    return True


# ==================== 快捷接口 ====================

def fit_formula(data: Sequence[int | float]) -> Tuple[int | float, int | float, int, int | float, List[int | float] | None]:
    """
    统一拟合接口，自动检测数据类型
    
    返回：(base, growth, divisor, offset, special_values)
    """
    if len(data) == 90:
        base, growth, divisor, offset = fit_attribute_formula(data)
        return (base, growth, divisor, offset, None)
    elif len(data) == 12:
        return fit_skill_formula(data)
    elif len(data) == 9:
        return fit_skill_formula_no_special(data)
    else:
        raise ValueError(f"不支持的数据长度: {len(data)}")


def validate_formula(base: int | float, growth: int | float, divisor: int, offset: int | float, data: Sequence[int | float], special_values: List[int | float] | None = None) -> bool:
    """
    统一验证接口，自动检测数据类型
    """
    if len(data) == 90:
        return validate_attribute_formula(base, growth, divisor, offset, data)
    elif len(data) == 12:
        return validate_skill_formula(base, growth, divisor, offset, special_values or [], data)
    elif len(data) == 9:
        return validate_skill_formula_no_special(base, growth, divisor, offset, special_values or [], data)
    else:
        raise ValueError(f"不支持的数据长度: {len(data)}")