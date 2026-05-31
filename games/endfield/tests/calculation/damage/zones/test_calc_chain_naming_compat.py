#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""计算链新命名兼容测试。"""

import unittest

from games.endfield.calc.multiplicative_zones.attribute_zone import (
    calculate_attribute_zones_with_details,
)
from games.endfield.calc.multiplicative_zones.final_attack_zone import (
    calculate_final_attack_with_details,
)


class TestCalcChainNamingCompat(unittest.TestCase):
    def test_attribute_zone_accepts_new_skill_names(self):
        char = {
            "主能力": "力量",
            "副能力": "敏捷",
            "力量": [100.0] * 90,
            "敏捷": [50.0] * 90,
            "智识": [40.0] * 90,
            "意志": [30.0] * 90,
        }
        weapon = {
            "special_skills": [
                {
                    "zone": 3,
                    "name": "力量+",
                    "condition": "",
                    "effect": "力量+",
                    "curve": [6.0] * 9,
                    "max_stack": 1,
                }
            ]
        }
        details = calculate_attribute_zones_with_details(
            char,
            weapon,
            level=1,
            special_skill_1_name="力量+",
            special_skill_1_level=1,
            special_skill_1_stack=0,
        )
        self.assertEqual(details["力量"]["bonus"], 6.0)

    def test_final_attack_accepts_new_skill_names(self):
        char = {
            "主能力": "力量",
            "副能力": "敏捷",
            "基础攻击力": [100.0] * 90,
            "力量": [100.0] * 90,
            "敏捷": [50.0] * 90,
        }
        weapon = {
            "基础攻击力": [50.0] * 90,
            "special_skills": [
                {
                    "zone": 3,
                    "name": "攻击力+",
                    "condition": "",
                    "effect": "攻击力+",
                    "curve": [10.0] * 9,
                    "max_stack": 1,
                }
            ],
        }
        details = calculate_final_attack_with_details(
            character=char,
            weapon=weapon,
            char_level=1,
            weapon_level=1,
            special_skill_1_name="攻击力+",
            special_skill_1_level=1,
            special_skill_1_stack=0,
        )
        self.assertAlmostEqual(details["attack_bonus_multiplier"], 1.1)

    def test_attribute_zone_warns_on_legacy_skill_names(self):
        char = {
            "主能力": "力量",
            "副能力": "敏捷",
            "力量": [100.0] * 90,
            "敏捷": [50.0] * 90,
            "智识": [40.0] * 90,
            "意志": [30.0] * 90,
        }
        weapon = {
            "主能力+": [6.0] * 9,
        }
        with self.assertWarns(DeprecationWarning):
            calculate_attribute_zones_with_details(
                char,
                weapon,
                level=1,
                sa1_name="主能力+",
                sa1_level=1,
            )

    def test_final_attack_warns_on_legacy_skill_names(self):
        char = {
            "主能力": "力量",
            "副能力": "敏捷",
            "基础攻击力": [100.0] * 90,
            "力量": [100.0] * 90,
            "敏捷": [50.0] * 90,
        }
        weapon = {
            "基础攻击力": [50.0] * 90,
            "攻击力+": [10.0] * 9,
        }
        with self.assertWarns(DeprecationWarning):
            calculate_final_attack_with_details(
                character=char,
                weapon=weapon,
                char_level=1,
                weapon_level=1,
                sa1_name="攻击力+",
                sa1_level=1,
            )


if __name__ == "__main__":
    unittest.main()
