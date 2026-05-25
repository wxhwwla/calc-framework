#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""单段伤害预览文案测试。"""

import json
import unittest
from pathlib import Path

from calculation.damage_engine import ZONE_ORDER
from gui_design.display_lines import build_single_hit_damage_lines

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


class TestSingleHitPreview(unittest.TestCase):
    def test_single_hit_preview_lines_include_mode_skill_and_damage(self):
        char = _load_by_name(_CHARACTERS_JSON, "秋栗")
        weapon = _load_by_name(_WEAPONS_JSON, "逐鳞3.0")
        lines = build_single_hit_damage_lines(
            char_data=char,
            weapon_data=weapon,
            char_level=1,
            weapon_level=1,
            skill_1_level=5,
            skill_2_level=0,
            skill_3_level=0,
        )
        self.assertTrue(any(line.startswith("计算模式: 单段伤害计算") for line in lines))
        self.assertTrue(any(line.startswith("技能:") for line in lines))
        self.assertTrue(any(line.startswith("最终攻击力(基础伤害区):") for line in lines))
        self.assertTrue(any(line.startswith("最终伤害:") for line in lines))
        for zone_name in ZONE_ORDER:
            self.assertTrue(
                any(line.startswith(f"{zone_name}:") for line in lines),
                msg=f"missing zone line: {zone_name}",
            )

    def test_single_hit_preview_defaults_to_base_multiplier_when_no_skill_selected(self):
        char = _load_by_name(_CHARACTERS_JSON, "秋栗")
        weapon = _load_by_name(_WEAPONS_JSON, "逐鳞3.0")
        lines = build_single_hit_damage_lines(
            char_data=char,
            weapon_data=weapon,
            char_level=1,
            weapon_level=1,
            skill_1_level=0,
            skill_2_level=0,
            skill_3_level=0,
        )
        self.assertTrue(any("未选择技能等级" in line for line in lines))
        self.assertTrue(any("技能倍率: 100%" in line for line in lines))

    def test_single_hit_preview_accepts_new_weapon_skill_kwargs(self):
        char = _load_by_name(_CHARACTERS_JSON, "秋栗")
        weapon = _load_by_name(_WEAPONS_JSON, "逐鳞3.0")
        lines = build_single_hit_damage_lines(
            char_data=char,
            weapon_data=weapon,
            char_level=1,
            weapon_level=1,
            skill_1_level=1,
            normal_skill_1_name="攻击力+",
            normal_skill_1_level=1,
            special_skill_1_name="施放战技后，法术伤害+",
            special_skill_1_level=1,
            special_skill_1_stack=1,
        )
        self.assertTrue(any(line.startswith("最终伤害:") for line in lines))


if __name__ == "__main__":
    unittest.main()
