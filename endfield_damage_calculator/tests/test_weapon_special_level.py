#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""武器特殊能力：等级 0 表示关闭（无 GUI 开关）。"""

import unittest

from calculation.multiplicative_zones.ability_bonus_zone import (
    calculate_ability_bonus_with_details,
)
from gui_design.selection_components import SpecialAbilityPanel


class TestWeaponSpecialLevel(unittest.TestCase):
    def test_parse_weapon_special_field(self):
        with_special = {
            "特殊能力": [True, "源石技艺强度+", [10, 20, 30]],
        }
        without = {"特殊能力": [False]}

        self.assertEqual(
            SpecialAbilityPanel._parse_weapon_special_field(with_special),
            (True, "源石技艺强度+"),
        )
        self.assertEqual(
            SpecialAbilityPanel._parse_weapon_special_field(without),
            (False, ""),
        )

    def test_ws_level_zero_skips_field_bonus(self):
        char = {
            "主能力": "力量",
            "副能力": "敏捷",
            "力量": [100.0] * 90,
            "敏捷": [50.0] * 90,
        }
        weapon = {
            "特殊能力": [True, "主能力+", [5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0]],
        }
        off = calculate_ability_bonus_with_details(
            char, weapon, level=1, ws_name="主能力+", ws_level=0
        )
        on = calculate_ability_bonus_with_details(
            char, weapon, level=1, ws_name="主能力+", ws_level=1
        )
        self.assertEqual(off["main_bonus"], 0.0)
        self.assertEqual(on["main_bonus"], 5.0)


if __name__ == "__main__":
    unittest.main()
