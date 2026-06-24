# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""静默吞异常修复 — fit_auto / run_parallel 日志测试。"""

from __future__ import annotations

import logging
from typing import Any

import pytest

from calc_framework.inverse.base import FitResult, FormulaFitter
from calc_framework.inverse.engine import InverseEngine
from calc_framework.inverse.registry import FormulaType
from calc_framework.search import run_parallel


class _BrokenFitter(FormulaFitter):
    """始终失败的拟合器，用于测试日志。"""

    def describe(self) -> dict[str, Any]:
        return {"description": "broken", "param_names": []}

    def fit(
        self,
        data: Any,
        *,
        num_levels: int | None = None,
        **options: Any,
    ) -> FitResult:
        raise RuntimeError("拟合失败")

    def compute(
        self,
        params: dict[str, Any],
        num_levels: int,
        *,
        level_overrides: dict[int, float] | None = None,
    ) -> list[float]:
        return []

    def validate(self, params: dict[str, Any], data: Any) -> FitResult:
        raise RuntimeError("validate 未实现")


class TestFitAutoExceptionLogging:
    def test_logs_debug_when_fitter_fails(self, caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch) -> None:
        caplog.set_level(logging.DEBUG, logger="calc_framework")

        broken = FormulaType(id="broken_test", name="broken", fitter=_BrokenFitter())
        good = FormulaType(
            id="floor_linear",
            name="floor",
            fitter=__import__("calc_framework.inverse.base", fromlist=["FloorFormulaFitter"]).FloorFormulaFitter(),
        )

        monkeypatch.setattr(
            "calc_framework.inverse.engine.registry.list_types",
            lambda: [broken, good],
        )

        engine = InverseEngine()
        result = engine.fit_auto([100 + i * 5 for i in range(9)])

        assert result is not None
        assert any("broken_test" in m for m in caplog.messages)

    def test_logs_warning_when_all_fitters_fail(self, caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch) -> None:
        caplog.set_level(logging.WARNING, logger="calc_framework")

        broken = FormulaType(id="broken_only", name="broken", fitter=_BrokenFitter())
        monkeypatch.setattr(
            "calc_framework.inverse.engine.registry.list_types",
            lambda: [broken],
        )

        engine = InverseEngine()
        assert engine.fit_auto([1, 2, 3]) is None
        assert any("全部" in m and "拟合失败" in m for m in caplog.messages)


class TestRunParallelExceptionLogging:
    def test_logs_warning_when_evaluator_raises(self, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level(logging.WARNING, logger="calc_framework")

        def broken(x: int) -> int:
            if x == 2:
                raise ValueError("boom")
            return x

        results = run_parallel(range(4), broken, max_workers=1)
        assert 2 not in results
        assert any("run_parallel" in m or "评估失败" in m for m in caplog.messages)
