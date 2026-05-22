#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""武器技能面板：标题格式与 bonus 属性提取顺序（无 GUI）。"""

import json
import unittest
from pathlib import Path

from gui_design.selection_components import (
    SpecialAbilityPanel,
    format_weapon_skill_slider_value,
    format_weapon_skill_title,
)

_WEAPONS_JSON = (
    Path(__file__).resolve().parent.parent
    / "character_weapon_equipment"
    / "weapon_data"
    / "weapons.json"
)


def _load_weapon_by_name(name: str) -> dict:
    with _WEAPONS_JSON.open(encoding="utf-8") as f:
        weapons = json.load(f)
    for weapon in weapons:
        if weapon.get("名称") == name:
            return weapon
    raise KeyError(name)


class TestFormatWeaponSkillSliderValue(unittest.TestCase):
    def test_inactive_skill_shows_zero_like_weapon_special(self):
        self.assertEqual(format_weapon_skill_slider_value(active=False), "0")

    def test_active_skill_shows_level(self):
        self.assertEqual(format_weapon_skill_slider_value(active=True, level=3), "3")


class TestFormatWeaponSkillTitle(unittest.TestCase):
    def test_with_attribute_name(self):
        self.assertEqual(
            format_weapon_skill_title("第一技能", "智识+"),
            "第一技能：智识+",
        )

    def test_without_attribute_name(self):
        self.assertEqual(format_weapon_skill_title("第三技能"), "第三技能：无")
        self.assertEqual(format_weapon_skill_title("特殊能力1", ""), "特殊能力1：无")


class TestBonusAttributeOrder(unittest.TestCase):
    def test_jiancheng_casting_bonus_order(self):
        weapon = _load_weapon_by_name("坚城铸造者")
        attrs = SpecialAbilityPanel._extract_bonus_attributes(weapon)
        self.assertEqual(
            attrs,
            ["智识+", "终结技充能效率+", "攻击力+"],
        )

    def test_jiancheng_weapon_special_field(self):
        weapon = _load_weapon_by_name("坚城铸造者")
        available, name = SpecialAbilityPanel._parse_weapon_special_field(weapon)
        self.assertTrue(available)
        self.assertEqual(name, "源石技艺强度+")


if __name__ == "__main__":
    unittest.main()
