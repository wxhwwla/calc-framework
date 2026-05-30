"""
高级公式拟合器：指数 / 分段 / 阈值。

每个拟合器继承 ``FormulaFitter`` ABC，实现完整的
``describe`` / ``fit`` / ``compute`` / ``validate`` SPI。
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
        return [
            round(base * (growth ** (lv - 1)) + offset, 4)
            for lv in range(1, num_levels + 1)
        ]

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
                min_y = min(y for y in ys if y > 0)
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
                "base", "segments",
                "segment_1_end", "segment_1_growth",
                "segment_2_end", "segment_2_growth",
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
        best_breakpoint: int | None = None

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
                best_breakpoint = bp

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
                "base", "threshold", "pre_growth", "post_growth", "post_is_flat",
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
                linear_result = self._try_post_linear(
                    data, num_levels, threshold, base, pre_growth, post_growth)
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
