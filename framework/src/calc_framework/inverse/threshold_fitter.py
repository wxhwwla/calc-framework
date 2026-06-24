# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""
阈值公式拟合器。

公式：level <= threshold 时使用 pre_formula，
      level > threshold 时使用 post_formula。

典型场景：达到特定等级后切换成长模式（如线性→持平、慢速→快速）。
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from .base import FitResult, FormulaFitter


class ThresholdFormulaFitter(FormulaFitter):
    """阈值公式拟合器。

    公式：level <= threshold 时使用 pre_formula，
          level > threshold 时使用 post_formula。

    典型场景：达到特定等级后切换成长模式（如线性→持平、慢速→快速）。
    """

    def describe(self) -> dict[str, Any]:
        return {
            "name": "threshold",
            "description": "阈值公式：阈值前线性，阈值后切换到第二公式",
            "param_names": [
                "base",
                "threshold",
                "pre_growth",
                "post_growth",
                "post_is_flat",
            ],
            "param_descriptions": {
                "base": "1 级基础值",
                "threshold": "阈值等级（切换点）",
                "pre_growth": "阈值前每级成长值",
                "post_growth": "阈值后每级成长值（flat 模式忽略）",
                "post_is_flat": "阈值后是否持平（bool）",
            },
            "required_options": ["num_levels"],
            "optional_options": {
                "min_threshold": "最小阈值搜索（默认 3）",
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
        if num_levels < 4:
            return FitResult(max_error=0.0)

        min_threshold = options.get("min_threshold", 3)
        if min_threshold < 2:
            min_threshold = 2

        best_result: FitResult | None = None

        for threshold in range(min_threshold, num_levels - 1):
            # 拟合阈值前：线性
            pre_data = data[:threshold]
            pre_growth = self._fit_linear_growth(pre_data)
            if pre_growth is None:
                continue

            base = float(data[0])

            # 尝试 post 模式 1：持平（flat）
            flat_result = self._try_post_flat(data, num_levels, threshold, base, pre_growth)
            if flat_result is not None and flat_result.is_exact:
                return flat_result
            if flat_result is not None and (best_result is None or flat_result.max_error < best_result.max_error):
                best_result = flat_result

            # 尝试 post 模式 2：慢速/快速线性
            post_data = data[threshold:]
            post_growth = self._fit_linear_growth(post_data)
            if post_growth is not None:
                linear_result = self._try_post_linear(data, num_levels, threshold, base, pre_growth, post_growth)
                if linear_result is not None and linear_result.is_exact:
                    return linear_result
                if linear_result is not None and (best_result is None or linear_result.max_error < best_result.max_error):
                    best_result = linear_result

        return best_result or FitResult(max_error=999999.0)

    def compute(
        self,
        params: dict[str, Any],
        num_levels: int = 1,
    ) -> list[float]:
        base = float(params.get("base", 0))
        threshold = int(params.get("threshold", num_levels))
        pre_growth = float(params.get("pre_growth", 0))
        post_growth = float(params.get("post_growth", 0))
        post_is_flat = bool(params.get("post_is_flat", False))

        result: list[float] = []
        for lv in range(1, num_levels + 1):
            if lv <= threshold:
                result.append(base + pre_growth * (lv - 1))
            elif post_is_flat:
                result.append(base + pre_growth * (threshold - 1))
            else:
                result.append(base + pre_growth * (threshold - 1) + post_growth * (lv - threshold))

        return [round(v, 4) for v in result]

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
            max_error=max_error,
            is_exact=max_error < 0.001,
        )

    # ── 内部 ─────────────────────────────────

    @staticmethod
    def _fit_linear_growth(data: Sequence[int | float]) -> float | None:
        """用最小二乘法拟合增长率。"""
        n = len(data)
        if n < 2:
            return None
        try:
            xs = list(range(n))
            ys = [float(v) for v in data]
            sum_x = sum(xs)
            sum_y = sum(ys)
            sum_xy = sum(x * y for x, y in zip(xs, ys))
            sum_x2 = sum(x * x for x in xs)
            denom = n * sum_x2 - sum_x * sum_x
            if denom == 0:
                return None
            growth = (n * sum_xy - sum_x * sum_y) / denom
            return round(growth, 4)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _try_post_flat(
        data: Sequence[int | float],
        num_levels: int,
        threshold: int,
        base: float,
        pre_growth: float,
    ) -> FitResult | None:
        """尝试阈值后持平模式。"""
        computed: list[float] = []
        for lv in range(1, num_levels + 1):
            if lv <= threshold:
                computed.append(base + pre_growth * (lv - 1))
            else:
                computed.append(base + pre_growth * (threshold - 1))

        errors = [abs(computed[i] - float(data[i])) for i in range(num_levels)]
        max_error = max(errors)

        return FitResult(
            params={
                "base": int(base) if base == int(base) else base,
                "threshold": threshold,
                "pre_growth": int(pre_growth) if pre_growth == int(pre_growth) else pre_growth,
                "post_growth": 0.0,
                "post_is_flat": True,
            },
            computed=[round(v, 4) for v in computed],
            max_error=max_error,
            is_exact=max_error < 0.001,
        )

    @staticmethod
    def _try_post_linear(
        data: Sequence[int | float],
        num_levels: int,
        threshold: int,
        base: float,
        pre_growth: float,
        post_growth: float,
    ) -> FitResult | None:
        """尝试阈值后线性模式。"""
        computed: list[float] = []
        for lv in range(1, num_levels + 1):
            if lv <= threshold:
                computed.append(base + pre_growth * (lv - 1))
            else:
                computed.append(base + pre_growth * (threshold - 1) + post_growth * (lv - threshold))

        errors = [abs(computed[i] - float(data[i])) for i in range(num_levels)]
        max_error = max(errors)

        return FitResult(
            params={
                "base": int(base) if base == int(base) else base,
                "threshold": threshold,
                "pre_growth": int(pre_growth) if pre_growth == int(pre_growth) else pre_growth,
                "post_growth": int(post_growth) if post_growth == int(post_growth) else post_growth,
                "post_is_flat": False,
            },
            computed=[round(v, 4) for v in computed],
            max_error=max_error,
            is_exact=max_error < 0.001,
        )
