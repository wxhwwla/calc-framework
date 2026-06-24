# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""明日方舟分段逆推适配器测试。"""

from __future__ import annotations

import pytest
from calc_framework.inverse.curve import GROWTH_PARAM_SEGMENTS_KEY

from games.arknights.calc.inverse.adapter import ArknightsInverseAdapter, blueprint_for_rarity
from games.arknights.calc.inverse.milestones import fit_operator_growth_params
from games.arknights.calc.inverse.segments import (
    elite_segment_key,
    expand_segment_linear,
    segment_length,
)


class TestSegments:
    def test_six_star_segment_lengths(self):
        assert segment_length(6, 0) == 50
        assert segment_length(6, 1) == 30
        assert segment_length(6, 2) == 10

    def test_two_star_only_e0(self):
        assert segment_length(2, 0) == 30
        assert segment_length(2, 1) == 0

    def test_elite_segment_key(self):
        assert elite_segment_key(1) == "e1"

    def test_blueprint_for_rarity(self):
        bp = blueprint_for_rarity(6)
        assert bp.keys() == ["e0", "e1", "e2"]
        assert bp.get("e1").length == 30


class TestArknightsInverseAdapter:
    @pytest.fixture
    def adapter(self) -> ArknightsInverseAdapter:
        return ArknightsInverseAdapter()

    def test_fit_exusiai_e0_hp_segment(self, adapter: ArknightsInverseAdapter):
        data = expand_segment_linear(711, 1016, 50)
        result = adapter.fit_elite_segment(data, elite=0, rarity=6)
        assert result.params
        assert result.max_error < 0.01
        curve = adapter.compute_segment(result.params, elite=0, rarity=6)
        assert len(curve) == 50
        assert int(curve[0]) == 711
        assert int(curve[-1]) == 1016

    def test_fit_skill_sp_with_mastery_specials(self, adapter: ArknightsInverseAdapter):
        sp = [50, 48, 46, 44, 42, 40, 38, 36, 34, 30]
        result = adapter.fit_skill_sp(sp)
        assert result.params
        assert "special_values" in result.params
        assert result.params["special_values"] == [36.0, 34.0, 30.0]
        rebuilt = adapter.compute_skill_sp(result.params)
        assert [int(x) for x in rebuilt] == sp

    def test_unsupported_length_raises(self, adapter: ArknightsInverseAdapter):
        with pytest.raises(ValueError, match="不支持的数据长度"):
            adapter.fit([100.0] * 99)


class TestFitOperatorMilestones:
    def test_exusiai_milestones_dry_run(self):
        operator = {
            "名称": "能天使",
            "星级": 6,
            "属性里程碑": {
                "hp": {"e0_lv1": 711, "e0_max": 1016, "e1_max": 1338, "e2_max": 1673},
                "atk": {"e0_lv1": 217, "e0_max": 305, "e1_max": 437, "e2_max": 540},
            },
            "技能": [
                {
                    "名称": "过载模式",
                    "SP消耗": [50, 48, 46, 44, 42, 40, 38, 36, 34, 30],
                }
            ],
        }
        growth = fit_operator_growth_params(operator, max_error=0.05)
        segments = growth.get(GROWTH_PARAM_SEGMENTS_KEY, [])
        assert any(s["key"] == "e0.hp" for s in segments)
        assert "过载模式" in growth.get("技能SP", {})
