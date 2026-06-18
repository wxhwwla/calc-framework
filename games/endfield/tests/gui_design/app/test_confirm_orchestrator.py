#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""确认编排与 DisplayRequest 接缝测试。"""

import unittest
from unittest.mock import MagicMock

from games.endfield.calc.loadout.slot_search import FixedLoadoutSelection
from games.endfield.gui.app.display_request import build_display_request
from games.endfield.gui.app.loadout_state import LoadoutState


class TestConfirmOrchestrator(unittest.TestCase):
    def _loadout(self) -> LoadoutState:
        return LoadoutState(
            char_data={"名称": "测试"},
            weapon_data={"名称": "武器"},
            char_level=1,
            weapon_level=1,
            trust_level=0,
            skill_levels=(1, 0, 0),
            skill_name="战技",
            skill_type="战技",
            skill_multiplier=1.0,
            damage_type="物理",
            calculation_mode="zone_snapshot",
            weapon_scope_label="当前武器",
            equipment_scope_label="全部装备",
            fixed_loadout=FixedLoadoutSelection(),
            fixed_equipment_names={},
            use_manual_multi_skill_counts=False,
            manual_counts={"战技": 1, "连携技": 0, "终结技": 0},
            enemy_defense=100.0,
            weapon_specials=("", 0) * 5,
        )

    def test_build_display_request_uses_facade_catalog(self) -> None:
        loadout = self._loadout()

        game_data = MagicMock()

        game_data.equipment_catalog.return_value = {"chest": [], "gloves": [], "accessories": []}

        req = build_display_request(loadout, game_data, preview_weapon_candidates=[])

        game_data.equipment_catalog.assert_called_once_with("全部装备")

        self.assertIs(req.loadout, loadout)


if __name__ == "__main__":
    unittest.main()
