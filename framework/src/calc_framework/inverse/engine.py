# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""
通用反推引擎 — 拟合 / 正向计算 / 验证三合一入口。

用法::

    from calc_framework.inverse.engine import InverseEngine

    engine = InverseEngine()

    # ── 最简调用：数据 ⇄ 参数 ──
    data = [100, 105, 110, 115, 120, 125, 130, 135, 140]

    # 反向：数据 → 4 参数
    params = engine.data_to_params(data)
    print(params.base, params.growth, params.divisor, params.offset)

    # 正向：4 参数 + 等级 → 曲线
    curve = engine.params_to_curve(params, num_levels=90)

    # ── 完整调用 ──
    result = engine.fit(data, "floor_linear")
    print(result.summary())

    # 自动探测公式类型
    result = engine.fit_auto(data)
    print(result.summary())

    # 验证
    validation = engine.validate("floor_linear", result.params, data)
    print(f"精确匹配: {validation.is_exact}")
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from calc_framework.logging import get_logger

from .base import FitResult, GrowthParams
from .registry import registry

logger = get_logger(__name__)


class InverseEngine:
    """通用公式反推引擎。

    封装注册表查找 + FormulaFitter 调用，提供一站式接口。

    核心方法分两层：

    - **底层**：``fit()`` / ``compute()`` / ``validate()`` / ``fit_auto()``
      — 完整的公式类型控制
    - **便捷层**：``data_to_params()`` / ``params_to_curve()``
      — 一行调用完成双向转换，适合"给数据得参数"或"给参数得曲线"的场景
    """

    # ── 底层 API（保持向后兼容）──────────────────

    def fit(
        self,
        data: Sequence[int | float],
        formula_id: str = "floor_linear",
        *,
        num_levels: int | None = None,
        **options: Any,
    ) -> FitResult:
        """从等级数据反推公式参数。

        Args:
            data: 各等级的观测值
            formula_id: 公式类型 ID（默认 "floor_linear"）
            num_levels: 等级数（自动从 data 推断）
            options: 透传给 FormulaFitter.fit() 的额外参数

        Returns:
            FitResult 包含拟合参数
        """
        ft = registry.get(formula_id)
        return ft.fitter.fit(data, num_levels=num_levels, **options)

    def fit_auto(
        self,
        data: Sequence[int | float],
        **options: Any,
    ) -> tuple[str, FitResult] | None:
        """尝试所有注册的公式类型，选择误差最小的结果。

        Args:
            data: 各等级的观测值
            options: 透传参数

        Returns:
            (formula_id, FitResult) 元组，或 None（全部失败）
        """
        best_result: FitResult | None = None
        best_id = ""
        best_error = float("inf")
        failures = 0

        for ft in registry.list_types():
            try:
                result = ft.fitter.fit(data, **options)
                if result.max_error < best_error:
                    best_error = result.max_error
                    best_result = result
                    best_id = ft.id
            except Exception:
                failures += 1
                logger.debug(
                    "fit_auto: 公式 %s 拟合失败，已跳过",
                    ft.id,
                    exc_info=True,
                )
                continue

        if best_result is None and failures:
            logger.warning(
                "fit_auto: 全部 %d 个公式类型拟合失败",
                failures,
            )

        return (best_id, best_result) if best_result else None

    def compute(
        self,
        formula_id: str,
        params: dict[str, Any] | GrowthParams,
        num_levels: int = 1,
        *,
        level_overrides: dict[int, float] | None = None,
    ) -> list[float]:
        """用参数正向计算各等级值。

        Args:
            formula_id: 公式类型 ID
            params: 参数 dict 或 GrowthParams
            num_levels: 要计算的等级数
            level_overrides: 等级 → 固定值映射（1-based）。用于技能特殊值场景。
        """
        if isinstance(params, GrowthParams):
            params = params.to_dict()
        ft = registry.get(formula_id)
        return ft.fitter.compute(params, num_levels, level_overrides=level_overrides)  # type: ignore[call-arg]

    def validate(
        self,
        formula_id: str,
        params: dict[str, Any] | GrowthParams,
        data: Sequence[int | float],
    ) -> FitResult:
        """验证参数与观测数据的一致性。"""
        if isinstance(params, GrowthParams):
            params = params.to_dict()
        ft = registry.get(formula_id)
        return ft.fitter.validate(params, data)

    def list_formula_types(self) -> list[dict]:
        """列出所有注册的公式类型元信息。"""
        return [ft.to_dict() for ft in registry.list_types()]

    # ── 便捷层（新增）────────────────────────────

    def data_to_params(
        self,
        data: Sequence[int | float],
        formula_id: str = "floor_linear",
        **options: Any,
    ) -> GrowthParams:
        """数据 → 4 参数（最简调用）。

        一行代码完成反推，返回类型安全的 GrowthParams。

        Usage::

            engine = InverseEngine()
            params = engine.data_to_params([100, 105, 110, 115, 120])
            # GrowthParams(base=100, growth=5, divisor=1, offset=0)

        Args:
            data: 各等级的观测值（索引 0 = 等级 1）
            formula_id: 公式类型 ID
            options: 透传搜索选项

        Returns:
            GrowthParams 包含拟合参数

        Raises:
            ValueError: 拟合失败时
        """
        result = self.fit(data, formula_id, **options)
        if result.growth_params is None:
            raise ValueError(f"拟合失败：无法从 data (len={len(data)}) 提取 {formula_id} 参数。 max_error={result.max_error}")
        return result.growth_params

    def params_to_curve(
        self,
        params: GrowthParams | dict[str, Any],
        num_levels: int,
        formula_id: str = "floor_linear",
        *,
        level_overrides: dict[int, float] | None = None,
    ) -> list[float]:
        """4 参数 + 等级 → 数据曲线（最简调用）。

        一行代码完成正向计算。

        Usage::

            engine = InverseEngine()
            params = GrowthParams(base=100, growth=5, divisor=1, offset=0)
            curve = engine.params_to_curve(params, num_levels=90)
            # [100.0, 105.0, 110.0, ..., 545.0]

            # 带特殊值
            curve = engine.params_to_curve(params, num_levels=12,
                                           level_overrides={10: 200.0, 11: 220.0, 12: 240.0})

        Args:
            params: 公式参数（GrowthParams 或 dict）
            num_levels: 要计算的等级数
            formula_id: 公式类型 ID
            level_overrides: 等级 → 固定值映射（1-based）

        Returns:
            各等级值列表（索引 0 = 等级 1）
        """
        return self.compute(formula_id, params, num_levels, level_overrides=level_overrides)
