#!/usr/bin/env python3
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
from collections.abc import Sequence


def _inverse_verbose() -> bool:
    """调试输出开关：环境变量 INVERSE_FIT_VERBOSE=1。"""
    return os.environ.get("INVERSE_FIT_VERBOSE", "").strip().lower() in ("1", "true", "yes")


def _inv_print(*args: object, **kwargs: object) -> None:
    """调试输出函数：仅在环境变量 INVERSE_FIT_VERBOSE=1 时输出。"""
    if _inverse_verbose():
        print(*args, **kwargs)


# ==================== 内部辅助函数 ====================


def _is_decimal_data(data: Sequence[int | float]) -> bool:
    """
    判断数据是否包含小数（非整数的浮点数）。

    Args:
        data: 数据序列

    Returns:
        True 如果数据中包含非整数的浮点数（如 5.4、23.4），False 否则
    """
    return any(isinstance(x, float) and x != int(x) for x in data)


def _scale_data(data: Sequence[int | float], scale_factor: int = 10) -> tuple[list[int], int]:
    """
    缩放数据（小数乘10转换为整数）。

    小数数据需要进行缩放处理，将其转换为整数后再进行公式拟合，
    避免浮点数精度问题带来的误差。

    Args:
        data: 原始数据序列
        scale_factor: 缩放因子（默认10，用于处理小数数据）

    Returns:
        元组：(缩放后的数据列表, 实际使用的缩放因子)
    """
    is_decimal = _is_decimal_data(data)
    actual_scale = scale_factor if is_decimal else 1

    if is_decimal:
        scaled = [round(x * actual_scale) for x in data]
    else:
        scaled = [int(x) for x in data]

    return scaled, actual_scale


def _restore_param(value: float | int, scale_factor: int) -> int | float:
    """
    将反推参数还原为录入格式。

    整数曲线在 scale_factor==1 时必须返回 int，否则 calculate_bonus_attribute
    会把 float 误判为小数模式（×10），与 weapons.json / seed 不一致。

    Args:
        value: 缩放后的参数值
        scale_factor: 缩放因子（1 表示整数数据，10 表示小数数据）

    Returns:
        还原后的参数值（整数数据返回 int，小数数据保持 float）
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
) -> tuple[int, int, int]:
    """
    参数排序键生成函数。

    用于在多条等价参数中选择最优解：按 growth → divisor → |offset| 取最小，
    这样选择的参数更简洁，便于人工录入和维护。

    Args:
        growth: 成长系数
        divisor: 除数
        offset: 偏移量

    Returns:
        排序键元组
    """
    return (growth, divisor, abs(offset))


def _gcd_normalize_params(
    growth: int,
    divisor: int,
    offset: int,
    scaled_data: list[int],
    scaled_base: int,
) -> tuple[int, int, int]:
    """
    对参数进行最大公约数规范化。

    如果 growth 和 divisor 有公因子，且约分后仍能精确拟合数据，则进行约分，
    得到更小、更简洁的整数参数。

    Args:
        growth: 成长系数
        divisor: 除数
        offset: 偏移量
        scaled_data: 缩放后的数据列表
        scaled_base: 缩放后的基础值

    Returns:
        规范化后的 (growth, divisor, offset) 元组
    """
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
    scaled_data: list[int],
    scaled_base: int,
    growth: int,
    divisor: int,
    num_levels: int,
) -> tuple[bool, int, int]:
    """
    计算使 floor 公式在各等级成立的 offset 整数区间。

    对于给定的 growth 和 divisor，计算 offset 的取值范围，使得公式：
        scaled_base + floor((growth * (lv - 1) + offset) / divisor)
    在所有等级上都能精确匹配 scaled_data。

    Args:
        scaled_data: 缩放后的数据列表
        scaled_base: 缩放后的基础值
        growth: 成长系数
        divisor: 除数
        num_levels: 等级数量

    Returns:
        元组：(是否存在有效区间, offset下界, offset上界)
    """
    offset_lower = -(10**18)
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
    scaled_data: list[int],
    base: int | float,
    scaled_base: int,
    scale_factor: int,
    num_levels: int,
    divisor_range: tuple[int, int] = (1, 501),
    growth_range: tuple[int, int] = (1, 1001),
    offset_search_limit: int = 500,
) -> tuple[int | float, int, int | float] | None:
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
    best_params: tuple[int, int, int] | None = None
    best_key: tuple[int, int, int] | None = None
    best_error = float("inf")

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
                    calculated = scaled_base + math.floor((growth * (lv - 1) + offset) / divisor)
                    error += abs(calculated - scaled_data[lv - 1])
                if error < 0.001:
                    growth, divisor, offset = _gcd_normalize_params(growth, divisor, offset, scaled_data, scaled_base)
                    return (
                        _restore_param(growth / scale_factor, scale_factor),
                        divisor,
                        _restore_param(offset / scale_factor, scale_factor),
                    )

    # 无精确解：最小二乘，并在同误差下取最小字典序参数
    for growth in range(*growth_range):
        for divisor in range(*divisor_range):
            total_offset = sum(
                (scaled_data[lv - 1] - scaled_base) * divisor - growth * (lv - 1) for lv in range(1, num_levels + 1)
            )
            offset = round(total_offset / num_levels)
            error = sum(
                abs(scaled_base + math.floor((growth * (lv - 1) + offset) / divisor) - scaled_data[lv - 1])
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
                    abs(scaled_base + math.floor((growth * (lv - 1) + offset) / divisor) - scaled_data[lv - 1])
                    for lv in range(1, num_levels + 1)
                )
                _consider(growth, divisor, offset, float(error))

    if best_params is None or best_error >= num_levels * 0.1:
        return None

    growth, divisor, offset = best_params
    if best_error < 0.001:
        growth, divisor, offset = _gcd_normalize_params(growth, divisor, offset, scaled_data, scaled_base)
    return (
        _restore_param(growth / scale_factor, scale_factor),
        divisor,
        _restore_param(offset / scale_factor, scale_factor),
    )


# ==================== 属性成长反向计算 ====================
