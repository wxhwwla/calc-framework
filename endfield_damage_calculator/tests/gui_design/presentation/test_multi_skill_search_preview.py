#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""多技能遍历快速预览文案测试。"""

import json
import unittest
from pathlib import Path

from gui_design.presentation.preview_lines import build_multi_skill_search_preview_lines
from tests.fixtures.path_roots import PKG_ROOT

_CHARACTERS_JSON = (
    PKG_ROOT
    / "character_weapon_equipment"
    / "character_data"
    / "characters.json"
)
_WEAPONS_JSON = (
    PKG_ROOT
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


def _sample_catalog() -> dict:
    return {
        "chest": [{"名称": "胸甲A", "装备种类": "护甲", "部位": "护甲", "套装": "", "效果": [], "三件套效果": []}],
        "gloves": [{"名称": "护手A", "部位": "护手", "套装": "", "效果": [], "三件套效果": []}],
        "accessories": [{"名称": "配件A", "部位": "配件", "套装": "", "效果": [], "三件套效果": []}],
    }


class TestMultiSkillSearchPreview(unittest.TestCase):
    def test_preview_lines_include_counts_and_top_result(self) -> None:
        char = _load_by_name(_CHARACTERS_JSON, "秋栗")
        weapon = _load_by_name(_WEAPONS_JSON, "逐鳞3.0")
        lines = build_multi_skill_search_preview_lines(
            char_data=char,
            weapon_data=weapon,
            char_level=1,
            weapon_level=1,
            skill_1_level=5,
            skill_2_level=0,
            skill_3_level=0,
            preview_equipment_catalog=_sample_catalog(),
        )
        self.assertTrue(any(line.startswith("计算模式: 多技能遍历(快速预览)") for line in lines))
        self.assertTrue(any(line.startswith("默认次数:") for line in lines))
        self.assertTrue(any(line.startswith("Top1:") for line in lines))

    def test_preview_lines_use_manual_counts_when_provided(self) -> None:
        char = _load_by_name(_CHARACTERS_JSON, "秋栗")
        weapon = _load_by_name(_WEAPONS_JSON, "逐鳞3.0")
        lines = build_multi_skill_search_preview_lines(
            char_data=char,
            weapon_data=weapon,
            char_level=1,
            weapon_level=1,
            skill_1_level=5,
            skill_2_level=0,
            skill_3_level=0,
            manual_counts={"战技": 2, "连携技": 1, "终结技": 0},
            use_manual_counts=True,
            preview_equipment_catalog=_sample_catalog(),
        )
        self.assertTrue(any(line.startswith("手动次数:") for line in lines))

    def test_preview_lines_warn_when_manual_counts_all_zero(self) -> None:
        char = _load_by_name(_CHARACTERS_JSON, "秋栗")
        weapon = _load_by_name(_WEAPONS_JSON, "逐鳞3.0")
        lines = build_multi_skill_search_preview_lines(
            char_data=char,
            weapon_data=weapon,
            char_level=1,
            weapon_level=1,
            skill_1_level=5,
            skill_2_level=0,
            skill_3_level=0,
            manual_counts={"战技": 0, "连携技": 0, "终结技": 0},
            use_manual_counts=True,
            preview_equipment_catalog=_sample_catalog(),
        )
        self.assertTrue(any("不能全为0" in line for line in lines))

    def test_preview_requires_explicit_catalog(self) -> None:
        char = _load_by_name(_CHARACTERS_JSON, "秋栗")
        weapon = _load_by_name(_WEAPONS_JSON, "逐鳞3.0")
        lines = build_multi_skill_search_preview_lines(
            char_data=char,
            weapon_data=weapon,
            char_level=1,
            weapon_level=1,
            skill_1_level=1,
        )
        self.assertTrue(any("未提供装备 catalog" in line for line in lines))


if __name__ == "__main__":
    unittest.main()
