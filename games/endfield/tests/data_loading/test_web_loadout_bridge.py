# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""Web 配装桥接与桌面 LoadoutState 互认。"""

from __future__ import annotations

import unittest

from games.endfield.data_loading.web_loadout_bridge import (
    build_loadout_state_from_web,
    loadout_state_to_web_preset,
    resolve_fixed_loadout_selection,
    resolve_search_skill_fields,
)


class TestWebLoadoutBridge(unittest.TestCase):
    _CATALOG = {
        "chest": [{"名称": "测试护甲", "部位": "护甲"}],
        "gloves": [{"名称": "测试护手", "部位": "护手"}],
        "accessories": [
            {"名称": "配件甲", "部位": "配件"},
            {"名称": "配件乙", "部位": "配件"},
        ],
    }

    def test_roundtrip_preset_fields(self) -> None:
        char = {"名称": "测试角色", "战技倍率": [[1.0]], "连携技倍率": [], "终结技倍率": []}
        weapon = {"名称": "测试武器"}
        body = {
            "char_level": 90,
            "weapon_level": 90,
            "trust_level": 0,
            "skill_1_level": 8,
            "skill_2_level": 7,
            "skill_3_level": 6,
            "enemy_params": {
                "enemy_defense": 200,
                "enemy_tier": "精英",
                "imbalance_efficiency_bonus": 0.15,
            },
            "manual_buffs": {"战技:1:1": [{"effect_type": "伤害加成", "value": 0.1}]},
            "use_manual_multi_skill_counts": True,
            "manual_counts": {"战技:1": 2},
        }
        state = build_loadout_state_from_web(char_data=char, weapon_data=weapon, body=body)
        self.assertEqual(state.skill_levels, (8, 7, 6))
        self.assertEqual(state.enemy_tier, "精英")
        self.assertAlmostEqual(state.imbalance_efficiency_bonus, 0.15)
        self.assertIn("战技:1:1", state.manual_buffs)

        preset = loadout_state_to_web_preset(state)
        self.assertEqual(preset["schema"], "endfield_loadout_preset_v2")
        self.assertEqual(preset["skill_levels"], [8, 7, 6])
        self.assertEqual(preset["enemy_params"]["enemy_tier"], "精英")

    def test_skill_levels_list_fallback(self) -> None:
        char = {"名称": "A", "战技倍率": [[1.0]], "连携技倍率": [], "终结技倍率": []}
        weapon = {"名称": "W"}
        state = build_loadout_state_from_web(
            char_data=char,
            weapon_data=weapon,
            body={"skill_levels": [10, 9, 8]},
        )
        self.assertEqual(state.skill_levels, (10, 9, 8))

    def test_resolve_fixed_loadout_from_names(self) -> None:
        fixed = resolve_fixed_loadout_selection(
            fixed_equipment_names={
                "chest": "测试护甲",
                "gloves": "测试护手",
                "accessory_a": "配件甲",
                "accessory_b": "配件乙",
            },
            equipment_catalog=self._CATALOG,
        )
        self.assertEqual(fixed.chest["名称"], "测试护甲")
        self.assertEqual(fixed.gloves["名称"], "测试护手")
        self.assertEqual(fixed.accessory_a["名称"], "配件甲")
        self.assertEqual(fixed.accessory_b["名称"], "配件乙")

    def test_build_loadout_with_fixed_equipment_names(self) -> None:
        char = {
            "名称": "A",
            "战技倍率": [[100.0]],
            "连携技倍率": [],
            "终结技倍率": [],
        }
        weapon = {"名称": "W"}
        body = {
            "fixed_equipment_names": {"chest": "测试护甲"},
            "equipment_catalog": self._CATALOG,
        }
        state = build_loadout_state_from_web(char_data=char, weapon_data=weapon, body=body)
        self.assertIsNotNone(state.fixed_loadout.chest)
        self.assertEqual(state.fixed_loadout.chest["名称"], "测试护甲")

    def test_resolve_search_skill_fields(self) -> None:
        char = {
            "名称": "A",
            "战技倍率": [[150.0]],
            "连携技倍率": [[200.0]],
            "终结技倍率": [[300.0]],
        }
        name, skill_type, mult, dmg = resolve_search_skill_fields(
            char,
            skill_1_level=8,
            skill_2_level=0,
            skill_3_level=0,
        )
        self.assertEqual(skill_type, "战技")
        self.assertIsInstance(name, str)
        self.assertGreater(len(name), 0)
        self.assertIsInstance(mult, float)
        self.assertIsInstance(dmg, str)


if __name__ == "__main__":
    unittest.main()
