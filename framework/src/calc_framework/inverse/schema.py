# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""
逆推引擎 — 游戏适配层抽象。

提供 ``InverseSchema``（声明式数据模式）和 ``GameInverseAdapter`` ABC，
让新游戏通过声明式配置接入逆推引擎，无需手写 if/elif 分派逻辑。

Usage::

    from calc_framework.inverse.schema import InverseSchema, GameInverseAdapter

    class MyGameAdapter(GameInverseAdapter):
        @property
        def schemas(self):
            return [
                InverseSchema(length=60, label="属性成长"),
                InverseSchema(length=20, label="技能倍率"),
            ]

        def default_formula(self) -> str:
            return "floor_linear"

    adapter = MyGameAdapter()
    result = adapter.fit(data)           # 自动按长度匹配
    curve = adapter.compute(result.growth_params, num_levels=60)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from .base import FitResult, GrowthParams
from .engine import InverseEngine


@dataclass
class InverseSchema:
    """描述一种数据格式与公式类型的映射关系。

    替代手写 ``if len(data) == N: ...`` 的分派逻辑。
    每个 schema 定义：期望的数据长度、使用的公式类型、特殊值位置、自定义搜索选项。

    Usage::

        # 90 级属性数据
        InverseSchema(length=90, label="属性成长")

        # 12 级技能倍率，第 10-12 级为特殊值
        InverseSchema(length=12, label="技能倍率(12级)", special_indices=[9, 10, 11])

        # 自定义搜索范围
        InverseSchema(length=30, label="自定义",
                      search_options={"divisor_range": (1, 100), "growth_range": (1, 200)})
    """

    length: int
    """期望的数据长度。"""

    key: str = ""
    """可选唯一键；同长度多模式时用于 ``fit_with_key`` 精确匹配。"""

    formula_id: str = "floor_linear"
    """使用的公式类型 ID。"""

    label: str = ""
    """人类可读标签（用于调试和错误消息）。"""

    special_indices: list[int] | None = None
    """特殊值在数据中的索引位置（0-based）。

    例如技能 10-12 级为特殊值（不参与公式拟合）:
        special_indices=[9, 10, 11]
    """

    search_options: dict[str, Any] | None = None
    """自定义搜索选项，透传给 FormulaFitter.fit()。

    例如: {"divisor_range": (1, 201), "growth_range": (1, 301)}
    """

    def extract_base_data(self, data: Sequence[float]) -> Sequence[float]:
        """从完整数据中提取参与公式拟合的基础数据（排除特殊值）。"""
        if self.special_indices is None:
            return data
        special_set = set(self.special_indices)
        return [v for i, v in enumerate(data) if i not in special_set]

    def extract_special_values(self, data: Sequence[float]) -> list[float]:
        """从完整数据中提取特殊值。"""
        if self.special_indices is None:
            return []
        return [data[i] for i in self.special_indices if i < len(data)]


class GameInverseAdapter(ABC):
    """游戏适配器的逆推入口 ABC。

    每个游戏实现一个子类，声明其数据模式（schemas），框架自动处理：
    - 按数据长度匹配 schema
    - 调用 InverseEngine 执行拟合
    - 正向计算与验证

    最简实现::

        class MyGameInverse(GameInverseAdapter):
            @property
            def schemas(self):
                return [
                    InverseSchema(length=60, label="属性成长"),
                    InverseSchema(length=10, label="技能倍率",
                                  special_indices=[9]),
                ]

            def default_formula(self) -> str:
                return "floor_linear"

        adapter = MyGameInverse()
        result = adapter.fit(some_data)
        curve = adapter.compute(result.growth_params, num_levels=60)
    """

    def __init__(self, engine: InverseEngine | None = None):
        self._engine = engine or InverseEngine()

    # ── 子类必须实现 ────────────────────────────

    @property
    @abstractmethod
    def schemas(self) -> list[InverseSchema]:
        """该游戏支持的数据模式列表。

        按数据长度定义每种模式。fit() 时自动匹配。
        """
        ...

    @abstractmethod
    def default_formula(self) -> str:
        """默认公式类型 ID。

        用于正向计算等场景。
        """
        ...

    # ── 子类可选覆盖 ────────────────────────────

    def fit_special_logic(
        self,
        schema: InverseSchema,
        base_data: Sequence[float],
        result: FitResult,
        original_data: Sequence[float],
    ) -> FitResult:
        """拟合后的后处理钩子。

        子类可覆盖此方法，对拟合结果做游戏特定的调整
        （如注入特殊值到 params、应用游戏特定的校验等）。
        默认不做任何处理。

        Args:
            schema: 匹配到的数据模式
            base_data: 参与拟合的基础数据（已排除特殊值）
            result: 框架拟合结果
            original_data: 完整的原始数据（含特殊值）

        Returns:
            处理后的 FitResult
        """
        return result

    def on_no_match(self, data: Sequence[float]) -> None:
        """无匹配 schema 时的处理钩子。默认抛出 ValueError。

        子类可覆盖以实现自定义降级策略。
        """
        supported = ", ".join(str(s.length) for s in self.schemas)
        raise ValueError(f"不支持的数据长度: {len(data)}。支持的长度: {supported}")

    # ── 公共方法 ────────────────────────────────

    def fit(self, data: Sequence[float]) -> FitResult:
        """自动按数据长度匹配 schema 并拟合。

        遍历 schemas，找到 length 匹配的 schema，调用 InverseEngine 执行拟合。
        如果 schema 定义了 special_indices，自动排除特殊值后拟合。

        Args:
            data: 各等级的观测值

        Returns:
            FitResult 包含拟合参数

        Raises:
            ValueError: 无匹配的 schema 时
        """
        matched = [s for s in self.schemas if len(data) == s.length]
        if len(matched) == 1:
            return self._fit_with_schema(matched[0], data)
        if len(matched) > 1:
            keys = ", ".join(s.key or s.label or str(s.length) for s in matched)
            raise ValueError(f"数据长度 {len(data)} 匹配多个 schema（{keys}），请使用 fit_with_key() 指定 key。")
        self.on_no_match(data)
        raise RuntimeError("on_no_match 应已抛出异常")  # unreachable, satisfies type checker

    def fit_with_key(self, data: Sequence[float], schema_key: str) -> FitResult:
        """按 schema.key 精确匹配并拟合。"""
        for schema in self.schemas:
            if schema.key == schema_key:
                if len(data) != schema.length:
                    raise ValueError(f"schema '{schema_key}' 期望长度 {schema.length}，实际 {len(data)}")
                return self._fit_with_schema(schema, data)
        supported = ", ".join(s.key for s in self.schemas if s.key)
        raise ValueError(f"未知 schema key: {schema_key}。已注册: {supported}")

    def _fit_with_schema(self, schema: InverseSchema, data: Sequence[float]) -> FitResult:
        """对单个 schema 执行拟合流程。"""
        base_data = schema.extract_base_data(data)
        special_values = schema.extract_special_values(data)
        options = schema.search_options or {}

        result = self._engine.fit(
            base_data,
            formula_id=schema.formula_id,
            **options,
        )

        if special_values and result.params:
            result.params["special_values"] = special_values

        return self.fit_special_logic(schema, base_data, result, data)

    def compute(
        self,
        params: GrowthParams | dict[str, Any],
        num_levels: int,
        formula_id: str | None = None,
    ) -> list[float]:
        """正向计算成长曲线。

        Args:
            params: 公式参数
            num_levels: 要计算的等级数
            formula_id: 公式类型（默认使用 default_formula()）

        Returns:
            各等级值列表
        """
        fid = formula_id or self.default_formula()
        return self._engine.compute(fid, params, num_levels)

    def validate(
        self,
        params: GrowthParams | dict[str, Any],
        data: Sequence[float],
        formula_id: str | None = None,
    ) -> FitResult:
        """验证参数与数据的一致性。

        Args:
            params: 公式参数
            data: 观测数据
            formula_id: 公式类型（默认使用 default_formula()）

        Returns:
            FitResult 含 max_error 和 is_exact
        """
        fid = formula_id or self.default_formula()
        return self._engine.validate(fid, params, data)

    def data_to_params(self, data: Sequence[float]) -> GrowthParams:
        """数据 → 参数（便捷方法）。

        等价于 ``self.fit(data).growth_params``，失败时抛出 ValueError。
        """
        result = self.fit(data)
        if result.growth_params is None:
            raise ValueError(f"拟合失败：无法从 data (len={len(data)}) 提取参数。 max_error={result.max_error}")
        return result.growth_params
