#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""武器属性面板数值展示格式。"""

import unittest

from gui_design.property_display import format_weapon_bonus_display_value


class TestFormatWeaponBonusDisplayValue(unittest.TestCase):
    def test_first_skill_shows_json_integer_not_float(self):
        self.assertEqual(format_weapon_bonus_display_value(60.0, is_first_skill=True), "60")
        self.assertEqual(format_weapon_bonus_display_value(93, is_first_skill=True), "93")

    def test_second_and_third_skills_show_percent(self):
        self.assertEqual(format_weapon_bonus_display_value(27.6, is_first_skill=False), "27.6%")
        self.assertEqual(format_weapon_bonus_display_value(11.0, is_first_skill=False), "11%")

    def test_special_ability_field_shows_percent(self):
        self.assertEqual(format_weapon_bonus_display_value(60.0, is_first_skill=False), "60%")
        self.assertEqual(format_weapon_bonus_display_value(37.1, is_first_skill=False), "37.1%")


if __name__ == "__main__":
    unittest.main()
