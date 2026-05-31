#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""确认选择时角色属性列应传入技能等级（无 CTk）。"""

import json
import unittest
from unittest.mock import MagicMock

from calc_engine.endfield.calc.loadout.slot_search import FixedLoadoutSelection
from games.endfield.gui_design.app.loadout_state import read_loadout_from_panels
from games.endfield.gui_design.presentation.display_lines import build_character_attribute_lines
from calc_engine.endfield.tests.conftest import PKG_ROOT, GAMES_END, DATA_DIR

_CHARACTERS_JSON = DATA_DIR / "characters.json"


def _load_by_name(name: str) -> dict:
    with _CHARACTERS_JSON.open(encoding="utf-8") as f:
        data = json.load(f)
    for item in data:
        if item.get("名称") == name:
            return item
    raise KeyError(name)


class TestConfirmSelectionSkillLevels(unittest.TestCase):
    def test_loadout_and_char_lines_use_panel_skill_levels(self) -> None:
        char = _load_by_name("秋栗")
        char_panel = MagicMock()
        char_panel.get_selected_data.return_value = char
        char_panel.get_level.return_value = 1
        char_panel.get_trust_level.return_value = 0
        char_panel.get_skill_1_level.return_value = 5
        char_panel.get_skill_2_level.return_value = 3
        char_panel.get_skill_3_level.return_value = 2

        weapon_panel = MagicMock()
        weapon_panel.get_selected_data.return_value = {"名称": "测试武器", "基础攻击力": [100]}
        weapon_panel.get_level.return_value = 1
        weapon_panel.get_special_ability_1_name.return_value = ""
        weapon_panel.get_special_ability_1_level.return_value = 0
        weapon_panel.get_special_ability_2_name.return_value = ""
        weapon_panel.get_special_ability_2_level.return_value = 0
        weapon_panel.get_special_ability_3_name.return_value = ""
        weapon_panel.get_special_ability_3_level.return_value = 0
        weapon_panel.get_weapon_special_name.return_value = ""
        weapon_panel.get_weapon_special_level.return_value = 0
        weapon_panel.get_weapon_special_2_name.return_value = ""
        weapon_panel.get_weapon_special_2_level.return_value = 0

        loadout = read_loadout_from_panels(
            char_panel,
            weapon_panel,
            calculation_mode="zone_snapshot",
            weapon_scope_label="当前武器",
            equipment_scope_label="全部装备",
            fixed_loadout=FixedLoadoutSelection(),
            use_manual_multi_skill_counts=False,
            manual_counts={"战技": 0, "连携技": 0, "终结技": 0},
            enemy_defense=100.0,
        )
        self.assertIsNotNone(loadout)
        assert loadout is not None
        self.assertEqual(loadout.skill_levels, (5, 3, 2))

        lines = build_character_attribute_lines(
            char,
            loadout.char_level,
            skill_1_level=loadout.skill_levels[0],
            skill_2_level=loadout.skill_levels[1],
            skill_3_level=loadout.skill_levels[2],
        )
        self.assertTrue(lines)


if __name__ == "__main__":
    unittest.main()
