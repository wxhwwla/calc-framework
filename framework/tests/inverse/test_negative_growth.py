# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""FloorFormulaFitter 递减曲线（负 growth）测试。"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from calc_framework.inverse.engine import InverseEngine


class TestNegativeGrowthFit:
    """递减数据应自动启用含负数的 growth 搜索。"""

    def test_decreasing_sp_segment_fits_without_explicit_range(self):
        engine = InverseEngine()
        sp7 = [50, 48, 46, 44, 42, 40, 38]
        result = engine.fit(sp7, formula_id="floor_linear")
        assert result.params, f"拟合失败 max_error={result.max_error}"
        assert result.max_error < 0.001
        assert int(result.params["growth"]) < 0

    def test_increasing_still_positive_growth(self):
        engine = InverseEngine()
        data = [100 + i * 5 for i in range(20)]
        result = engine.fit(data, formula_id="floor_linear")
        assert result.is_exact
        assert int(result.params["growth"]) > 0

    def test_explicit_negative_range(self):
        engine = InverseEngine()
        sp = [45, 44, 43, 42, 41, 40, 39]
        result = engine.fit(
            sp,
            formula_id="floor_linear",
            growth_range=(-200, 201),
            divisor_range=(1, 21),
        )
        assert result.max_error < 0.001
