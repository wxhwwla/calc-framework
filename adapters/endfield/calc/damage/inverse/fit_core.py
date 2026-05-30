"""
反向计算公式参数模块（薄适配层）

核心算法已迁移至框架 ``calc_framework.inverse.base.FloorFormulaFitter``。
本模块保留原始 API 签名，作为终末地适配器的向后兼容层。
"""

from __future__ import annotations

import os
from collections.abc import Sequence

from calc_framework.inverse.base import FloorFormulaFitter

_FITTER = FloorFormulaFitter()


def _inverse_verbose() -> bool:
    """调试输出开关：环境变量 INVERSE_FIT_VERBOSE=1。"""
    return os.environ.get("INVERSE_FIT_VERBOSE", "").strip().lower() in ("1", "true", "yes")


def _inv_print(*args: object, **kwargs: object) -> None:
    """调试输出函数。"""
    if _inverse_verbose():
        print(*args, **kwargs)


def _is_decimal_data(data: Sequence[int | float]) -> bool:
    """判断数据是否包含真小数。"""
    return _FITTER._detect_scale(data) > 1


def _scale_data(data: Sequence[int | float], scale_factor: int = 10) -> tuple[list[int], int]:
    """缩放数据（小数乘 10 转换为整数）。"""
    is_decimal = _is_decimal_data(data)
    actual_scale = scale_factor if is_decimal else 1
    if is_decimal:
        return [round(x * actual_scale) for x in data], actual_scale
    return [int(x) for x in data], actual_scale


def _restore_param(value: float | int, scale_factor: int) -> int | float:
    """将反推参数还原为录入格式。"""
    return _FITTER._restore_param(value, scale_factor)


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
    """查找最佳拟合参数（委托框架 FloorFormulaFitter）。

    Returns:
        (growth, divisor, offset) 或 None
    """
    result = _FITTER._search(
        scaled_data=scaled_data,
        scaled_base=scaled_base,
        scale_factor=scale_factor,
        num_levels=num_levels,
        divisor_range=divisor_range,
        growth_range=growth_range,
        offset_search_limit=offset_search_limit,
    )
    if result is None or not result.is_exact:
        return None
    return (
        result.params["growth"],
        result.params["divisor"],
        result.params["offset"],
    )
