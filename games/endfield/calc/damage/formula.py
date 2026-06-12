#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
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


# ==================== 通用常量 ====================

# 等级列表（1-90级）
levels = list(range(1, 91))

# 潜能/精炼等级列表（0-5级）
talent = list(range(0, 6))

# 信赖等级列表（0-4级）
trust = list(range(0, 5))

# 信赖加成（累积值，0-4级：0→10→25→40→60）
trust_add = [0, 10, 25, 40, 60]


def has_fractional_part(value: int | float) -> bool:
    """真小数（如 5.4、23.4）；整数值的 float（如 10.0）不算。

    委托框架 FloorFormulaFitter._detect_scale 统一判断。
    """
    from calc_framework.inverse.base import FloorFormulaFitter

    return FloorFormulaFitter._detect_scale([value]) > 1


def infer_decimal_mode(
    base: int | float,
    growth: int | float,
    divisor: int | float,
    offset: int | float = 0,
    *,
    special: list[float | int] | None = None,
    is_decimal: bool | None = None,
) -> bool:
    """
    是否启用「×10 → floor → ÷10」小数取整。

    委托框架 FloorFormulaFitter._detect_scale 统一判断。

    - 曲线/参数含真小数（如 5.4、special 里 23.4）→ 小数模式
    - 纯整数或 10.0 这类整型 float → 直接 floor
    - 可显式传入 is_decimal 覆盖自动判断
    """
    if is_decimal is not None:
        return is_decimal
    from calc_framework.inverse.base import FloorFormulaFitter

    candidates = [base, growth, divisor, offset]
    if special:
        candidates.extend(special)
    return FloorFormulaFitter._detect_scale(candidates) > 1


# ==================== 通用成长曲线计算器 ====================


def calculate_growth_curve(
    base: float | int, growth: float | int, divisor: float | int, offset: float | int = 0, max_level: int = 90
) -> list[float]:
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

    from calc_framework.inverse.base import FloorFormulaFitter

    return FloorFormulaFitter().compute(
        {"base": base, "growth": growth, "divisor": divisor, "offset": offset},
        num_levels=max_level,
    )


def calculate_skill_curve(
    base: float | int,
    growth: float | int,
    divisor: float | int,
    offset: float | int = 0,
    special_values: list[float | int] | None = None,
    use_floor: bool = True,
    is_decimal: bool | None = None,
) -> list[float]:
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
        is_decimal = infer_decimal_mode(base, growth, divisor, offset, special=special_values)

    # 构建 level_overrides（游戏层逻辑：special_values → 等级映射）
    level_overrides: dict[int, float] = {}
    if special_values:
        if len(special_values) == 1:
            # 1 个特殊值 → 替代第 9 级
            level_overrides[9] = special_values[0]
        elif len(special_values) >= 3:
            # 3 个特殊值 → 替代第 10-12 级
            for i, v in enumerate(special_values[:3]):
                level_overrides[10 + i] = v

    from calc_framework.inverse.base import FloorFormulaFitter

    return FloorFormulaFitter().compute(
        {"base": base, "growth": growth, "divisor": divisor, "offset": offset, "is_decimal": is_decimal},
        num_levels=12,
        level_overrides=level_overrides or None,
    )


def calculate_bonus_attribute(
    base: float | int,
    growth: float | int,
    divisor: float | int,
    offset: float | int = 0,
    special: list[float | int] | None = None,
    max_level: int = 9,
    is_decimal: bool | None = None,
) -> list[float]:
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

    # 构建 level_overrides（游戏层逻辑：special → 等级映射）
    level_overrides: dict[int, float] = {}
    if special and max_level >= 9:
        level_overrides[9] = special[0]

    from calc_framework.inverse.base import FloorFormulaFitter

    return FloorFormulaFitter().compute(
        {"base": base, "growth": growth, "divisor": divisor, "offset": offset, "is_decimal": is_decimal},
        num_levels=max_level,
        level_overrides=level_overrides or None,
    )
