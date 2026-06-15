# SPDX-License-Identifier: AGPL-3.0
"""CurveBlueprint / SegmentCurveEngine 测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from calc_framework.inverse.curve import (
    CurveBlueprint,
    SegmentCurveEngine,
    SegmentSpec,
    expand_segment_linear,
    single_segment_blueprint,
)


class TestSegmentSpec:
    def test_to_schema_key(self):
        spec = SegmentSpec(key="e0", length=50)
        schema = spec.to_schema()
        assert schema.key == "e0"
        assert schema.length == 50


class TestSingleSegmentBlueprint:
    def test_endfield_degenerate(self):
        bp = single_segment_blueprint(90, search_options={"growth_range": (1, 301)})
        assert len(bp.segments) == 1
        assert bp.get("main").length == 90


class TestSegmentCurveEngine:
    @pytest.fixture
    def engine(self) -> SegmentCurveEngine:
        return SegmentCurveEngine()

    def test_fit_and_compute_with_special(self, engine: SegmentCurveEngine):
        bp = CurveBlueprint(
            segments=[
                SegmentSpec(
                    key="skill_sp",
                    length=10,
                    special_indices=[7, 8, 9],
                    search_options={"growth_range": (-500, 501), "divisor_range": (1, 101)},
                )
            ]
        )
        sp = [50, 48, 46, 44, 42, 40, 38, 36, 34, 30]
        result = engine.fit_by_key(sp, bp, "skill_sp")
        assert result.params
        rebuilt = engine.compute_by_key(result.params, bp, "skill_sp")
        assert [int(x) for x in rebuilt] == sp

    def test_materialize_stored_segments(self, engine: SegmentCurveEngine):
        bp = single_segment_blueprint(5)
        data = [10, 12, 14, 16, 18]
        fit = engine.fit_segment([float(x) for x in data], bp.segments[0])
        stored = {"segments": [{"key": "main", "length": 5, **fit.params}]}
        out = engine.materialize(bp, stored)
        assert [int(x) for x in out["main"]] == data

    def test_expand_segment_linear(self):
        assert expand_segment_linear(711, 1016, 50)[0] == 711
        assert expand_segment_linear(711, 1016, 50)[-1] == 1016

    def test_fit_blueprint_endpoints(self, engine: SegmentCurveEngine):
        bp = single_segment_blueprint(50, search_options={"growth_range": (1, 501), "divisor_range": (1, 201)})
        entries, errors = engine.fit_blueprint_endpoints(bp, {"main": (711, 1016)})
        assert not errors
        assert entries[0]["key"] == "main"
        assert entries[0]["base"] == 711
