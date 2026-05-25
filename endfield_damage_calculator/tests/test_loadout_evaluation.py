#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LoadoutEvaluation 快照测试。"""

import unittest
from unittest.mock import patch

from gui_design.loadout_evaluation import (
    build_search_preview_lines,
    build_snapshot_from_loadout,
)
from calculation.loadout_slot_search import FixedLoadoutSelection
from gui_design.loadout_state import LoadoutState


class TestLoadoutEvaluation(unittest.TestCase):
    def test_effective_skill_counts_default_manual_off(self) -> None:
        state = LoadoutState(
            char_data={"名称": "A", "战技倍率": [[100]], "连携技倍率": [], "终结技倍率": []},
            weapon_data={"名称": "W", "基础攻击力": [100]},
            char_level=1,
            weapon_level=1,
            trust_level=0,
            skill_levels=(1, 0, 0),
            skill_name="战技",
            skill_type="战技",
            skill_multiplier=1.0,
            calculation_mode="zone_snapshot",
            weapon_scope_label="当前武器",
            equipment_scope_label="全部装备",
            fixed_loadout=FixedLoadoutSelection(),
            fixed_equipment_names={},
            use_manual_multi_skill_counts=False,
            manual_counts={"战技": 9, "连携技": 9, "终结技": 9},
            enemy_defense=100.0,
            weapon_specials=("", 0) * 5,
        )
        self.assertEqual(state.effective_skill_counts()["战技"], 1)
        self.assertEqual(state.effective_skill_counts()["连携技"], 0)

    @patch("gui_design.loadout_evaluation.build_damage_snapshot")
    @patch("gui_design.loadout_evaluation.sync_evaluation_cache")
    def test_build_snapshot_from_loadout(self, mock_sync, mock_build) -> None:
        state = LoadoutState(
            char_data={"名称": "A"},
            weapon_data={"名称": "W"},
            char_level=1,
            weapon_level=1,
            trust_level=0,
            skill_levels=(1, 0, 0),
            skill_name="战技",
            skill_type="战技",
            skill_multiplier=1.0,
            calculation_mode="zone_snapshot",
            weapon_scope_label="当前武器",
            equipment_scope_label="全部装备",
            fixed_loadout=FixedLoadoutSelection(),
            fixed_equipment_names={},
            use_manual_multi_skill_counts=False,
            manual_counts={"战技": 1, "连携技": 0, "终结技": 0},
            enemy_defense=50.0,
            weapon_specials=("", 0) * 5,
        )
        mock_build.return_value = object()
        build_snapshot_from_loadout(state)
        mock_sync.assert_called_once_with(state)
        mock_build.assert_called_once()
        self.assertEqual(mock_build.call_args.kwargs["enemy_defense"], 50.0)

    @patch("gui_design.loadout_evaluation.build_single_skill_search_preview_lines")
    @patch("gui_design.loadout_evaluation.sync_evaluation_cache")
    def test_build_search_preview_lines_single_skill(
        self, mock_sync, mock_preview
    ) -> None:
        state = LoadoutState(
            char_data={"名称": "A"},
            weapon_data={"名称": "W"},
            char_level=1,
            weapon_level=1,
            trust_level=0,
            skill_levels=(1, 0, 0),
            skill_name="战技",
            skill_type="战技",
            skill_multiplier=1.0,
            calculation_mode="single_skill_search",
            weapon_scope_label="当前武器",
            equipment_scope_label="全部装备",
            fixed_loadout=FixedLoadoutSelection(),
            fixed_equipment_names={},
            use_manual_multi_skill_counts=False,
            manual_counts={"战技": 1, "连携技": 0, "终结技": 0},
            enemy_defense=80.0,
            weapon_specials=(
                "攻击力+",
                1,
                "",
                1,
                "",
                0,
                "施放战技后，法术伤害+",
                1,
                1,
                "",
                1,
                0,
            ),
        )
        catalog = {"chest": [], "gloves": [], "accessories": [{"名称": "x"}]}
        mock_preview.return_value = ["line"]
        lines = build_search_preview_lines(state, equipment_catalog=catalog)
        mock_sync.assert_called_once_with(state)
        mock_preview.assert_called_once()
        self.assertEqual(lines, ["line"])
        self.assertEqual(
            mock_preview.call_args.kwargs["preview_equipment_catalog"], catalog
        )
        self.assertEqual(mock_preview.call_args.kwargs["enemy_defense"], 80.0)
        self.assertEqual(mock_preview.call_args.kwargs["normal_skill_1_name"], "攻击力+")
        self.assertEqual(
            mock_preview.call_args.kwargs["special_skill_1_name"],
            "施放战技后，法术伤害+",
        )


if __name__ == "__main__":
    unittest.main()
