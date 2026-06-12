#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""
反推公式统一入口（向后兼容层）

公开函数保持原始签名不变，内部委托给 ``EndfieldInverseAdapter``。

支持的数据格式：
- 属性数据：90 或 94 个数据（等级 1-90）
- 技能倍率：9 或 12 个数据（等级 1-9 或 1-12）
- 支持整数和小数百分比格式

新代码推荐直接使用 ``EndfieldInverseAdapter``::

    from games.endfield.calc.damage.inverse.adapter import EndfieldInverseAdapter
    adapter = EndfieldInverseAdapter()
    result = adapter.fit(data)
"""

from collections.abc import Sequence

from .adapter import EndfieldInverseAdapter
from .adapter import remove_duplicates_94 as remove_duplicates
from .attribute import fit_attribute_formula, validate_attribute_formula
from .skill import (
    fit_skill_formula,
    fit_skill_formula_no_special,
    validate_skill_formula,
    validate_skill_formula_no_special,
)

_adapter = EndfieldInverseAdapter()

__all__ = [
    "fit_attribute_formula",
    "fit_formula",
    "fit_skill_formula",
    "fit_skill_formula_no_special",
    "remove_duplicates",
    "validate_attribute_formula",
    "validate_formula",
    "validate_skill_formula",
    "validate_skill_formula_no_special",
]


def fit_formula(
    data: Sequence[int | float],
) -> tuple[int | float, int | float, int, int | float, list[int | float] | None]:
    """
    统一拟合接口，自动检测数据类型。

    返回：(base, growth, divisor, offset, special_values)

    支持：
    - 90 个数据 → 属性成长
    - 12 个数据 → 技能倍率（含特殊值）
    - 9 个数据 → 技能倍率（无特殊值）
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
    统一验证接口，自动检测数据类型。
    """
    if len(data) == 90:
        return validate_attribute_formula(base, growth, divisor, offset, data)
    elif len(data) == 12:
        return validate_skill_formula(base, growth, divisor, offset, special_values or [], data)
    elif len(data) == 9:
        return validate_skill_formula_no_special(base, growth, divisor, offset, special_values or [], data)
    else:
        raise ValueError(f"不支持的数据长度: {len(data)}")
