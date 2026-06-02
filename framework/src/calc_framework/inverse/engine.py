# SPDX-License-Identifier: AGPL-3.0
"""
通用反推引擎 — 拟合 / 正向计算 / 验证三合一入口。

用法::

    from calc_framework.inverse.engine import InverseEngine

    engine = InverseEngine()
    data = [100, 105, 110, 115, 120, 125, 130, 135, 140]

    # 通用 floor 线性公式
    result = engine.fit(data, "floor_linear")
    print(result.summary())

    # 不指定公式类型时自动探测
    result = engine.fit_auto(data)
    print(result.summary())

    # 正向计算
    computed = engine.compute("floor_linear", result.params, num_levels=9)

    # 验证
    validation = engine.validate("floor_linear", result.params, data)
    print(f"精确匹配: {validation.is_exact}")
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from .registry import registry


class InverseEngine:
    """通用公式反推引擎。

    封装注册表查找 + FormulaFitter 调用，提供一站式接口。
    """

    def fit(
        self,
        data: Sequence[int | float],
        formula_id: str = "floor_linear",
        *,
        num_levels: int | None = None,
        **options: Any,
    ) -> Any:
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
    ) -> Any:
        """尝试所有注册的公式类型，选择误差最小的结果。

        Args:
            data: 各等级的观测值
            options: 透传参数

        Returns:
            (formula_id, FitResult) 元组，或 None（全部失败）
        """
        best_result = None
        best_id = None
        best_error = float("inf")

        for ft in registry.list_types():
            try:
                result = ft.fitter.fit(data, **options)
                if result.max_error < best_error:
                    best_error = result.max_error
                    best_result = result
                    best_id = ft.id
            except Exception:
                continue

        return (best_id, best_result) if best_result else None

    def compute(
        self,
        formula_id: str,
        params: dict[str, Any],
        num_levels: int = 1,
    ) -> list[float]:
        """用参数正向计算各等级值。"""
        ft = registry.get(formula_id)
        return ft.fitter.compute(params, num_levels)

    def validate(
        self,
        formula_id: str,
        params: dict[str, Any],
        data: Sequence[int | float],
    ) -> Any:
        """验证参数与观测数据的一致性。"""
        ft = registry.get(formula_id)
        return ft.fitter.validate(params, data)

    def list_formula_types(self) -> list[dict]:
        """列出所有注册的公式类型元信息。"""
        return [ft.to_dict() for ft in registry.list_types()]
