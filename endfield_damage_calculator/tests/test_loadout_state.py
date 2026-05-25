#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LoadoutState 接缝测试。"""

import unittest

from calculation.loadout_slot_search import FixedLoadoutSelection
from gui_design.loadout_state import LoadoutState, normalize_weapon_specials_tuple, read_loadout_from_panels
from tests.gui_fixtures import MockSelectionPanel


class TestLoadoutState(unittest.TestCase):
    def _char(self) -> dict:
        return {
            "名称": "测试干员",
            "武器": "单手剑",
            "战技倍率": [[200] * 3],
            "连携技倍率": [[100] * 3],
            "终结技倍率": [[50] * 3],
            "基础攻击力": [100] * 3,
        }

    def _weapon(self) -> dict:
        return {
            "名称": "测试武器",
            "类型": "单手剑",
            "星级": 5,
            "基础攻击力": [100] * 3,
        }

    def test_read_returns_none_without_character(self) -> None:
        weapon_panel = MockSelectionPanel(self._weapon())
        char_panel = MockSelectionPanel(self._char())
        char_panel.get_selected_data = lambda: None  # type: ignore[method-assign]
        state = read_loadout_from_panels(
            char_panel,
            weapon_panel,
            calculation_mode="zone_snapshot",
            weapon_scope_label="当前武器",
            equipment_scope_label="全部装备",
            fixed_loadout=FixedLoadoutSelection(),
            use_manual_multi_skill_counts=False,
            manual_counts={"战技": 1, "连携技": 0, "终结技": 0},
            enemy_defense=100.0,
        )
        self.assertIsNone(state)

    def test_to_search_job_inputs_carries_enemy_defense(self) -> None:
        state = read_loadout_from_panels(
            MockSelectionPanel(self._char(), skills=(1, 1, 0)),
            MockSelectionPanel(self._weapon()),
            calculation_mode="single_hit",
            weapon_scope_label="当前武器",
            equipment_scope_label="全部装备",
            fixed_loadout=FixedLoadoutSelection(),
            use_manual_multi_skill_counts=True,
            manual_counts={"战技": 2, "连携技": 1, "终结技": 0},
            enemy_defense=420.0,
        )
        assert state is not None
        catalog = {
            "chest": [{"名称": "甲", "效果": [], "三件套效果": []}],
            "gloves": [{"名称": "手", "效果": [], "三件套效果": []}],
            "accessories": [{"名称": "件", "效果": [], "三件套效果": []}],
        }
        inputs = state.to_search_job_inputs(
            all_weapons=[self._weapon()],
            equipment_catalog=catalog,
        )
        self.assertEqual(inputs.enemy_defense, 420.0)
        self.assertTrue(inputs.use_manual_multi_skill_counts)

    def test_to_loadout_preset_roundtrip_names(self) -> None:
        fixed = FixedLoadoutSelection()
        state = LoadoutState(
            char_data=self._char(),
            weapon_data=self._weapon(),
            char_level=10,
            weapon_level=20,
            trust_level=1,
            skill_levels=(3, 2, 0),
            skill_name="战技",
            skill_type="战技",
            skill_multiplier=2.0,
            calculation_mode="zone_snapshot",
            weapon_scope_label="当前武器",
            equipment_scope_label="全部装备",
            fixed_loadout=fixed,
            fixed_equipment_names={
                "chest": None,
                "gloves": None,
                "accessory_a": None,
                "accessory_b": None,
            },
            use_manual_multi_skill_counts=False,
            manual_counts={"战技": 1, "连携技": 0, "终结技": 0},
            enemy_defense=100.0,
            weapon_specials=("敏捷+", 9, "", 0, "", 0, "主能力+", 8, "", 0),
        )
        preset = state.to_loadout_preset()
        self.assertEqual(preset.char_name, "测试干员")
        self.assertEqual(preset.char_level, 10)
        self.assertEqual(preset.weapon_normal_levels, [9])
        self.assertEqual(preset.weapon_special_states, [{"level": 8, "stack": 1}])

    def test_normalize_weapon_specials_migrates_legacy_ws_level(self) -> None:
        migrated = normalize_weapon_specials_tuple(
            ("", 1, "", 1, "", 0, "攻击力+", 0, "", 3)
        )
        self.assertEqual(migrated[7:12], (1, 0, "", 3, 1))

    def test_weapon_skill_selection_uses_new_schema_shape(self) -> None:
        state = LoadoutState(
            char_data=self._char(),
            weapon_data=self._weapon(),
            char_level=10,
            weapon_level=20,
            trust_level=1,
            skill_levels=(3, 2, 0),
            skill_name="战技",
            skill_type="战技",
            skill_multiplier=2.0,
            calculation_mode="zone_snapshot",
            weapon_scope_label="当前武器",
            equipment_scope_label="全部装备",
            fixed_loadout=FixedLoadoutSelection(),
            fixed_equipment_names={
                "chest": None,
                "gloves": None,
                "accessory_a": None,
                "accessory_b": None,
            },
            use_manual_multi_skill_counts=False,
            manual_counts={"战技": 1, "连携技": 0, "终结技": 0},
            enemy_defense=100.0,
            weapon_specials=("敏捷+", 9, "攻击力+", 8, "", 0, "施放战技后，攻击力+", 7, 2, "", 1, 0),
        )
        selection = state.weapon_skill_selection()
        self.assertEqual(selection["weapon_normal_levels"], [9, 8])
        self.assertEqual(
            selection["weapon_special_states"],
            [{"level": 7, "stack": 2}],
        )


if __name__ == "__main__":
    unittest.main()
