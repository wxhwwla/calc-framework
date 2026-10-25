# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""
分段公式拟合器。

公式：多段线性公式，每段独立计算。
支持自动检测断点（2 段），也支持指定断点。
段内公式：value = segment_base + growth × (lv - segment_start)
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from .base import FitResult, FormulaFitter


class PiecewiseFormulaFitter(FormulaFitter):
    """分段公式拟合器。

    公式：多段线性公式，每段独立计算。
    支持自动检测断点（2 段），也支持指定断点。
    段内公式：value = segment_base + growth × (lv - segment_start)
    """

    def describe(self) -> dict[str, Any]:
        return {
            "name": "piecewise",
            "description": "分段公式：多段线性，自动检测断点",
            "param_names": [
                "base",
                "segments",
                "segment_1_end",
                "segment_1_growth",
                "segment_2_end",
                "segment_2_growth",
            ],
            "param_descriptions": {
                "base": "1 级基础值",
                "segments": "段数",
                "segment_N_end": "第 N 段结束等级",
                "segment_N_growth": "第 N 段成长值",
            },
            "required_options": ["num_levels"],
            "optional_options": {
                "num_segments": "段数（默认 2）",
                "min_segment_size": "最小段长度（默认 3）",
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

        num_segments = options.get("num_segments", 2)
        min_segment_size = options.get("min_segment_size", 3)

        # 自动检测断点（对 2 段做穷举搜索，更多段暂不支持自动）
        if num_segments == 2:
            return self._fit_two_segments(data, num_levels, min_segment_size)

        return FitResult(max_error=999999.0)

    def compute(
        self,
        params: dict[str, Any],
        num_levels: int = 1,
    ) -> list[float]:
        base = float(params.get("base", 0))
        segments = params.get("segments", 1)

        # 构建段配置
        seg_ends: list[int] = []
        seg_growths: list[float] = []
        for i in range(1, segments + 1):
            seg_ends.append(int(params.get(f"segment_{i}_end", num_levels)))
            seg_growths.append(float(params.get(f"segment_{i}_growth", 0)))

        result: list[float] = []
        prev_val = base

        for lv in range(1, num_levels + 1):
            if lv == 1:
                val = base
            else:
                growth = self._growth_for_level(lv, seg_ends, seg_growths)
                val = prev_val + growth
            result.append(val)
            prev_val = val

        return [round(v, 4) for v in result]

    @staticmethod
    def _growth_for_level(lv: int, seg_ends: list[int], seg_growths: list[float]) -> float:
        """返回指定等级的增长率。"""
        for end, growth in zip(seg_ends, seg_growths):
            if lv <= end:
                return growth
        return seg_growths[-1] if seg_growths else 0.0

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

    def _fit_two_segments(
        self,
        data: Sequence[int | float],
        num_levels: int,
        min_segment_size: int,
    ) -> FitResult:
        """尝试所有可能的断点位置，选择最好拟合。"""
        best_result: FitResult | None = None

        for bp in range(min_segment_size + 1, num_levels - min_segment_size):
            # 段 1：level 1..bp
            seg1_data = data[:bp]
            g1 = self._fit_linear_segment(seg1_data)
            if g1 is None:
                continue

            # 段 2：level bp+1..num_levels
            seg2_data = data[bp:]
            g2 = self._fit_linear_segment(seg2_data)
            if g2 is None:
                continue

            # 计算完整拟合值
            base = float(data[0])
            computed: list[float] = []
            for lv in range(1, num_levels + 1):
                if lv <= bp:
                    computed.append(base + g1 * (lv - 1))
                else:
                    seg2_start_val = base + g1 * (bp - 1)
                    computed.append(seg2_start_val + g2 * (lv - bp))

            errors = [abs(computed[i] - float(data[i])) for i in range(num_levels)]
            max_error = max(errors)

            if max_error < 0.001:
                return FitResult(
                    params={
                        "base": int(base) if base == int(base) else base,
                        "segments": 2,
                        "segment_1_end": bp,
                        "segment_1_growth": int(g1) if g1 == int(g1) else g1,
                        "segment_2_end": num_levels,
                        "segment_2_growth": int(g2) if g2 == int(g2) else g2,
                    },
                    computed=[round(v, 4) for v in computed],
                    max_error=0.0,
                    is_exact=True,
                )

            if best_result is None or max_error < best_result.max_error:
                best_result = FitResult(
                    params={
                        "base": int(base) if base == int(base) else base,
                        "segments": 2,
                        "segment_1_end": bp,
                        "segment_1_growth": int(g1) if g1 == int(g1) else g1,
                        "segment_2_end": num_levels,
                        "segment_2_growth": int(g2) if g2 == int(g2) else g2,
                    },
                    computed=[round(v, 4) for v in computed],
                    max_error=max_error,
                    is_exact=max_error < 0.001,
                )

        return best_result or FitResult(max_error=999999.0)

    @staticmethod
    def _fit_linear_segment(data: Sequence[int | float]) -> float | None:
        """用最小二乘法拟合一个段的增长率。"""
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
