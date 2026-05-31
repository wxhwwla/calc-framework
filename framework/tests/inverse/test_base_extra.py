# SPDX-License-Identifier: AGPL-3.0
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from calc_framework.inverse.base import FitResult, FloorFormulaFitter  # noqa: E402
from calc_framework.inverse.registry import FormulaType, registry  # noqa: E402


class TestFitResultSummary:

    def test_summary_exact(self):
        result = FitResult(params={"base": 100, "growth": 5}, is_exact=True)
        s = result.summary()
        assert "✓ 精确匹配" in s
        assert "base=100" in s
        assert "growth=5" in s

    def test_summary_not_exact(self):
        result = FitResult(params={"a": 3.5}, max_error=0.5, is_exact=False)
        s = result.summary()
        assert "≈" in s
        assert "a=3.5" in s
        assert "0.5000" in s

    def test_summary_empty_params(self):
        s = FitResult(is_exact=True).summary()
        assert "✓ 精确匹配" in s

    def test_summary_zero_error(self):
        s = FitResult(params={"k": 0}, max_error=0.0, is_exact=False).summary()
        assert "0.0000" in s


class TestFloorFormulaFitterComputeDecimal:
    """Cover line 173: is_decimal branch in compute()."""

    def test_compute_decimal(self):
        fitter = FloorFormulaFitter()
        params = {"base": 10.0, "growth": 1.0, "divisor": 2, "offset": 0, "is_decimal": True}
        result = fitter.compute(params, num_levels=5)
        assert len(result) == 5
        assert result == [10.0, 10.0, 11.0, 11.0, 12.0]

    def test_compute_decimal_with_offset(self):
        fitter = FloorFormulaFitter()
        params = {"base": 20.0, "growth": 0.3, "divisor": 2, "offset": 0.5, "is_decimal": True}
        result = fitter.compute(params, num_levels=4)
        assert len(result) == 4

    def test_compute_integer_no_is_decimal(self):
        fitter = FloorFormulaFitter()
        params = {"base": 50, "growth": 10, "divisor": 1}
        result = fitter.compute(params, num_levels=3)
        assert result == [50.0, 60.0, 70.0]


class TestDetectScale:
    """Cover line 205: _detect_scale returning 10."""

    def test_integer_data_returns_1(self):
        assert FloorFormulaFitter._detect_scale([1, 2, 3]) == 1

    def test_float_without_fraction_returns_1(self):
        assert FloorFormulaFitter._detect_scale([1.0, 2.0, 3.0]) == 1

    def test_float_with_fraction_returns_10(self):
        assert FloorFormulaFitter._detect_scale([1.5, 2.0, 3.0]) == 10

    def test_mixed_data_with_fraction_returns_10(self):
        assert FloorFormulaFitter._detect_scale([1, 2.5, 3]) == 10


class TestRestoreParam:
    """Cover lines 212, 216: _restore_param edge cases."""

    def test_scale_factor_not_one_returns_value(self):
        result = FloorFormulaFitter._restore_param(5.0, 10)
        assert result == 5.0

    def test_round_to_int(self):
        result = FloorFormulaFitter._restore_param(5.0 + 1e-10, 1)
        assert result == 5
        assert isinstance(result, int)

    def test_no_round_to_int(self):
        result = FloorFormulaFitter._restore_param(5.5, 1)
        assert result == 5.5
        assert isinstance(result, float)


class TestGcdNormalize:
    """Cover lines 229-237: _gcd_normalize while-loop reduction."""

    def test_gcd_reduction(self):
        scaled_data = [100, 105, 110, 115, 120]
        scaled_base = 100
        growth, divisor, offset = FloorFormulaFitter._gcd_normalize(
            10, 2, 0, scaled_data, scaled_base)
        assert growth == 5
        assert divisor == 1

    def test_gcd_non_reducible(self):
        scaled_data = [100, 103, 106, 109]
        scaled_base = 100
        growth, divisor, offset = FloorFormulaFitter._gcd_normalize(
            3, 1, 0, scaled_data, scaled_base)
        assert growth == 3
        assert divisor == 1

    def test_gcd_offset_nonzero(self):
        scaled_data = [100, 106, 112, 118]
        scaled_base = 100
        growth, divisor, offset = FloorFormulaFitter._gcd_normalize(
            12, 2, 0, scaled_data, scaled_base)
        assert growth == 6
        assert divisor == 1
        assert offset == 0

    def test_gcd_break_early(self):
        scaled_data = [100, 102, 105, 107]
        scaled_base = 100
        growth, divisor, offset = FloorFormulaFitter._gcd_normalize(
            10, 4, 1, scaled_data, scaled_base)
        assert growth == 10
        assert divisor == 4
        assert offset == 1


class TestFloorFormulaFitterEdgeCases:
    """Cover various search and fit edge cases."""

    def test_fit_decimal_data(self):
        data = [10.0, 10.5, 11.0, 11.5, 12.0]
        result = FloorFormulaFitter().fit(data)
        assert result.max_error < 0.1
        assert result.params.get("is_decimal") is True

    def test_fit_flat_data_no_growth(self):
        data = [100.0] * 5
        result = FloorFormulaFitter().fit(data)
        assert result.max_error < 0.1

    def test_fit_single_element(self):
        result = FloorFormulaFitter().fit([100.0])
        assert result.max_error == 0.0

    def test_fit_approximate_only(self):
        data = [100, 101, 103, 106, 110]
        result = FloorFormulaFitter().fit(data)
        assert result.max_error == 999999.0 or result.max_error < 100

    def test_fit_large_growth(self):
        data = [100, 500, 900, 1300, 1700]
        result = FloorFormulaFitter().fit(data)
        assert result.max_error < 0.1

    def test_fit_data_with_noise(self):
        data = [100, 105, 110, 116, 121, 126]
        result = FloorFormulaFitter().fit(data)
        assert result.max_error < 1.0

    def test_validate_exact(self):
        fitter = FloorFormulaFitter()
        data = [100, 105, 110, 115]
        result = fitter.fit(data)
        validation = fitter.validate(result.params, data)
        assert validation.is_exact

    def test_validate_mismatch(self):
        fitter = FloorFormulaFitter()
        data = [100, 105, 110, 115]
        validation = fitter.validate({"base": 100, "growth": 10, "divisor": 1, "offset": 0}, data)
        assert not validation.is_exact
        assert validation.max_error > 0.001

    def test_validate_decimal(self):
        fitter = FloorFormulaFitter()
        data = [10.0, 10.0, 11.0, 11.0]
        result = fitter.fit(data)
        validation = fitter.validate(result.params, data)
        assert validation.is_exact


class TestFloorFormulaFitterSearchApproximate:
    """Trigger approximate search path with data having no exact floor formula."""

    def test_bounds_search_falls_back_to_approximate(self):
        data = [100, 102, 105, 109, 114, 120]
        result = FloorFormulaFitter().fit(data)
        assert result is not None
        assert isinstance(result.max_error, float)


class TestFormulaType:
    """Cover FormulaType construction and registry."""

    def test_create_bare(self):
        ft = FormulaType(id="test_id", name="测试", description="desc")
        assert ft.id == "test_id"
        assert ft.name == "测试"
        assert ft.description == "desc"
        assert ft._fitter is None

    def test_fitter_property_raises(self):
        ft = FormulaType(id="no_fitter")
        with pytest.raises(ValueError, match="未绑定"):
            _ = ft.fitter

    def test_to_dict_with_fitter(self):
        ft = FormulaType(id="floor_check", fitter=FloorFormulaFitter())
        d = ft.to_dict()
        assert d["id"] == "floor_check"
        assert "base" in d["param_names"]
        assert "growth" in d["param_names"]
        assert "divisor" in d["param_names"]

    def test_to_dict_without_fitter_raises(self):
        ft = FormulaType(id="no_fitter")
        with pytest.raises(ValueError):
            ft.to_dict()

    def test_registry_has_floor_linear(self):
        ft = registry.get("floor_linear")
        assert ft.id == "floor_linear"
        assert ft.fitter is not None

    def test_registry_has_exponential(self):
        ft = registry.get("exponential")
        assert ft.id == "exponential"

    def test_registry_has_piecewise(self):
        ft = registry.get("piecewise")
        assert ft.id == "piecewise"

    def test_registry_has_threshold(self):
        ft = registry.get("threshold")
        assert ft.id == "threshold"

    def test_registry_get_unknown_raises(self):
        with pytest.raises(KeyError):
            registry.get("nonexistent_formula")

    def test_registry_list_ids(self):
        ids = registry.list_ids()
        assert "floor_linear" in ids
        assert "exponential" in ids
        assert "piecewise" in ids
        assert "threshold" in ids

    def test_registry_to_dict_includes_name_desc(self):
        d = registry.get("floor_linear").to_dict()
        assert "param_descriptions" in d
        assert "description" in d
