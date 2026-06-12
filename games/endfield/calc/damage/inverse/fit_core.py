# SPDX-License-Identifier: AGPL-3.0
"""
反推公式参数模块（薄适配层）

核心算法已迁移至框架 ``calc_framework.inverse``。
本模块通过 ``InverseEngine`` 公共 API 调用框架，不再直接访问私有方法。

``_find_best_params()`` 保留原始签名作为向后兼容层，
内部委托给 ``InverseEngine.fit()``。
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from typing import Any

from calc_framework.inverse.base import FloorFormulaFitter
from calc_framework.inverse.engine import InverseEngine
from calc_framework.logging import get_logger

_logger = get_logger(__name__)
_FITTER = FloorFormulaFitter()
_ENGINE = InverseEngine()


def _inverse_verbose() -> bool:
    """调试输出开关：环境变量 INVERSE_FIT_VERBOSE=1。"""
    return os.environ.get("INVERSE_FIT_VERBOSE", "").strip().lower() in ("1", "true", "yes")


def _inv_print(*args: Any, **kwargs: Any) -> None:
    """调试输出函数。"""
    if _inverse_verbose():
        _logger.debug(" ".join(str(a) for a in args))


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
    """查找最佳拟合参数（通过框架 InverseEngine 公共 API）。

    保持原始签名向后兼容。内部委托给 ``InverseEngine.fit()``。

    Returns:
        (growth, divisor, offset) 或 None（拟合失败）
    """
    # 将缩放后的数据还原为原始数据（框架 fit() 会自动处理缩放）
    if scale_factor != 1:
        original_data = [x / scale_factor for x in scaled_data]
    else:
        original_data = [float(x) for x in scaled_data]

    result = _ENGINE.fit(
        original_data,
        formula_id="floor_linear",
        num_levels=num_levels,
        divisor_range=divisor_range,
        growth_range=growth_range,
        offset_search_limit=offset_search_limit,
    )

    if not result.is_exact:
        return None

    params = result.params
    return (
        params["growth"],
        params["divisor"],
        params["offset"],
    )
