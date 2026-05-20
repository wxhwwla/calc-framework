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
from typing import List, Tuple, Sequence


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
    print(f"\n数据长度: 90")
    print(f"base = {base}")

    # 判断是否为小数数据
    is_decimal = any(isinstance(x, float) and x != int(x) for x in data)
    print(f"数据类型: {'小数' if is_decimal else '整数'}")

    # 小数数据：乘10处理
    scale_factor = 10 if is_decimal else 1
    scaled_base = base * scale_factor
    scaled_data = [x * scale_factor for x in data]

    diffs = [scaled_data[i] - scaled_data[i-1] for i in range(1, 90)]
    print(f"差分: 平均={sum(diffs)/len(diffs):.3f}, 最大={max(diffs)}, 最小={min(diffs)}")

    best_params = None
    best_error = float('inf')

    for divisor in range(1, 201):
        for growth in range(1, 301):
            offset_lower = -10**18
            offset_upper = 10**18

            valid = True
            for lv in range(1, 91):
                target = scaled_data[lv-1] - scaled_base
                lower = target * divisor - growth * (lv - 1)
                upper = (target + 1) * divisor - growth * (lv - 1)
                offset_lower = max(offset_lower, lower)
                offset_upper = min(offset_upper, upper)
                if offset_lower >= offset_upper:
                    valid = False
                    break

            if valid and offset_lower < offset_upper:
                for offset in range(int(offset_lower), min(int(offset_upper) + 1, int(offset_lower) + 200)):
                    error = 0
                    for lv in range(1, 91):
                        calculated = scaled_base + math.floor((growth * (lv - 1) + offset) / divisor)
                        if abs(calculated - scaled_data[lv-1]) > 0.001:
                            error += abs(calculated - scaled_data[lv-1])

                    if error < 0.001:
                        print(f"\n[OK] 找到完全匹配的参数!")
                        # 返回适用于原始数据的参数（除以scale_factor还原）
                        return (base, growth / scale_factor, divisor, offset / scale_factor)
                    elif error < best_error:
                        best_error = error
                        # 返回适用于原始数据的参数（除以scale_factor还原）
                        best_params = (base, growth / scale_factor, divisor, offset / scale_factor)

    if best_params is None:
        print("\n未找到精确匹配，使用最小二乘法...")
        for divisor in range(1, 201):
            for growth in range(1, 301):
                total_offset = sum((scaled_data[lv-1] - scaled_base) * divisor - growth * (lv - 1) for lv in range(1, 91))
                offset = round(total_offset / 90)
                error = sum(abs(scaled_base + math.floor((growth * (lv - 1) + offset) / divisor) - scaled_data[lv-1]) for lv in range(1, 91))
                if error < best_error:
                    best_error = error
                    # 返回适用于原始数据的参数（除以scale_factor还原）
                    best_params = (base, growth / scale_factor, divisor, offset / scale_factor)

    assert best_params is not None, "无法找到合适的公式参数"
    return best_params


def validate_attribute_formula(base: int | float, growth: int | float, divisor: int, offset: int | float, data: Sequence[int | float]) -> bool:
    """验证属性成长公式"""
    # 判断是否为小数数据
    is_decimal = any(isinstance(x, float) and x != int(x) for x in data)
    
    # 小数数据：乘10处理
    scale_factor = 10 if is_decimal else 1
    scaled_base = base * scale_factor
    scaled_data = [x * scale_factor for x in data]
    
    for lv in range(1, 91):
        # 统一使用整数 floor 算法
        calculated = scaled_base + math.floor((growth * (lv - 1) + offset) / divisor)
        if abs(calculated - scaled_data[lv-1]) > 0.001:
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
    print(f"\nbase = {base}")

    # 判断是否为小数数据
    is_decimal = any(isinstance(x, float) and x != int(x) for x in base_data)
    print(f"数据类型: {'小数' if is_decimal else '整数'}")

    # 小数数据：乘10处理
    scale_factor = 10 if is_decimal else 1
    scaled_base = base * scale_factor
    scaled_base_data = [x * scale_factor for x in base_data]

    diffs = [scaled_base_data[i] - scaled_base_data[i-1] for i in range(1, 9)]
    if diffs:
        print(f"差分(1-9级): 平均={sum(diffs)/len(diffs):.3f}, 最大={max(diffs)}, 最小={min(diffs)}")
    print(f"特殊值(10-12级): {special_values}")

    best_params = None
    best_error = float('inf')

    # 扩大搜索范围
    for divisor in range(1, 501):
        for growth in range(1, 601):
            offset_lower = -10**18
            offset_upper = 10**18

            valid = True
            for lv in range(1, 10):
                target = scaled_base_data[lv-1] - scaled_base
                lower = target * divisor - growth * (lv - 1)
                upper = (target + 1) * divisor - growth * (lv - 1)
                offset_lower = max(offset_lower, lower)
                offset_upper = min(offset_upper, upper)
                if offset_lower >= offset_upper:
                    valid = False
                    break

            if valid and offset_lower < offset_upper:
                for offset in range(int(offset_lower), min(int(offset_upper) + 1, int(offset_lower) + 500)):
                    error = 0
                    for lv in range(1, 10):
                        calculated = scaled_base + math.floor((growth * (lv - 1) + offset) / divisor)
                        if abs(calculated - scaled_base_data[lv-1]) > 0.001:
                            error += abs(calculated - scaled_base_data[lv-1])

                    if error < 0.001:
                        print(f"\n[OK] 找到完全匹配的参数!")
                        # 返回适用于原始数据的参数（除以scale_factor还原）
                        return (base, growth / scale_factor, divisor, offset / scale_factor, special_values)
                    elif error < best_error:
                        best_error = error
                        # 返回适用于原始数据的参数（除以scale_factor还原）
                        best_params = (base, growth / scale_factor, divisor, offset / scale_factor, special_values)

    if best_params is None:
        print("\n未找到精确匹配，使用最小二乘法...")
        for divisor in range(1, 501):
            for growth in range(1, 601):
                total_offset = sum((scaled_base_data[lv-1] - scaled_base) * divisor - growth * (lv - 1) for lv in range(1, 10))
                offset = round(total_offset / 9)
                error = sum(abs(scaled_base + math.floor((growth * (lv - 1) + offset) / divisor) - scaled_base_data[lv-1]) for lv in range(1, 10))
                if error < best_error:
                    best_error = error
                    # 返回适用于原始数据的参数（除以scale_factor还原）
                    best_params = (base, growth / scale_factor, divisor, offset / scale_factor, special_values)

    assert best_params is not None, "无法找到合适的公式参数"
    return best_params


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
    print(f"\nbase = {base}")

    diffs = [data[i] - data[i-1] for i in range(1, 9)]
    if diffs:
        print(f"差分(1-9级): 平均={sum(diffs)/len(diffs):.3f}, 最大={max(diffs)}, 最小={min(diffs)}")

    # 判断是否为小数数据
    is_decimal = any(isinstance(x, float) for x in data)
    print(f"数据类型: {'小数' if is_decimal else '整数'}")

    # 小数数据：乘10处理
    scale_factor = 10 if is_decimal else 1
    scaled_base = int(base * scale_factor)
    scaled_data = [int(round(x * scale_factor)) for x in data]

    best_params = None
    best_error = float('inf')

    # 首先尝试拟合全部9个数据
    for divisor in range(1, 501):
        for growth in range(1, 1001):
            offset_lower = -10**18
            offset_upper = 10**18

            valid = True
            for lv in range(1, 10):
                target = scaled_data[lv-1] - scaled_base
                lower = target * divisor - growth * (lv - 1)
                upper = (target + 1) * divisor - growth * (lv - 1)
                offset_lower = max(offset_lower, lower)
                offset_upper = min(offset_upper, upper)
                if offset_lower >= offset_upper:
                    valid = False
                    break

            if valid and offset_lower < offset_upper:
                for offset in range(int(offset_lower), min(int(offset_upper) + 1, int(offset_lower) + 500)):
                    error = 0
                    for lv in range(1, 10):
                        calculated = scaled_base + math.floor((growth * (lv - 1) + offset) / divisor)
                        if calculated != scaled_data[lv-1]:
                            error += abs(calculated - scaled_data[lv-1])

                    if error == 0:
                        print(f"\n[OK] 找到完全匹配的参数!")
                        print(f"公式: base + floor((growth * (lv - 1) + offset) / divisor)")
                        # 返回适用于原始数据的参数（除以scale_factor还原）
                        result_growth = growth / scale_factor
                        result_offset = offset / scale_factor
                        print(f"参数: base={base}, growth={result_growth}, divisor={divisor}, offset={result_offset}")
                        return (base, result_growth, divisor, result_offset, [])

    # 如果全部9个数据无法拟合，则尝试将第9个作为特殊值
    print("\n[INFO] 无法拟合全部9个数据，尝试将第9个作为特殊值...")
    
    special_values = [data[8]]
    scaled_base_data = scaled_data[:8]

    print(f"特殊值(9级): {special_values}")

    # 记录所有满足前8级的参数
    candidate_params = []

    for divisor in range(1, 501):
        for growth in range(1, 1001):
            offset_lower = -10**18
            offset_upper = 10**18

            valid = True
            for lv in range(1, 9):
                target = scaled_base_data[lv-1] - scaled_base
                lower = target * divisor - growth * (lv - 1)
                upper = (target + 1) * divisor - growth * (lv - 1)
                offset_lower = max(offset_lower, lower)
                offset_upper = min(offset_upper, upper)
                if offset_lower >= offset_upper:
                    valid = False
                    break

            if valid and offset_lower < offset_upper:
                for offset in range(int(offset_lower), min(int(offset_upper) + 1, int(offset_lower) + 500)):
                    error = 0
                    for lv in range(1, 9):
                        calculated = scaled_base + math.floor((growth * (lv - 1) + offset) / divisor)
                        if calculated != scaled_base_data[lv-1]:
                            error += abs(calculated - scaled_base_data[lv-1])

                    if error == 0:
                        if divisor > 0:
                            candidate_params.append((growth, divisor, offset))

    # 优先选择参数比值(growth/divisor)较小的（更合理的游戏数据）
    if candidate_params:
        # 按growth/divisor比值排序，优先选择比值较小的
        candidate_params.sort(key=lambda x: x[0]/x[1])
        result_growth_scaled, result_divisor, result_offset_scaled = candidate_params[0]
        # 返回适用于原始数据的参数（除以scale_factor还原）
        result_growth = result_growth_scaled / scale_factor
        result_offset = result_offset_scaled / scale_factor
        print(f"\n[OK] 找到完全匹配的参数!")
        print(f"公式: base + floor((growth * (lv - 1) + offset) / divisor)")
        print(f"参数: base={base}, growth={result_growth}, divisor={result_divisor}, offset={result_offset}")
        return (base, result_growth, result_divisor, result_offset, special_values)

    # 如果没有找到精确匹配，使用最小二乘法
    if best_params is None:
        print("\n未找到精确匹配，使用最小二乘法...")
        for divisor in range(1, 501):
            for growth in range(1, 1001):
                total_offset = sum((scaled_base_data[lv-1] - scaled_base) * divisor - growth * (lv - 1) for lv in range(1, 9))
                offset = round(total_offset / 8)
                error = sum(abs(scaled_base + math.floor((growth * (lv - 1) + offset) / divisor) - scaled_base_data[lv-1]) for lv in range(1, 9))
                
                if error < best_error:
                    best_error = error
                    if divisor > 0:
                        # 返回适用于原始数据的参数（除以scale_factor还原）
                        best_params = (base, growth / scale_factor, divisor, offset / scale_factor, special_values)

    assert best_params is not None, "无法找到合适的公式参数"
    return best_params


def validate_skill_formula(base: int | float, growth: int | float, divisor: int, offset: int | float, special_values: List[int | float], data: Sequence[int | float]) -> bool:
    """验证技能倍率公式（含特殊值）"""
    # 判断是否为小数数据
    is_decimal = any(isinstance(x, float) and x != int(x) for x in data[:9])
    
    # 小数数据：乘10处理
    scale_factor = 10 if is_decimal else 1
    scaled_base = base * scale_factor
    scaled_base_data = [x * scale_factor for x in data[:9]]
    
    # 验证1-9级
    for lv in range(1, 10):
        # 统一使用整数 floor 算法
        calculated = scaled_base + math.floor((growth * (lv - 1) + offset) / divisor)
        if abs(calculated - scaled_base_data[lv-1]) > 0.001:
            return False
    
    # 验证10-12级特殊值
    for i in range(10, 13):
        if abs(data[i-1] - special_values[i-10]) > 0.001:
            return False
    return True


def validate_skill_formula_no_special(base: int | float, growth: int | float, divisor: int, offset: int | float, special_values: List[int | float], data: Sequence[int | float]) -> bool:
    """验证技能倍率公式（9个元素版本）"""
    # 判断是否为小数数据
    is_decimal = any(isinstance(x, float) and x != int(x) for x in data)
    
    # 小数数据：乘10处理
    scale_factor = 10 if is_decimal else 1
    scaled_base = base * scale_factor
    scaled_data = [x * scale_factor for x in data]
    
    # 如果没有特殊值，验证全部9级
    if not special_values:
        for lv in range(1, 10):
            # 统一使用整数 floor 算法
            calculated = scaled_base + math.floor((growth * (lv - 1) + offset) / divisor)
            if abs(calculated - scaled_data[lv-1]) > 0.001:
                return False
        return True
    
    # 如果有特殊值，1-8级用公式验证，9级用特殊值验证
    for lv in range(1, 9):
        # 统一使用整数 floor 算法
        calculated = scaled_base + math.floor((growth * (lv - 1) + offset) / divisor)
        if abs(calculated - scaled_data[lv-1]) > 0.001:
            return False
    
    # 验证9级特殊值（保持原值比较，不乘10）
    if is_decimal:
        if abs(data[8] - special_values[0]) > 0.001:
            return False
    else:
        if data[8] != special_values[0]:
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