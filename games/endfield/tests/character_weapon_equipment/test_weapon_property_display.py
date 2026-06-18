#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""武器属性面板数值展示格式。"""

import unittest

from games.endfield.gui.presentation.display_lines import format_weapon_bonus_display_value


class TestFormatWeaponBonusDisplayValue(unittest.TestCase):
    def test_first_skill_shows_json_integer_not_float(self):
        self.assertEqual(
            format_weapon_bonus_display_value(60.0, attr_name="智识+", is_first_skill=True),
            "60",
        )

        self.assertEqual(
            format_weapon_bonus_display_value(93, attr_name="敏捷+", is_first_skill=True),
            "93",
        )

    def test_originium_art_skill_attr_shows_integer_without_percent_when_not_first(self):
        self.assertEqual(
            format_weapon_bonus_display_value(60.0, attr_name="源石技艺强度+", is_first_skill=False),
            "60",
        )

    def test_additional_attack_shows_flat_value_not_percent(self):
        self.assertEqual(
            format_weapon_bonus_display_value(12.0, attr_name="附加攻击力+", is_first_skill=False),
            "12",
        )

    def test_second_and_third_skills_show_percent(self):
        self.assertEqual(
            format_weapon_bonus_display_value(27.6, attr_name="攻击力+", is_first_skill=False),
            "27.6%",
        )

        self.assertEqual(
            format_weapon_bonus_display_value(11.0, attr_name="智识+", is_first_skill=False),
            "11",
        )

    def test_non_originium_special_ability_field_shows_percent(self):
        self.assertEqual(
            format_weapon_bonus_display_value(37.1, attr_name="物理伤害+", is_first_skill=False),
            "37.1%",
        )


if __name__ == "__main__":
    unittest.main()
