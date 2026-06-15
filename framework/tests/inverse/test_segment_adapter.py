# SPDX-License-Identifier: AGPL-3.0
"""SegmentCurveAdapter 与物化 helpers 测试。"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from calc_framework.inverse.curve import CurveBlueprint, SegmentSpec, single_segment_blueprint
from calc_framework.inverse.materialize import (
    blueprint_from_stored,
    has_segment_storage,
    materialize_entity_from_stored_segments,
)
from calc_framework.inverse.segment_adapter import SegmentCurveAdapter


class _MiniAdapter(SegmentCurveAdapter):
    def iter_blueprints(self):
        yield single_segment_blueprint(5, key="main")
        yield CurveBlueprint(segments=[SegmentSpec(key="bonus", length=5, search_options={"growth_range": (1, 51)})])

    def default_formula(self):
        return "floor_linear"


class TestSegmentCurveAdapter:
    def test_schemas_aggregate_unique_keys(self):
        adapter = _MiniAdapter()
        keys = [s.key for s in adapter.schemas if s.key]
        assert keys == ["main", "bonus"]

    def test_fit_segment_by_key(self):
        adapter = _MiniAdapter()
        data = [10.0, 12.0, 14.0, 16.0, 18.0]
        result = adapter.fit_segment_by_key(data, "main")
        assert result.params
        curve = adapter.compute_segment_by_key(result.params, "main")
        assert [int(x) for x in curve] == [10, 12, 14, 16, 18]

    def test_materialize_stored_merges_blueprints(self):
        adapter = _MiniAdapter()
        stored = {
            "segments": [
                {"key": "main", "length": 5, "base": 10, "growth": 2, "divisor": 1, "offset": 0},
            ]
        }
        out = adapter.materialize_stored(stored)
        assert "main" in out
        assert len(out["main"]) == 5


class TestMaterializeHelpers:
    def test_has_segment_storage(self):
        assert has_segment_storage({"segments": [{"key": "a", "length": 3}]})
        assert not has_segment_storage({"力量": {"base": 1}})

    def test_blueprint_from_stored(self):
        stored = {
            "segments": [
                {"key": "力量", "length": 90, "base": 100, "growth": 5, "divisor": 1, "offset": 0},
            ]
        }
        bp = blueprint_from_stored(stored)
        assert bp.get("力量").length == 90

    def test_materialize_entity_segments_to_fields(self):
        entity = {
            "名称": "测试",
            "成长参数": {
                "segments": [
                    {"key": "力量", "length": 5, "base": 10, "growth": 2, "divisor": 1, "offset": 0},
                ]
            },
        }
        out = materialize_entity_from_stored_segments(entity)
        assert "力量" in out
        assert len(out["力量"]) == 5
