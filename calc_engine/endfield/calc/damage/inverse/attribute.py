#!/usr/bin/env python3
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

from .fit_core import _find_best_params, _inv_print, _scale_data


def remove_duplicates(data: Sequence[int | float]) -> list[int | float]:
    """
    移除重复数据（第20,40,60,80级重复）
    重复位置：索引19-20, 40-41, 61-62, 82-83
    移除重复中后面的那个：索引20, 41, 62, 83
    """
    if len(data) != 94:
        raise ValueError(f"输入数据长度应为94，实际为{len(data)}")

    duplicate_indices = [20, 41, 62, 83]
    return [data[i] for i in range(94) if i not in duplicate_indices]


def fit_attribute_formula(data: Sequence[int | float]) -> tuple[int | float, int | float, int, int | float]:
    """
    拟合属性成长公式参数：base + floor((growth * (lv - 1) + offset) / divisor)

    数据处理规则：
    - 整数数据: 直接使用 floor 公式
    - 小数数据: 乘10→整数计算→除10
    """
    if len(data) != 90:
        raise ValueError(f"数据长度应为90，实际为{len(data)}")

    base = data[0]
    _inv_print("\n数据长度: 90")
    _inv_print(f"base = {base}")

    # 缩放数据
    scaled_data, scale_factor = _scale_data(data)
    scaled_base = int(base * scale_factor)
    _inv_print(f"数据类型: {'小数' if scale_factor == 10 else '整数'}")

    # 计算差分
    diffs = [scaled_data[i] - scaled_data[i - 1] for i in range(1, 90)]
    _inv_print(f"差分: 平均={sum(diffs) / len(diffs):.3f}, 最大={max(diffs)}, 最小={min(diffs)}")

    # 查找最佳参数
    params = _find_best_params(
        scaled_data,
        base,
        scaled_base,
        scale_factor,
        num_levels=90,
        divisor_range=(1, 201),
        growth_range=(1, 301),
        offset_search_limit=200,
    )

    assert params is not None, "无法找到合适的公式参数"
    return (base, params[0], params[1], params[2])


def validate_attribute_formula(
    base: int | float, growth: int | float, divisor: int, offset: int | float, data: Sequence[int | float]
) -> bool:
    """验证属性成长公式"""
    from calc_engine.endfield.calc.damage.formula import calculate_growth_curve

    calculated = calculate_growth_curve(base, growth, divisor, offset)
    return all(abs(calculated[i] - val) <= 0.001 for i, val in enumerate(data))


# ==================== 技能倍率反向计算 ====================
