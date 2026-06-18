# SPDX-License-Identifier: AGPL-3.0
from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2] / "src"

if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


from calc_framework.inverse.advanced import (  # noqa: E402
    ExponentialFormulaFitter,
    PiecewiseFormulaFitter,
    ThresholdFormulaFitter,
)
from calc_framework.inverse.base import FitResult  # noqa: E402
from calc_framework.inverse.registry import registry  # noqa: E402


class TestExponentialFormulaFitterExtra:
    def test_num_levels_less_than_2(self):
        fitter = ExponentialFormulaFitter()

        result = fitter.fit([100.0], num_levels=1)

        assert result.max_error == 0.0

    def test_estimate_offset_short_data(self):
        offset = ExponentialFormulaFitter._estimate_offset([100.0, 105.0])

        assert offset == 0.0

    def test_estimate_offset_non_increasing(self):
        offset = ExponentialFormulaFitter._estimate_offset([100.0, 95.0, 90.0])

        assert offset == 0.0

    def test_fit_with_invalid_data(self):
        fitter = ExponentialFormulaFitter()

        result = fitter.fit([100, "abc", 200])

        assert isinstance(result, FitResult)

    def test_compute_with_missing_params(self):
        fitter = ExponentialFormulaFitter()

        result = fitter.compute({"base": 100, "growth": 1.05}, num_levels=5)

        assert len(result) == 5

        assert result[0] == 100.0

    def test_validate_with_perfect_data(self):
        fitter = ExponentialFormulaFitter()

        params = {"base": 100.0, "growth": 1.05, "offset": 0.0}

        data = [round(100.0 * (1.05 ** (lv - 1)), 1) for lv in range(1, 11)]

        result = fitter.validate(params, data)

        assert result.is_exact is True


class TestPiecewiseFormulaFitterExtra:
    def test_num_levels_less_than_4(self):
        fitter = PiecewiseFormulaFitter()

        result = fitter.fit([100, 105, 110], num_levels=3)

        assert result.max_error == 0.0

    def test_num_segments_not_2(self):
        fitter = PiecewiseFormulaFitter()

        result = fitter.fit([100, 105, 110, 115, 120], num_levels=5, num_segments=3)

        assert result.max_error == 999999.0

    def test_fit_linear_segment_too_short(self):
        result = PiecewiseFormulaFitter._fit_linear_segment([100.0])

        assert result is None

    def test_compute_with_missing_params(self):
        fitter = PiecewiseFormulaFitter()

        result = fitter.compute({}, num_levels=5)

        assert len(result) == 5

    def test_describe_returns_expected_keys(self):
        meta = registry.get("piecewise").fitter.describe()

        assert "name" in meta

        assert "description" in meta

        assert "param_names" in meta


class TestThresholdFormulaFitterExtra:
    def test_num_levels_less_than_4(self):
        fitter = ThresholdFormulaFitter()

        result = fitter.fit([100, 105, 110], num_levels=3)

        assert result.max_error == 0.0

    def test_min_threshold_clamping(self):
        fitter = ThresholdFormulaFitter()

        data = [100, 105, 110, 115, 120, 120, 120, 120, 120, 120]

        result = fitter.fit(data, num_levels=10, min_threshold=1)

        assert result.max_error < 0.5

    def test_compute_with_missing_params(self):
        fitter = ThresholdFormulaFitter()

        result = fitter.compute({}, num_levels=5)

        assert len(result) == 5

    def test_validate_with_mismatched_data(self):
        fitter = ThresholdFormulaFitter()

        params = {"base": 100, "threshold": 10, "pre_growth": 5, "post_growth": 0, "post_is_flat": True}

        data = [999.0] * 10

        result = fitter.validate(params, data)

        assert result.is_exact is False

        assert result.max_error > 10.0

    def test_describe_returns_expected_keys(self):
        meta = registry.get("threshold").fitter.describe()

        assert "name" in meta

        assert "description" in meta

        assert "param_names" in meta


class TestFitResultExtra:
    def test_fit_result_dataclass(self):
        result = FitResult(
            params={"a": 1, "b": 2},
            computed=[1.0, 2.0, 3.0],
            max_error=0.5,
            is_exact=False,
        )

        assert result.params == {"a": 1, "b": 2}

        assert result.computed == [1.0, 2.0, 3.0]

        assert result.max_error == 0.5

        assert result.is_exact is False

    def test_fit_result_exact_true(self):
        result = FitResult(
            params={"x": 10},
            computed=[10.0, 20.0, 30.0],
            max_error=0.0,
            is_exact=True,
        )

        assert result.is_exact is True

        assert result.max_error == 0.0

    def test_fit_result_defaults(self):
        result = FitResult()

        assert result.params == {}

        assert result.computed == []

        assert result.max_error == 0.0

        assert result.is_exact is False
