#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""属性列明细文本构建测试。"""

import json
import unittest
from pathlib import Path

from gui_design.property_display import (
    build_character_attribute_lines,
    build_character_skill_lines,
    build_weapon_attribute_lines,
)


_CHARACTERS_JSON = (
    Path(__file__).resolve().parent.parent
    / "character_weapon_equipment"
    / "character_data"
    / "characters.json"
)
_WEAPONS_JSON = (
    Path(__file__).resolve().parent.parent
    / "character_weapon_equipment"
    / "weapon_data"
    / "weapons.json"
)


def _load_by_name(path: Path, name: str) -> dict:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    for item in data:
        if item.get("名称") == name:
            return item
    raise KeyError(name)


class TestPropertyDisplayLines(unittest.TestCase):
    def test_character_lines_include_war_skill_at_selected_level(self):
        char = _load_by_name(_CHARACTERS_JSON, "秋栗")
        lines = build_character_attribute_lines(
            char, level=1, skill_1_level=5, skill_2_level=1, skill_3_level=1,
        )
        self.assertIn("战技 等级5 第1段: 199%", lines)

    def test_character_lines_show_multiple_finale_segments(self):
        char = _load_by_name(_CHARACTERS_JSON, "陈千语")
        lines = build_character_attribute_lines(
            char, level=1, skill_1_level=1, skill_2_level=1, skill_3_level=5,
        )
        self.assertIn("终结技 等级5 第1段: 50%", lines)
        self.assertIn("终结技 等级5 第2段: 636%", lines)

    def test_character_lines_omit_empty_link_skill_type(self):
        char = _load_by_name(_CHARACTERS_JSON, "昼雪")
        lines = build_character_attribute_lines(
            char, level=1, skill_1_level=5, skill_2_level=5, skill_3_level=5,
        )
        self.assertTrue(any(line.startswith("战技 ") for line in lines))
        self.assertFalse(any(line.startswith("连携技 ") for line in lines))
        self.assertTrue(any(line.startswith("终结技 ") for line in lines))

    def test_character_skill_line_shows_no_damage_multiplier_for_null_segment(self):
        char = {
            "战技倍率": [[100, 200, 300], None],
            "连携技倍率": [],
            "终结技倍率": [],
        }
        lines = build_character_skill_lines(char, skill_1_level=2)
        self.assertEqual(
            lines,
            [
                "战技 等级2 第1段: 200%",
                "战技 等级2 第2段: 无伤害倍率",
            ],
        )

    def test_character_skill_line_formats_decimal_percent(self):
        char = {"战技倍率": [[218.5]], "连携技倍率": [], "终结技倍率": []}
        lines = build_character_skill_lines(char, skill_1_level=1)
        self.assertEqual(lines, ["战技 等级1 第1段: 218.5%"])

    def test_character_lines_are_attribute_only_without_skill_levels(self):
        char = _load_by_name(_CHARACTERS_JSON, "秋栗")
        lines = build_character_attribute_lines(char, level=1)
        self.assertTrue(any(line.startswith("力量:") for line in lines))
        self.assertFalse(any(line.startswith("角色：") for line in lines))
        self.assertFalse(any("战技 " in line for line in lines))

    def test_weapon_lines_are_attribute_only(self):
        weapon = _load_by_name(_WEAPONS_JSON, "坚城铸造者")
        lines = build_weapon_attribute_lines(
            weapon,
            weapon_level=1,
            sa1_name="智识+",
            sa1_level=1,
            sa2_name="终结技充能效率+",
            sa2_level=1,
            sa3_name="攻击力+",
            sa3_level=1,
            ws_name="源石技艺强度+",
            ws_level=8,
        )
        self.assertTrue(any(line.startswith("基础攻击力:") for line in lines))
        self.assertIn("智识+: 12", lines)
        self.assertIn("终结技充能效率+: 4.8%", lines)
        self.assertIn("攻击力+: 5%", lines)
        self.assertIn("源石技艺强度+(特殊能力): 60", lines)
        self.assertFalse(any(line.startswith("武器：") for line in lines))
        self.assertFalse(any(line.startswith("===") for line in lines))


if __name__ == "__main__":
    unittest.main()
