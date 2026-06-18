#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""武器技能面板：标题格式与 bonus 属性提取顺序（无 GUI）。"""

import json
import unittest

from games.endfield.calc.skills.special_fields import (
    bonus_attribute_keys,
    read_weapon_special_slots,
)
from games.endfield.gui.shared.weapon_display_text import (
    extract_effect_display_name,
    format_weapon_skill_slider_value,
    format_weapon_skill_title,
    split_special_skill_display,
)
from games.endfield.tests.conftest import DATA_DIR

_WEAPONS_JSON = DATA_DIR / "weapons.json"


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

    def test_active_skill_shows_plain_level(self):
        self.assertEqual(format_weapon_skill_slider_value(active=True, level=3), "3")


class TestFormatWeaponSkillTitle(unittest.TestCase):
    def test_with_attribute_name(self):
        self.assertEqual(
            format_weapon_skill_title("第一技能", "智识+"),
            "第一技能：智识+",
        )

    def test_without_attribute_name(self):
        self.assertEqual(format_weapon_skill_title("第三技能"), "第三技能：无")

        self.assertEqual(format_weapon_skill_title("特殊一", ""), "特殊一：无")


class TestExtractEffectDisplayName(unittest.TestCase):
    def test_extracts_attr_name_from_conditional_text(self):
        self.assertEqual(
            extract_effect_display_name('造成"物理异常"时获得攻击力+'),
            "攻击力+",
        )

    def test_keeps_plain_attr_name(self):
        self.assertEqual(extract_effect_display_name("源石技艺强度+"), "源石技艺强度+")

    def test_strips_target_received_prefix(self):
        self.assertEqual(
            extract_effect_display_name("目标受到的寒冷伤害+"),
            "寒冷伤害+",
        )


class TestSplitSpecialSkillDisplay(unittest.TestCase):
    def test_split_condition_and_effect(self):
        self.assertEqual(
            split_special_skill_display("施放战技后，攻击力+"),
            ("施放战技后", "攻击力+"),
        )

    def test_plain_effect_has_empty_condition(self):
        self.assertEqual(
            split_special_skill_display("法术伤害+"),
            ("", "法术伤害+"),
        )


class TestBonusAttributeOrder(unittest.TestCase):
    def test_jiancheng_casting_bonus_order(self):
        weapon = _load_weapon_by_name("坚城铸造者")

        attrs = bonus_attribute_keys(weapon)[:3]

        self.assertEqual(
            attrs,
            ["智识+", "终结技充能效率+", "攻击力+"],
        )

    def test_jiancheng_weapon_special_field(self):
        weapon = _load_weapon_by_name("坚城铸造者")

        available, name = read_weapon_special_slots(weapon)[0][:2]

        self.assertTrue(available)

        self.assertEqual(name, "源石技艺强度+")


if __name__ == "__main__":
    unittest.main()
