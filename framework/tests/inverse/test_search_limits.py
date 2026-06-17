# SPDX-License-Identifier: AGPL-3.0
"""FloorFormulaFitter._search 超时与早停选项测试。"""

from __future__ import annotations

import pytest

from calc_framework.inverse.base import FloorFormulaFitter


def _linear_data(levels: int = 20) -> list[int]:
    return [100 + i * 10 for i in range(levels)]


class TestSearchLimits:
    """search_timeout_seconds / early_stop_max_error / max_search_iterations。"""

    def test_max_search_iterations_stops_before_full_scan(self) -> None:
        data = [100 + i * 3 for i in range(90)]
        full = FloorFormulaFitter().fit(data, growth_range=(1, 200), divisor_range=(1, 50))
        limited = FloorFormulaFitter().fit(
            data,
            growth_range=(1, 200),
            divisor_range=(1, 50),
            max_search_iterations=5,
        )
        assert full.is_exact
        assert limited.max_error == pytest.approx(999999.0)

    def test_early_stop_max_error_accepts_good_enough_fit(self) -> None:
        data = _linear_data()
        result = FloorFormulaFitter().fit(
            data,
            growth_range=(1, 50),
            divisor_range=(1, 5),
            early_stop_max_error=0.05,
        )
        assert result.max_error <= 0.05 or result.is_exact

    def test_search_timeout_logs_and_stops(self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
        data = _linear_data()
        ticks = iter([0.0, 0.0, 0.0005, 5.0])

        monkeypatch.setattr("calc_framework.inverse.base.time.monotonic", lambda: next(ticks, 5.0))

        FloorFormulaFitter().fit(
            data,
            growth_range=(1, 500),
            divisor_range=(1, 100),
            search_timeout_seconds=0.001,
        )
        assert any("timeout" in record.message for record in caplog.records)

    def test_describe_includes_search_limit_options(self) -> None:
        optional = FloorFormulaFitter().describe()["optional_options"]
        assert "search_timeout_seconds" in optional
        assert "early_stop_max_error" in optional
        assert "max_search_iterations" in optional
