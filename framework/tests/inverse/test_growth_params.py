# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""
GrowthParams / InverseEngine 便捷方法 / GameInverseAdapter 测试。

覆盖 ADR-0024 新增的完全抽象化 API。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from calc_framework.inverse.base import FitResult, GrowthParams
from calc_framework.inverse.engine import InverseEngine
from calc_framework.inverse.schema import GameInverseAdapter, InverseSchema

# =========================================================================
# GrowthParams
# =========================================================================


class TestGrowthParams:
    """GrowthParams 类型化参数容器。"""

    def test_create_and_to_dict(self):
        p = GrowthParams(base=100, growth=5, divisor=1, offset=2)
        d = p.to_dict()
        assert d == {"base": 100, "growth": 5, "divisor": 1, "offset": 2, "is_decimal": False}

    def test_from_dict_roundtrip(self):
        d = {"base": 100, "growth": 5, "divisor": 3, "offset": 0, "is_decimal": True}
        p = GrowthParams.from_dict(d)
        assert p.base == 100
        assert p.growth == 5
        assert p.divisor == 3

    def test_tuple(self):
        p = GrowthParams(base=100, growth=5, divisor=3, offset=1)
        assert p.tuple() == (100, 5, 3, 1)

    def test_special_values(self):
        p = GrowthParams(base=100, growth=5, divisor=1, special_values=[23.4])
        d = p.to_dict()
        assert d["special_values"] == [23.4]
        p2 = GrowthParams.from_dict(d)
        assert p2.special_values == [23.4]

    def test_defaults(self):
        p = GrowthParams(base=100, growth=5, divisor=1)
        assert p.offset == 0.0
        assert p.is_decimal is False
        assert p.special_values is None

    def test_fitresult_growth_params(self):
        r = FitResult(
            params={"base": 100, "growth": 5, "divisor": 1, "offset": 0, "is_decimal": False},
            is_exact=True,
        )
        gp = r.growth_params
        assert gp is not None
        assert gp.base == 100

    def test_fitresult_growth_params_incomplete(self):
        r = FitResult(params={"foo": 1}, is_exact=False)
        assert r.growth_params is None


# =========================================================================
# InverseEngine 便捷方法
# =========================================================================


class TestInverseEngineConvenience:
    """data_to_params / params_to_curve。"""

    def test_data_to_params(self):
        engine = InverseEngine()
        data = [100 + i * 5 for i in range(9)]
        params = engine.data_to_params(data)
        assert isinstance(params, GrowthParams)
        assert params.base == 100
        assert params.growth == 5

    def test_data_to_params_any_levels(self):
        """任何等级数。"""
        engine = InverseEngine()
        data = [200 + i * 3 for i in range(60)]
        params = engine.data_to_params(data)
        assert params.base == 200

    def test_params_to_curve(self):
        engine = InverseEngine()
        params = GrowthParams(base=100, growth=5, divisor=1)
        curve = engine.params_to_curve(params, num_levels=9)
        expected = [100.0, 105.0, 110.0, 115.0, 120.0, 125.0, 130.0, 135.0, 140.0]
        assert curve == expected

    def test_roundtrip(self):
        """data → params → curve = 原始数据。"""
        engine = InverseEngine()
        original = [100 + i * 7 for i in range(30)]
        params = engine.data_to_params(original)
        curve = engine.params_to_curve(params, num_levels=30)
        assert curve == original

    def test_params_to_curve_accepts_dict(self):
        """接受 dict 参数（向后兼容）。"""
        engine = InverseEngine()
        curve = engine.params_to_curve({"base": 100, "growth": 2, "divisor": 1}, num_levels=5)
        assert curve == [100.0, 102.0, 104.0, 106.0, 108.0]

    def test_roundtrip_with_divisor(self):
        """带 divisor 和 offset 的双向转换。"""
        import math

        engine = InverseEngine()
        base, growth, divisor, offset = 29, 163, 57, 3
        data = [base + math.floor((growth * (lv - 1) + offset) / divisor) for lv in range(1, 91)]
        params = engine.data_to_params(data)
        curve = engine.params_to_curve(params, num_levels=90)
        assert curve == data


# =========================================================================
# GameInverseAdapter + InverseSchema
# =========================================================================


class TestGameInverseAdapter:
    """游戏适配器 ABC。"""

    def test_basic_adapter(self):
        class MiniGame(GameInverseAdapter):
            @property
            def schemas(self):
                return [
                    InverseSchema(length=10, label="属性"),
                    InverseSchema(length=5, label="技能", special_indices=[4]),
                ]

            def default_formula(self):
                return "floor_linear"

        adapter = MiniGame()
        data = [100 + i * 5 for i in range(10)]
        result = adapter.fit(data)
        assert result.is_exact
        assert result.params["base"] == 100

    def test_special_values_auto_extract(self):
        class MiniGame(GameInverseAdapter):
            @property
            def schemas(self):
                return [InverseSchema(length=5, label="技能", special_indices=[4])]

            def default_formula(self):
                return "floor_linear"

        adapter = MiniGame()
        data = [10, 15, 20, 25, 999]  # 第 5 级特殊值
        result = adapter.fit(data)
        assert result.is_exact
        assert result.params["special_values"] == [999]

    def test_adapter_compute(self):
        class MiniGame(GameInverseAdapter):
            @property
            def schemas(self):
                return [InverseSchema(length=10)]

            def default_formula(self):
                return "floor_linear"

        adapter = MiniGame()
        params = GrowthParams(base=50, growth=3, divisor=1)
        curve = adapter.compute(params, num_levels=10)
        assert curve == [50.0 + i * 3 for i in range(10)]

    def test_no_match_raises(self):
        class MiniGame(GameInverseAdapter):
            @property
            def schemas(self):
                return [InverseSchema(length=10)]

            def default_formula(self):
                return "floor_linear"

        adapter = MiniGame()
        with pytest.raises(ValueError, match="不支持的数据长度"):
            adapter.fit([1, 2, 3])

    def test_custom_search_options(self):
        class MiniGame(GameInverseAdapter):
            @property
            def schemas(self):
                return [
                    InverseSchema(
                        length=30,
                        search_options={"growth_range": (1, 10), "divisor_range": (1, 5)},
                    ),
                ]

            def default_formula(self):
                return "floor_linear"

        adapter = MiniGame()
        data = [10 + i * 2 for i in range(30)]
        result = adapter.fit(data)
        assert result.is_exact

    def test_data_to_params(self):
        class MiniGame(GameInverseAdapter):
            @property
            def schemas(self):
                return [InverseSchema(length=10)]

            def default_formula(self):
                return "floor_linear"

        adapter = MiniGame()
        data = [100 + i * 5 for i in range(10)]
        params = adapter.data_to_params(data)
        assert isinstance(params, GrowthParams)
        assert params.base == 100


# =========================================================================
# InverseSchema 独立功能
# =========================================================================


class TestInverseSchema:
    """InverseSchema 数据提取。"""

    def test_extract_base_data_no_special(self):
        schema = InverseSchema(length=10)
        data = list(range(10))
        assert schema.extract_base_data(data) == data

    def test_extract_base_data_with_special(self):
        schema = InverseSchema(length=12, special_indices=[9, 10, 11])
        data = list(range(12))
        base = schema.extract_base_data(data)
        assert base == list(range(9))
        assert schema.extract_special_values(data) == [9, 10, 11]
