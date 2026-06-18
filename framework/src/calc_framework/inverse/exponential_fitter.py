# SPDX-License-Identifier: AGPL-3.0
"""
指数公式拟合器。

公式：value = base × growth^(level-1) + offset

使用对数域线性回归拟合，当 offset=0 时有封闭解。
含 offset 时使用网格搜索 + 最小二乘法。
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from .base import FitResult, FormulaFitter


class ExponentialFormulaFitter(FormulaFitter):
    """指数公式拟合器。

    公式：value = base × growth^(level-1) + offset

    使用对数域线性回归拟合，当 offset=0 时有封闭解。
    含 offset 时使用网格搜索 + 最小二乘法。
    """

    def describe(self) -> dict[str, Any]:
        return {
            "name": "exponential",
            "description": "指数公式：value = base × growth^(level-1) + offset",
            "param_names": ["base", "growth", "offset"],
            "param_descriptions": {
                "base": "1 级基础值",
                "growth": "指数增长率 (>1 增长, <1 衰减)",
                "offset": "偏移量",
            },
            "required_options": [],
            "optional_options": {
                "offset_search_range": "offset 搜索范围（默认 200）",
            },
        }

    def fit(
        self,
        data: Sequence[int | float],
        *,
        num_levels: int | None = None,
        **options: Any,
    ) -> FitResult:
        if num_levels is None:
            num_levels = len(data)
        if num_levels < 2:
            return FitResult(max_error=0.0)

        offset_range = options.get("offset_search_range", 200)

        # 尝试不同的 offset 值，选择拟合最好的
        best_result: FitResult | None = None

        # 尝试 offset = 0（纯指数）
        result = self._fit_with_offset(data, num_levels, 0.0)
        if result is not None and result.is_exact:
            return result
        if result is not None and (best_result is None or result.max_error < best_result.max_error):
            best_result = result

        # 尝试基于数据的 offset 估计
        estimated_offset = self._estimate_offset(data)
        for offset_candidate in [
            estimated_offset,
            0.0,
            data[0] * 0.5 if data else 0,
            data[-1] * 0.1 if data else 0,
        ]:
            result = self._fit_with_offset(data, num_levels, offset_candidate)
            if result is not None and result.is_exact:
                return result
            if result is not None and (best_result is None or result.max_error < best_result.max_error):
                best_result = result

        # 网格搜索 offset（步长 1.0）
        lo = -offset_range
        hi = offset_range
        step = max(1.0, offset_range / 50.0)
        offset = lo
        while offset <= hi:
            result = self._fit_with_offset(data, num_levels, offset)
            if result is not None and result.is_exact:
                return result
            if result is not None and (best_result is None or result.max_error < best_result.max_error):
                best_result = result
            offset += step

        return best_result or FitResult(max_error=999999.0)

    def compute(
        self,
        params: dict[str, Any],
        num_levels: int = 1,
    ) -> list[float]:
        base = params["base"]
        growth = params["growth"]
        offset = params.get("offset", 0.0)
        return [round(base * (growth ** (lv - 1)) + offset, 4) for lv in range(1, num_levels + 1)]

    def validate(
        self,
        params: dict[str, Any],
        data: Sequence[int | float],
    ) -> FitResult:
        num_levels = len(data)
        computed = self.compute(params, num_levels)
        errors = [abs(computed[i] - data[i]) for i in range(num_levels)]
        max_error = max(errors) if errors else 0.0
        return FitResult(
            params=params,
            computed=computed,
            max_error=round(max_error, 6),
            is_exact=max_error < 0.05,
        )

    # ── 内部 ─────────────────────────────────

    @staticmethod
    def _estimate_offset(data: Sequence[int | float]) -> float:
        """通过最后一级与首级差值比粗略估计 offset。"""
        if len(data) < 3:
            return 0.0
        first, last = float(data[0]), float(data[-1])
        if last <= first:
            return 0.0
        return max(0.0, first - (last - first) * 0.3)

    @staticmethod
    def _fit_with_offset(
        data: Sequence[int | float],
        num_levels: int,
        offset: float,
    ) -> FitResult | None:
        """给定 offset，用对数域线性回归拟合 base 和 growth。"""
        try:
            ys = [float(v) - offset for v in data]
        except (TypeError, ValueError):
            return None

        # 确保全部 > 0
        if any(y <= 0 for y in ys):
            try:
                # 尝试小偏移微调
                min(y for y in ys if y > 0)
                ys = [max(y, 1e-10) for y in ys]
                if any(y <= 0 for y in ys):
                    return None
            except (ValueError, OverflowError):
                return None

        # 对数域线性回归：log(y) = log(base) + (lv-1) * log(growth)
        xs = [lv - 1 for lv in range(1, num_levels + 1)]
        log_ys: list[float] = []
        for y in ys:
            try:
                log_ys.append(math.log(float(y)))
            except (ValueError, OverflowError):
                return None

        n = num_levels
        sum_x = sum(xs)
        sum_y = sum(log_ys)
        sum_xy = sum(x * y for x, y in zip(xs, log_ys))
        sum_x2 = sum(x * x for x in xs)

        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return None

        log_growth = (n * sum_xy - sum_x * sum_y) / denominator
        log_base = (sum_y - log_growth * sum_x) / n

        growth = math.exp(log_growth)
        base = math.exp(log_base)

        # 计算误差
        computed = [base * (growth ** (lv - 1)) + offset for lv in range(1, num_levels + 1)]
        errors = [abs(computed[i] - float(data[i])) for i in range(num_levels)]
        max_error = max(errors)

        return FitResult(
            params={
                "base": round(base, 4),
                "growth": round(growth, 6),
                "offset": round(offset, 2),
            },
            computed=[round(v, 4) for v in computed],
            max_error=round(max_error, 6),
            is_exact=max_error < 0.05,
        )
