#!/usr/bin/env python3
"""武器特殊能力：等级 0 表示关闭（无 GUI 开关）。"""

import unittest

from adapters.endfield.calc.multiplicative_zones.ability_bonus_details import (
    calculate_ability_bonus_with_details,
)
from character_weapon_equipment.weapon_data.special_fields import read_weapon_special_slots


class TestWeaponSpecialLevel(unittest.TestCase):
    def test_parse_weapon_special_field(self):
        with_special = {
            "特殊能力1": [True, "源石技艺强度+", [10, 20, 30]],
        }
        without = {"特殊能力1": [False]}

        enabled, name = read_weapon_special_slots(with_special)[0][:2]
        self.assertEqual((enabled, name), (True, "源石技艺强度+"))
        enabled2, name2 = read_weapon_special_slots(without)[0][:2]
        self.assertEqual((enabled2, name2), (False, ""))

    def test_ws_level_zero_skips_field_bonus(self):
        char = {
            "主能力": "力量",
            "副能力": "敏捷",
            "力量": [100.0] * 90,
            "敏捷": [50.0] * 90,
        }
        weapon = {
            "特殊能力1": [True, "主能力+", [5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0]],
            "特殊能力2": [False],
        }
        off = calculate_ability_bonus_with_details(char, weapon, level=1, ws_name="主能力+", ws_level=0)
        on = calculate_ability_bonus_with_details(char, weapon, level=1, ws_name="主能力+", ws_level=1)
        self.assertEqual(off["main_pct"], 0.0)
        self.assertEqual(on["main_pct"], 5.0)

    def test_new_named_special_skill_kwargs_are_supported(self):
        char = {
            "主能力": "力量",
            "副能力": "敏捷",
            "力量": [100.0] * 90,
            "敏捷": [50.0] * 90,
        }
        weapon = {
            "special_skills": [
                {
                    "zone": 3,
                    "name": "主能力+",
                    "condition": "",
                    "effect": "主能力+",
                    "curve": [5.0] * 9,
                    "max_stack": 1,
                }
            ]
        }
        on = calculate_ability_bonus_with_details(
            char,
            weapon,
            level=1,
            special_skill_1_name="主能力+",
            special_skill_1_level=1,
            special_skill_1_stack=0,
        )
        self.assertEqual(on["main_pct"], 5.0)

    def test_ability_bonus_warns_on_legacy_skill_names(self):
        char = {
            "主能力": "力量",
            "副能力": "敏捷",
            "力量": [100.0] * 90,
            "敏捷": [50.0] * 90,
        }
        weapon = {
            "特殊能力1": [True, "主能力+", [5.0] * 9],
            "特殊能力2": [False],
        }
        with self.assertWarns(DeprecationWarning):
            calculate_ability_bonus_with_details(
                char,
                weapon,
                level=1,
                ws_name="主能力+",
                ws_level=1,
            )


if __name__ == "__main__":
    unittest.main()
