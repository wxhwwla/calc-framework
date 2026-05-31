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

from .attribute import fit_attribute_formula, validate_attribute_formula
from .skill import (
    fit_skill_formula,
    fit_skill_formula_no_special,
    validate_skill_formula,
    validate_skill_formula_no_special,
)


def fit_formula(
    data: Sequence[int | float],
) -> tuple[int | float, int | float, int, int | float, list[int | float] | None]:
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


def validate_formula(
    base: int | float,
    growth: int | float,
    divisor: int,
    offset: int | float,
    data: Sequence[int | float],
    special_values: list[int | float] | None = None,
) -> bool:
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
