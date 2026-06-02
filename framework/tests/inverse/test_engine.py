# SPDX-License-Identifier: AGPL-3.0
"""
框架通用反推引擎 — 完整测试。

覆盖场景：
- FloorFormulaFitter：整数/小数/不同长度/精确/近似
- InverseEngine：fit / compute / validate / fit_auto
- 跨游戏验证：card_rpg 公式类型
- 边界条件：空数据、单点、重复值、大数值
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

# path setup
_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from calc_framework.inverse.base import FloorFormulaFitter
from calc_framework.inverse.engine import InverseEngine
from calc_framework.inverse.registry import FormulaType, Registry, registry

# =========================================================================
# FloorFormulaFitter — 基础拟合功能
# =========================================================================


class TestFloorFormulaFitter:
    """Floor 线性公式拟合器的基本拟合功能。"""

    def test_linear_integer(self):
        """简单线性增长（整数，divisor=1，无 offset）。"""
        data = [100 + i * 5 for i in range(9)]
        result = FloorFormulaFitter().fit(data)
        assert result.is_exact, f"应精确匹配，实际 max_error={result.max_error}"
        assert result.params["base"] == 100
        assert result.params["growth"] == 5
        assert result.params["divisor"] == 1
        assert result.params["offset"] == 0

    def test_linear_integer_90_levels(self):
        """90 级属性数据。"""
        data = [100 + i * 3 for i in range(90)]
        result = FloorFormulaFitter().fit(data)
        assert result.is_exact
        assert result.params["growth"] == 3
        assert result.params["divisor"] == 1

    def test_with_divisor(self):
        """有 divisor 的 floor 公式。"""
        base, growth, divisor, offset = 29, 163, 57, 3
        data = [
            base + math.floor((growth * (lv - 1) + offset) / divisor)
            for lv in range(1, 91)
        ]
        result = FloorFormulaFitter().fit(data)
        assert result.is_exact, f"应精确匹配，实际 max_error={result.max_error}"
        assert result.params["base"] == base

    def test_configurable_ranges(self):
        """自定义搜索范围。"""
        data = [50 + i * 2 for i in range(10)]
        result = FloorFormulaFitter().fit(
            data,
            divisor_range=(1, 10),
            growth_range=(1, 50),
        )
        assert result.is_exact
        assert result.params["growth"] == 2

    def test_approx_fit(self):
        """近似解（小幅随机扰动）。"""
        base, growth, divisor = 100, 7, 3
        data = [
            base + math.floor((growth * (lv - 1)) / divisor)
            for lv in range(1, 21)
        ]
        data[-1] += 1  # 最后一级加 1
        result = FloorFormulaFitter().fit(data)
        # 应该能找到近似解（不是精确）
        assert not result.is_exact or result.max_error < 2.0


# =========================================================================
# FloorFormulaFitter — compute / validate
# =========================================================================


class TestFloorFormulaCompute:
    """正向计算与验证。"""

    def test_compute_consistency(self):
        """fit → compute 应该得到原始数据。"""
        fitter = FloorFormulaFitter()
        data = [200 + i * 7 for i in range(30)]
        result = fitter.fit(data)
        assert result.is_exact
        computed = fitter.compute(result.params, num_levels=30)
        assert computed == data

    def test_validate_exact(self):
        """精确匹配的验证。"""
        fitter = FloorFormulaFitter()
        data = [100 + i * 5 for i in range(9)]
        result = fitter.fit(data)
        validation = fitter.validate(result.params, data)
        assert validation.is_exact

    def test_validate_mismatch(self):
        """不匹配数据的验证报告合理误差。"""
        fitter = FloorFormulaFitter()
        params = {"base": 100, "growth": 5, "divisor": 1, "offset": 0, "is_decimal": False}
        data = [100, 106, 110, 115, 120]  # 第二级故意不匹配
        result = fitter.validate(params, data)
        assert not result.is_exact
        assert result.max_error > 0


# =========================================================================
# InverseEngine — 统一入口
# =========================================================================


class TestInverseEngine:
    """InverseEngine 统一入口。"""

    def test_fit_via_engine(self):
        engine = InverseEngine()
        data = [100 + i * 5 for i in range(9)]
        result = engine.fit(data, "floor_linear")
        assert result.is_exact
        assert result.params["base"] == 100

    def test_unknown_formula_type(self):
        engine = InverseEngine()
        with pytest.raises(KeyError):
            engine.fit([1, 2, 3], "nonexistent")

    def test_fit_auto(self):
        engine = InverseEngine()
        data = [100 + i * 5 for i in range(9)]
        auto = engine.fit_auto(data)
        assert auto is not None
        formula_id, result = auto
        assert formula_id == "floor_linear"
        assert result.is_exact

    def test_compute_via_engine(self):
        engine = InverseEngine()
        data = [100 + i * 5 for i in range(9)]
        result = engine.fit(data, "floor_linear")
        computed = engine.compute("floor_linear", result.params, num_levels=9)
        assert computed == data

    def test_validate_via_engine(self):
        engine = InverseEngine()
        data = [100 + i * 5 for i in range(9)]
        result = engine.fit(data, "floor_linear")
        val = engine.validate("floor_linear", result.params, data)
        assert val.is_exact

    def test_list_formula_types(self):
        engine = InverseEngine()
        types = engine.list_formula_types()
        ids = [t["id"] for t in types]
        assert "floor_linear" in ids


# =========================================================================
# 跨游戏验证
# =========================================================================


class TestCrossGameInverse:
    """验证通用反推引擎可服务于不同游戏的公式结构。"""

    def test_card_rpg_attack_formula(self):
        """卡牌RPG 攻击力公式：ATK = 角色基础 + 武器加成。"""
        atk_curve = [50 + i * 3 for i in range(30)]
        fitter = FloorFormulaFitter()
        result = fitter.fit(atk_curve)
        assert result.is_exact
        assert result.params["base"] == 50
        assert result.params["growth"] == 3

    def test_moba_armor_formula(self):
        """MOBA 护甲公式模拟：线性增长。"""
        armor_curve = [30 + i * 4 for i in range(18)]
        result = FloorFormulaFitter().fit(armor_curve)
        assert result.is_exact
        assert result.params["base"] == 30
        assert result.params["growth"] == 4

    def test_fps_damage_formula(self):
        """FPS 基础伤害公式。"""
        dmg_curve = [80 + i * 2 for i in range(10)]
        result = FloorFormulaFitter().fit(dmg_curve)
        assert result.is_exact
        assert result.params["base"] == 80


# =========================================================================
# 边界条件
# =========================================================================


class TestEdgeCases:
    """边界条件测试。"""

    def test_empty_data(self):
        result = FloorFormulaFitter().fit([])
        assert result.max_error == 0
        assert not result.is_exact

    def test_single_point(self):
        result = FloorFormulaFitter().fit([100])
        assert result.max_error == 0

    def test_two_points(self):
        data = [100, 105]
        result = FloorFormulaFitter().fit(data)
        assert result.is_exact

    def test_constant_data(self):
        """所有等级值相同。"""
        data = [100] * 10
        result = FloorFormulaFitter().fit(data)
        assert result.is_exact
        assert result.params["growth"] == 0 or result.params["divisor"] > 0

    def test_large_numbers(self):
        """大数值不溢出。"""
        data = [10000 + i * 500 for i in range(20)]
        result = FloorFormulaFitter().fit(data)
        assert result.is_exact
        assert result.params["base"] == 10000

    def test_negative_growth(self):
        """递减曲线。"""
        data = [100 - i * 3 for i in range(10)]
        result = FloorFormulaFitter().fit(data, growth_range=(-100, 0))
        assert result.is_exact or result.max_error < 0.1


# =========================================================================
# Registry
# =========================================================================


class TestRegistry:
    """公式类型注册表。"""

    def test_registry_has_floor_linear(self):
        assert registry.get("floor_linear") is not None

    def test_registry_list_ids(self):
        ids = registry.list_ids()
        assert "floor_linear" in ids

    def test_custom_registry(self):
        r = Registry()
        ft = FormulaType(id="test_custom", name="Test", fitter=FloorFormulaFitter())
        r.register(ft)
        assert r.get("test_custom") is not None
        assert "test_custom" in r.list_ids()
