# SPDX-License-Identifier: AGPL-3.0
from __future__ import annotations

from games.endfield.gui_design.shared.calc_mode_labels import (
    CALC_MODE_LABELS,
    CALC_MODE_OPTIONS,
    DEFAULT_CALC_MODE_LABEL,
    calculation_mode_from_label,
)


class TestCalculationModeFromLabel:
    def test_empty_string(self) -> None:
        assert calculation_mode_from_label("") == "single_hit"

    def test_whitespace_string(self) -> None:
        assert calculation_mode_from_label("  ") == "single_hit"

    def test_direct_mode_id(self) -> None:
        assert calculation_mode_from_label("single_hit") == "single_hit"
        assert calculation_mode_from_label("zone_snapshot") == "zone_snapshot"

    def test_exact_label(self) -> None:
        assert calculation_mode_from_label("乘区快照") == "zone_snapshot"
        assert calculation_mode_from_label("单段伤害计算") == "single_hit"

    def test_prefix_single(self) -> None:
        assert calculation_mode_from_label("单技能遍历全量搜索") == "single_skill_search"

    def test_prefix_multi(self) -> None:
        assert calculation_mode_from_label("多技能遍历加权总伤") == "multi_skill_search"

    def test_unknown_fallback(self) -> None:
        assert calculation_mode_from_label("未知模式") == "single_hit"

    def test_all_options_have_valid_mapping(self) -> None:
        for label, mode_id in CALC_MODE_OPTIONS:
            assert calculation_mode_from_label(label) == mode_id


class TestCalcModeConstants:
    def test_default_label_in_options(self) -> None:
        assert DEFAULT_CALC_MODE_LABEL in CALC_MODE_LABELS

    def test_calc_mode_labels_match_options(self) -> None:
        assert len(CALC_MODE_LABELS) == len(CALC_MODE_OPTIONS)
        for label, _ in CALC_MODE_OPTIONS:
            assert label in CALC_MODE_LABELS
