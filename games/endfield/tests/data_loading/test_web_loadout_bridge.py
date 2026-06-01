# SPDX-License-Identifier: AGPL-3.0
"""Web 配装桥接与桌面 LoadoutState 互认。"""

from __future__ import annotations

import unittest

from games.endfield.data_loading.web_loadout_bridge import (
    build_loadout_state_from_web,
    loadout_state_to_web_preset,
)


class TestWebLoadoutBridge(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
