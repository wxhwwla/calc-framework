#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""

反向计算公式参数模块



用于通过给定的等级数据，反向推导出属性成长公式和技能倍率公式的参数。



公式：base + floor((growth * (lv - 1) + offset) / divisor)



输入支持：

- 属性数据：90或94个数据（等级1-90）

- 技能倍率：9或12个数据（等级1-9或1-12）

- 支持整数和小数百分比格式

"""

from collections.abc import Sequence

from .fit_core import _find_best_params, _inv_print, _is_decimal_data, _scale_data


def fit_skill_formula(
    data: Sequence[int | float],
) -> tuple[int | float, int | float, int, int | float, list[int | float]]:
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

    diffs = [scaled_base_data[i] - scaled_base_data[i - 1] for i in range(1, 9)]

    if diffs:
        _inv_print(f"差分(1-9级): 平均={sum(diffs) / len(diffs):.3f}, 最大={max(diffs)}, 最小={min(diffs)}")

    _inv_print(f"特殊值(10-12级): {special_values}")

    # 查找最佳参数

    params = _find_best_params(
        scaled_base_data,
        base,
        scaled_base,
        scale_factor,
        num_levels=9,
        divisor_range=(1, 501),
        growth_range=(1, 601),
        offset_search_limit=500,
    )

    assert params is not None, "无法找到合适的公式参数"

    return (base, params[0], params[1], params[2], special_values)


def fit_skill_formula_no_special(
    data: Sequence[int | float],
) -> tuple[int | float, int | float, int, int | float, list[int | float]]:
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

    diffs = [data[i] - data[i - 1] for i in range(1, 9)]

    if diffs:
        _inv_print(f"差分(1-9级): 平均={sum(diffs) / len(diffs):.3f}, 最大={max(diffs)}, 最小={min(diffs)}")

    # 缩放数据

    scaled_data, scale_factor = _scale_data(data)

    scaled_base = int(base * scale_factor)

    _inv_print(f"数据类型: {'小数' if scale_factor == 10 else '整数'}")

    # 首先尝试拟合全部9个数据

    params = _find_best_params(
        scaled_data,
        base,
        scaled_base,
        scale_factor,
        num_levels=9,
        divisor_range=(1, 501),
        growth_range=(1, 1001),
        offset_search_limit=500,
    )

    if params:
        _inv_print("\n[OK] 找到完全匹配的参数!")

        _inv_print("公式: base + floor((growth * (lv - 1) + offset) / divisor)")

        _inv_print(f"参数: base={base}, growth={params[0]}, divisor={params[1]}, offset={params[2]}")

        return (base, params[0], params[1], params[2], [])

    # 如果全部9个数据无法拟合，则尝试将第9个作为特殊值

    _inv_print("\n[INFO] 无法拟合全部9个数据，尝试将第9个作为特殊值...")

    special_values = [data[8]]

    scaled_base_data = scaled_data[:8]

    _inv_print(f"特殊值(9级): {special_values}")

    # 使用前8级数据拟合

    params = _find_best_params(
        scaled_base_data,
        base,
        scaled_base,
        scale_factor,
        num_levels=8,
        divisor_range=(1, 501),
        growth_range=(1, 1001),
        offset_search_limit=500,
    )

    assert params is not None, "无法找到合适的公式参数"

    _inv_print("\n[OK] 找到完全匹配的参数!")

    _inv_print("公式: base + floor((growth * (lv - 1) + offset) / divisor)")

    _inv_print(f"参数: base={base}, growth={params[0]}, divisor={params[1]}, offset={params[2]}")

    return (base, params[0], params[1], params[2], special_values)


def validate_skill_formula(
    base: int | float,
    growth: int | float,
    divisor: int,
    offset: int | float,
    special_values: list[int | float],
    data: Sequence[int | float],
) -> bool:
    """验证技能倍率公式（含特殊值）"""

    from games.endfield.calc.damage.formula import calculate_skill_curve

    calculated = calculate_skill_curve(base, growth, divisor, offset, special_values)

    return all(abs(calculated[i] - val) <= 0.001 for i, val in enumerate(data))


def validate_skill_formula_no_special(
    base: int | float,
    growth: int | float,
    divisor: int,
    offset: int | float,
    special_values: list[int | float],
    data: Sequence[int | float],
) -> bool:
    """验证技能倍率公式（9个元素版本）"""

    from games.endfield.calc.damage.formula import calculate_bonus_attribute

    use_decimal = _is_decimal_data(data)

    calculated = calculate_bonus_attribute(base, growth, divisor, offset, special_values, is_decimal=use_decimal)

    return all(abs(calculated[i] - val) <= 0.001 for i, val in enumerate(data))


# ==================== 快捷接口 ====================
