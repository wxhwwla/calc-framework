#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""单技能遍历快速预览文案测试。"""

import json
import unittest
from pathlib import Path
from unittest.mock import patch

from calculation.loadout_optimizer import WeaponCandidate
from gui_design.property_display import build_single_skill_search_preview_lines

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


class TestSingleSkillSearchPreview(unittest.TestCase):
    @patch("gui_design.property_display.get_equipment_catalog")
    def test_preview_lines_include_top_result(
        self,
        mock_get_catalog,
    ):
        mock_get_catalog.return_value = {
            "chest": [{"名称": "胸甲A", "装备种类": "护甲", "部位": "护甲", "套装": "", "效果": [], "三件套效果": []}],
            "gloves": [{"名称": "护手A", "部位": "护手", "套装": "", "效果": [], "三件套效果": []}],
            "accessories": [{"名称": "配件A", "部位": "配件", "套装": "", "效果": [], "三件套效果": []}],
        }
        char = _load_by_name(_CHARACTERS_JSON, "秋栗")
        weapon = _load_by_name(_WEAPONS_JSON, "逐鳞3.0")
        lines = build_single_skill_search_preview_lines(
            char_data=char,
            weapon_data=weapon,
            char_level=1,
            weapon_level=1,
            skill_1_level=1,
            skill_2_level=0,
            skill_3_level=0,
        )
        self.assertTrue(any(line.startswith("计算模式: 单技能遍历(快速预览)") for line in lines))
        self.assertTrue(any(line.startswith("预览组合数:") for line in lines))
        self.assertTrue(any(line.startswith("Top1:") for line in lines))

    @patch("gui_design.property_display.get_equipment_catalog")
    def test_preview_lines_respect_candidate_scope_and_weapon_list(
        self,
        mock_get_catalog,
    ):
        mock_get_catalog.return_value = {
            "chest": [{"名称": "胸甲A", "装备种类": "护甲", "部位": "护甲", "套装": "", "效果": [], "三件套效果": []}],
            "gloves": [{"名称": "护手A", "部位": "护手", "套装": "", "效果": [], "三件套效果": []}],
            "accessories": [{"名称": "配件A", "部位": "配件", "套装": "", "效果": [], "三件套效果": []}],
        }
        char = _load_by_name(_CHARACTERS_JSON, "秋栗")
        weapon = _load_by_name(_WEAPONS_JSON, "逐鳞3.0")
        lines = build_single_skill_search_preview_lines(
            char_data=char,
            weapon_data=weapon,
            char_level=1,
            weapon_level=1,
            skill_1_level=1,
            skill_2_level=0,
            skill_3_level=0,
            preview_weapon_candidates=[
                WeaponCandidate(name="候选A", final_attack=1000.0),
                WeaponCandidate(name="候选B", final_attack=1200.0),
            ],
            preview_scope_label="同类型全部",
        )
        self.assertTrue(any(line.startswith("候选范围: 同类型全部") for line in lines))
        self.assertTrue(any("Top1:" in line and "候选B" in line for line in lines))

    @patch("gui_design.property_display.get_equipment_catalog")
    def test_preview_uses_provided_equipment_catalog_without_loading_local_data(
        self,
        mock_get_catalog,
    ):
        char = _load_by_name(_CHARACTERS_JSON, "秋栗")
        weapon = _load_by_name(_WEAPONS_JSON, "逐鳞3.0")
        lines = build_single_skill_search_preview_lines(
            char_data=char,
            weapon_data=weapon,
            char_level=1,
            weapon_level=1,
            skill_1_level=1,
            skill_2_level=0,
            skill_3_level=0,
            preview_weapon_candidates=[WeaponCandidate(name="候选A", final_attack=1000.0)],
            preview_scope_label="当前武器",
            preview_equipment_catalog={
                "chest": [{"名称": "胸甲X", "装备种类": "护甲", "部位": "护甲", "套装": "", "效果": [], "三件套效果": []}],
                "gloves": [{"名称": "护手X", "部位": "护手", "套装": "", "效果": [], "三件套效果": []}],
                "accessories": [{"名称": "配件X", "部位": "配件", "套装": "", "效果": [], "三件套效果": []}],
            },
            preview_equipment_scope_label="仅散件装备",
        )
        self.assertTrue(any(line.startswith("装备范围: 仅散件装备") for line in lines))
        self.assertFalse(mock_get_catalog.called)

    def test_preview_with_real_local_equipments_when_available(self):
        """不 mock 时，本地装备应能跑出 Top 结果而非「数据不完整」。"""
        equip_path = (
            Path(__file__).resolve().parent.parent
            / "character_weapon_equipment"
            / "equipment_data"
            / "equipments.json"
        )
        if not equip_path.is_file():
            self.skipTest("无本地 equipments.json")
        char = _load_by_name(_CHARACTERS_JSON, "秋栗")
        weapon = _load_by_name(_WEAPONS_JSON, "逐鳞3.0")
        lines = build_single_skill_search_preview_lines(
            char_data=char,
            weapon_data=weapon,
            char_level=1,
            weapon_level=1,
            skill_1_level=1,
            skill_2_level=0,
            skill_3_level=0,
        )
        joined = "\n".join(lines)
        self.assertNotIn("装备数据不完整", joined, msg=joined)
        self.assertTrue(any(line.startswith("Top1:") for line in lines), msg=joined)


if __name__ == "__main__":
    unittest.main()
