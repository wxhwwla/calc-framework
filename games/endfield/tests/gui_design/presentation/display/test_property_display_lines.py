#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""属性列明细文本构建测试。"""



import json
import unittest
from pathlib import Path

from games.endfield.calc.skills.special_fields import read_weapon_skills_schema
from games.endfield.gui.presentation.display_lines import (
    build_character_attribute_lines,
    build_character_skill_lines,
    build_weapon_attribute_lines,
    format_weapon_bonus_display_value,
)
from games.endfield.tests.conftest import DATA_DIR

_CHARACTERS_JSON = DATA_DIR / "characters.json"

_WEAPONS_JSON = DATA_DIR / "weapons.json"





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

            char,

            level=1,

            skill_1_level=5,

            skill_2_level=1,

            skill_3_level=1,

        )

        self.assertIn("战技 等级5 第1段: 199% · 物理(默认物理)", lines)



    def test_character_lines_show_multiple_finale_segments(self):

        char = _load_by_name(_CHARACTERS_JSON, "陈千语")

        lines = build_character_attribute_lines(

            char,

            level=1,

            skill_1_level=1,

            skill_2_level=1,

            skill_3_level=5,

        )

        self.assertIn("终结技 等级5 第1段: 50% · 物理(默认物理)", lines)

        self.assertIn("终结技 等级5 第2段: 636% · 物理(默认物理)", lines)



    def test_character_lines_omit_empty_link_skill_type(self):

        """连携技倍率为空时，连携技滑块>0 也不应出现连携技明细行。"""

        char = {

            "力量": [10],

            "敏捷": [10],

            "智识": [10],

            "意志": [10],

            "基础攻击力": [100],

            "战技倍率": [

                [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200],

            ],

            "连携技倍率": [],

            "终结技倍率": [

                [50, 100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600],

            ],

        }

        lines = build_character_attribute_lines(

            char,

            level=1,

            skill_1_level=5,

            skill_2_level=5,

            skill_3_level=5,

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

                "战技 等级2 第1段: 200% · 物理(默认物理)",

                "战技 等级2 第2段: 无伤害倍率 · 物理(默认物理)",

            ],

        )



    def test_character_skill_line_formats_decimal_percent(self):

        char = {"战技倍率": [[218.5]], "连携技倍率": [], "终结技倍率": []}

        lines = build_character_skill_lines(char, skill_1_level=1)

        self.assertEqual(lines, ["战技 等级1 第1段: 218.5% · 物理(默认物理)"])



    def test_character_lines_are_attribute_only_without_skill_levels(self):

        char = _load_by_name(_CHARACTERS_JSON, "秋栗")

        lines = build_character_attribute_lines(char, level=1)

        self.assertTrue(any(line.startswith("力量:") for line in lines))

        self.assertFalse(any(line.startswith("角色：") for line in lines))

        self.assertFalse(any("战技 " in line for line in lines))



    def test_weapon_lines_are_attribute_only(self):

        weapon = _load_by_name(_WEAPONS_JSON, "坚城铸造者")

        schema = read_weapon_skills_schema(weapon)

        normal = schema["normal_skills"]

        special = schema["special_skills"]

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

        zhishi = format_weapon_bonus_display_value(

            normal[0]["curve"][0],

            attr_name="智识+",

            is_first_skill=True,

        )

        self.assertIn(f"智识+: {zhishi}", lines)

        ce = format_weapon_bonus_display_value(normal[1]["curve"][0], attr_name="终结技充能效率+")

        self.assertIn(f"终结技充能效率+: {ce}", lines)

        atk = format_weapon_bonus_display_value(normal[2]["curve"][0], attr_name="攻击力+")

        self.assertIn(f"攻击力+: {atk}", lines)

        ws_raw = special[0]["curve"][7]

        ws = format_weapon_bonus_display_value(ws_raw, attr_name="源石技艺强度+")

        self.assertIn(f"源石技艺强度+(特殊一): {ws}", lines)

        self.assertFalse(any(line.startswith("武器：") for line in lines))

        self.assertFalse(any(line.startswith("===") for line in lines))



    def test_weapon_lines_support_new_weapon_skills_schema(self):

        weapon = {

            "名称": "测试武器",

            "基础攻击力": [42] * 90,

            "normal_skills": [

                {"zone": 1, "effect": "敏捷+", "curve": [16.0] * 9},

                {"zone": 2, "effect": "攻击力+", "curve": [5.0] * 9},

            ],

            "special_skills": [

                {

                    "zone": 3,

                    "name": "施放战技后，法术伤害+",

                    "condition": "施放战技后",

                    "effect": "法术伤害+",

                    "curve": [12.0] * 9,

                    "max_stack": 2,

                }

            ],

        }

        lines = build_weapon_attribute_lines(

            weapon,

            weapon_level=1,

            sa1_name="敏捷+",

            sa1_level=9,

            sa2_name="攻击力+",

            sa2_level=8,

            ws_name="施放战技后，法术伤害+",

            ws_level=7,

            ws_stack=2,

        )

        self.assertIn("敏捷+: 16", lines)

        self.assertIn("攻击力+: 5%", lines)

        self.assertIn("施放战技后，法术伤害+(特殊一): 24%", lines)



    def test_weapon_lines_accept_new_named_kwargs(self):

        weapon = {

            "名称": "测试武器",

            "基础攻击力": [42] * 90,

            "normal_skills": [

                {"zone": 1, "effect": "敏捷+", "curve": [16.0] * 9},

            ],

            "special_skills": [

                {

                    "zone": 3,

                    "name": "施放战技后，法术伤害+",

                    "condition": "施放战技后",

                    "effect": "法术伤害+",

                    "curve": [12.0] * 9,

                    "max_stack": 2,

                }

            ],

        }

        lines = build_weapon_attribute_lines(

            weapon,

            weapon_level=1,

            normal_skill_1_name="敏捷+",

            normal_skill_1_level=9,

            special_skill_1_name="施放战技后，法术伤害+",

            special_skill_1_level=7,

            special_skill_1_stack=2,

        )

        self.assertIn("敏捷+: 16", lines)

        self.assertIn("施放战技后，法术伤害+(特殊一): 24%", lines)





if __name__ == "__main__":

    unittest.main()

