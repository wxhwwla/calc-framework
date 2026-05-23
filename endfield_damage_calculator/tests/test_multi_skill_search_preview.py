#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""多技能遍历快速预览文案测试。"""

import json
import unittest
from pathlib import Path
from unittest.mock import patch

from gui_design.property_display import build_multi_skill_search_preview_lines

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


class TestMultiSkillSearchPreview(unittest.TestCase):
    @patch("gui_design.property_display.get_equipments")
    @patch("gui_design.property_display.build_equipment_catalog_from_local_rows")
    def test_preview_lines_include_weight_and_top_result(
        self,
        mock_build_catalog,
        mock_get_equipments,
    ):
        mock_get_equipments.return_value = [{"名称": "占位"}]
        mock_build_catalog.return_value = {
            "chest": [{"名称": "胸甲A", "装备种类": "护甲", "部位": "护甲", "套装": "", "效果": [], "三件套效果": []}],
            "gloves": [{"名称": "护手A", "部位": "护手", "套装": "", "效果": [], "三件套效果": []}],
            "accessories": [{"名称": "配件A", "部位": "配件", "套装": "", "效果": [], "三件套效果": []}],
        }
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
        )
        self.assertTrue(any(line.startswith("计算模式: 多技能遍历(快速预览)") for line in lines))
        self.assertTrue(any(line.startswith("默认权重:") for line in lines))
        self.assertTrue(any(line.startswith("Top1:") for line in lines))

    @patch("gui_design.property_display.get_equipments")
    @patch("gui_design.property_display.build_equipment_catalog_from_local_rows")
    def test_preview_lines_use_manual_weights_when_provided(
        self,
        mock_build_catalog,
        mock_get_equipments,
    ):
        mock_get_equipments.return_value = [{"名称": "占位"}]
        mock_build_catalog.return_value = {
            "chest": [{"名称": "胸甲A", "装备种类": "护甲", "部位": "护甲", "套装": "", "效果": [], "三件套效果": []}],
            "gloves": [{"名称": "护手A", "部位": "护手", "套装": "", "效果": [], "三件套效果": []}],
            "accessories": [{"名称": "配件A", "部位": "配件", "套装": "", "效果": [], "三件套效果": []}],
        }
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
            manual_weights={"战技": 2.0, "连携技": 1.0, "终结技": 0.0},
            use_manual_weights=True,
        )
        self.assertTrue(any(line.startswith("手动权重:") for line in lines))

    @patch("gui_design.property_display.get_equipments")
    @patch("gui_design.property_display.build_equipment_catalog_from_local_rows")
    def test_preview_lines_warn_when_manual_weights_all_zero(
        self,
        mock_build_catalog,
        mock_get_equipments,
    ):
        mock_get_equipments.return_value = [{"名称": "占位"}]
        mock_build_catalog.return_value = {
            "chest": [{"名称": "胸甲A", "装备种类": "护甲", "部位": "护甲", "套装": "", "效果": [], "三件套效果": []}],
            "gloves": [{"名称": "护手A", "部位": "护手", "套装": "", "效果": [], "三件套效果": []}],
            "accessories": [{"名称": "配件A", "部位": "配件", "套装": "", "效果": [], "三件套效果": []}],
        }
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
            manual_weights={"战技": 0.0, "连携技": 0.0, "终结技": 0.0},
            use_manual_weights=True,
        )
        self.assertTrue(any("不能全为0" in line for line in lines))


if __name__ == "__main__":
    unittest.main()
