# SPDX-License-Identifier: AGPL-3.0
"""
框架通用反推引擎 — 高级公式类型测试。

覆盖场景：
- ExponentialFormulaFitter：纯指数 / 含 offset / 不同底数
- PiecewiseFormulaFitter：两段线性 / 三段线性 / 自动断点检测
- ThresholdFormulaFitter：阈值后 flat / 阈值后换公式
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from calc_framework.inverse.engine import InverseEngine
from calc_framework.inverse.registry import registry

# =========================================================================
# ExponentialFormulaFitter
# =========================================================================


class TestExponentialFormulaFitter:

    def test_pure_exponential_integer(self):
        """纯指数增长（growth=1.05, base=100, offset=0）。"""
        base, growth, _offset = 100.0, 1.05, 0.0
        data = [round(base * (growth ** (lv - 1)), 1) for lv in range(1, 21)]
        result = registry.get("exponential").fitter.fit(data)
        assert result.max_error < 0.1, f"误差太大: {result.max_error}"
        assert abs(result.params["base"] - base) < 0.5
        assert abs(result.params["growth"] - growth) < 0.01

    def test_exponential_with_offset(self):
        """指数增长 + 偏移量。"""
        base, growth, offset = 50.0, 1.08, 30.0
        data = [round(base * (growth ** (lv - 1)) + offset, 1) for lv in range(1, 16)]
        result = registry.get("exponential").fitter.fit(data)
        assert result.max_error < 0.5, f"误差太大: {result.max_error}"
        assert abs(result.params["base"] - base) < 2.0
        assert abs(result.params["growth"] - growth) < 0.03
        assert abs(result.params.get("offset", 0) - offset) < 3.0

    def test_exponential_small_growth(self):
        """小底数指数增长（接近线性）。"""
        base, growth = 100.0, 1.02
        data = [round(base * (growth ** (lv - 1)), 1) for lv in range(1, 11)]
        result = registry.get("exponential").fitter.fit(data)
        assert result.max_error < 0.1, f"误差太大: {result.max_error}"
        assert abs(result.params["growth"] - growth) < 0.02

    def test_exponential_compute_consistency(self):
        """fit → compute 应该接近原始数据。"""
        fitter = registry.get("exponential").fitter
        base, growth = 200.0, 1.03
        data = [round(base * (growth ** (lv - 1)), 1) for lv in range(1, 21)]
        result = fitter.fit(data)
        computed = fitter.compute(result.params, num_levels=20)
        errors = [abs(computed[i] - data[i]) for i in range(20)]
        assert max(errors) < 0.5

    def test_exponential_validate(self):
        """验证功能。"""
        fitter = registry.get("exponential").fitter
        params = {"base": 100.0, "growth": 1.05, "offset": 0.0}
        data = [round(100.0 * (1.05 ** (lv - 1)), 1) for lv in range(1, 11)]
        validation = fitter.validate(params, data)
        assert validation.max_error < 0.1

    def test_exponential_flat_data(self):
        """平坦数据应能得到合理的指数拟合。"""
        data = [100.0] * 10
        result = registry.get("exponential").fitter.fit(data)
        assert abs(result.params["growth"] - 1.0) < 0.01

    def test_exponential_describe(self):
        """describe 返回正确的元数据。"""
        meta = registry.get("exponential").fitter.describe()
        assert "base" in meta["param_names"]
        assert "growth" in meta["param_names"]
        assert "指数" in meta["description"] or "exponential" in meta["description"].lower()


# =========================================================================
# PiecewiseFormulaFitter
# =========================================================================


class TestPiecewiseFormulaFitter:

    def test_two_segment_linear(self):
        """两段线性：段 1 成长慢，段 2 成长快。"""
        base, g1, g2 = 100, 3, 10
        breakpoint = 10
        data = []
        for lv in range(1, 21):
            if lv <= breakpoint:
                data.append(base + g1 * (lv - 1))
            else:
                data.append(base + g1 * (breakpoint - 1) + g2 * (lv - breakpoint))
        result = registry.get("piecewise").fitter.fit(data, num_levels=20)
        assert result.is_exact, f"应精确匹配，实际 max_error={result.max_error}"
        assert result.params.get("base", 0) == base
        assert 3 in (result.params.get("segment_1_growth", 0), result.params.get("growth_1", 0))

    def test_constant_then_linear(self):
        """段 1 持平，段 2 线性增长。"""
        data = [100] * 5 + [100 + 5 * i for i in range(1, 6)]
        result = registry.get("piecewise").fitter.fit(data, num_levels=10)
        assert result.is_exact or result.max_error < 0.5

    def test_piecewise_compute_consistency(self):
        """fit → compute 一致性。"""
        fitter = registry.get("piecewise").fitter
        base, g1, g2 = 50, 2, 8
        data = []
        for lv in range(1, 31):
            if lv <= 15:
                data.append(base + g1 * (lv - 1))
            else:
                data.append(base + g1 * 14 + g2 * (lv - 15))
        result = fitter.fit(data, num_levels=30)
        computed = fitter.compute(result.params, num_levels=30)
        errors = [abs(computed[i] - data[i]) for i in range(30)]
        assert max(errors) < 0.5, f"compute 误差太大: max={max(errors)} params={result.params}"

    def test_piecewise_validate(self):
        """验证功能。"""
        fitter = registry.get("piecewise").fitter
        base, g1, g2 = 100, 3, 10
        data = []
        for lv in range(1, 9):
            if lv <= 4:
                data.append(base + g1 * (lv - 1))
            else:
                data.append(base + g1 * 3 + g2 * (lv - 4))
        result = fitter.fit(data, num_levels=8)
        validation = fitter.validate(result.params, data)
        assert validation.is_exact, f"应精确匹配：params={result.params} computed={validation.computed}"

    def test_piecewise_describe(self):
        """describe 返回正确的元数据。"""
        meta = registry.get("piecewise").fitter.describe()
        assert "base" in meta["param_names"]
        assert "segment" in meta["description"].lower() or "分段" in meta["description"]


# =========================================================================
# ThresholdFormulaFitter
# =========================================================================


class TestThresholdFormulaFitter:

    def test_linear_then_flat(self):
        """线性增长到阈值后持平。"""
        base, growth = 100, 5
        threshold = 15
        data = []
        for lv in range(1, 31):
            if lv <= threshold:
                data.append(base + growth * (lv - 1))
            else:
                data.append(base + growth * (threshold - 1))
        result = registry.get("threshold").fitter.fit(data, num_levels=30)
        assert result.is_exact, f"应精确匹配，实际 max_error={result.max_error}"

    def test_linear_then_slower(self):
        """线性增长到阈值后换慢速公式。"""
        base, g1, g2 = 100, 10, 2
        threshold = 10
        data = []
        for lv in range(1, 26):
            if lv <= threshold:
                data.append(base + g1 * (lv - 1))
            else:
                data.append(base + g1 * (threshold - 1) + g2 * (lv - threshold))
        result = registry.get("threshold").fitter.fit(data, num_levels=25)
        assert result.is_exact, f"应精确匹配，实际 max_error={result.max_error}"

    def test_threshold_compute_consistency(self):
        """fit → compute 一致性。"""
        fitter = registry.get("threshold").fitter
        base, g1, g2 = 200, 8, 1
        threshold = 12
        data = []
        for lv in range(1, 25):
            if lv <= threshold:
                data.append(base + g1 * (lv - 1))
            else:
                data.append(base + g1 * (threshold - 1) + g2 * (lv - threshold))
        result = fitter.fit(data, num_levels=24)
        computed = fitter.compute(result.params, num_levels=24)
        errors = [abs(computed[i] - data[i]) for i in range(24)]
        assert max(errors) < 0.5

    def test_threshold_validate(self):
        """验证功能。"""
        fitter = registry.get("threshold").fitter
        data = [100, 105, 110, 115, 120, 120, 120, 120, 120, 120]
        result = fitter.fit(data, num_levels=10)
        validation = fitter.validate(result.params, data)
        assert validation.is_exact or validation.max_error < 0.5

    def test_threshold_describe(self):
        """describe 返回正确的元数据。"""
        meta = registry.get("threshold").fitter.describe()
        assert "threshold" in meta["description"].lower() or "阈值" in meta["description"]
        assert "threshold" in meta["param_names"]


# =========================================================================
# InverseEngine 集成
# =========================================================================


class TestEngineIntegration:

    def test_fit_auto_discovers_new_formulas(self):
        """fit_auto 应发现新注册的公式类型。"""
        engine = InverseEngine()
        ids = [t["id"] for t in engine.list_formula_types()]
        assert "exponential" in ids
        assert "piecewise" in ids
        assert "threshold" in ids

    def test_fit_exponential_via_engine(self):
        """通过 InverseEngine 调用指数公式。"""
        engine = InverseEngine()
        data = [round(100.0 * (1.05 ** (lv - 1)), 1) for lv in range(1, 11)]
        result = engine.fit(data, "exponential")
        assert result.max_error < 0.1, f"误差太大: {result.max_error}"

    def test_fit_piecewise_via_engine(self):
        """通过 InverseEngine 调用分段公式。"""
        engine = InverseEngine()
        data = [100 + i * 2 for i in range(10)] + [120 + i * 8 for i in range(10)]
        result = engine.fit(data, "piecewise", num_levels=20)
        assert result is not None

    def test_fit_threshold_via_engine(self):
        """通过 InverseEngine 调用阈值公式。"""
        engine = InverseEngine()
        data = [100 + i * 5 for i in range(10)] + [145] * 10
        result = engine.fit(data, "threshold", num_levels=20)
        assert result is not None
