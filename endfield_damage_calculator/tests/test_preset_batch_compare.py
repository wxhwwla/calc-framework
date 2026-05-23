#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""多预设并行对比测试。"""

import unittest

from calculation.equipment_system import build_runtime_equipment_from_wiki_draft
from gui_design.loadout_preset import LoadoutPreset
from gui_design.preset_batch_compare import compare_presets_parallel


class TestPresetBatchCompare(unittest.TestCase):
    def _char(self) -> dict:
        return {
            "名称": "测试干员",
            "战技倍率": [[200] * 3],
            "连携技倍率": [[100] * 3],
            "终结技倍率": [[50] * 3],
            "基础攻击力": [100] * 3,
        }

    def _weapon(self) -> dict:
        return {"名称": "测试武器", "基础攻击力": [100] * 3}

    def _equipments(self) -> list[dict]:
        return [
            build_runtime_equipment_from_wiki_draft(
                {
                    "名称": "胸甲A",
                    "_wiki_params": {"装备种类": "护甲", "所属套组": "套A", "效果1": "寒冷伤害+10%"},
                }
            ),
            build_runtime_equipment_from_wiki_draft(
                {
                    "名称": "胸甲B",
                    "_wiki_params": {"装备种类": "护甲", "所属套组": "套B"},
                }
            ),
        ]

    def _preset(self, chest: str) -> LoadoutPreset:
        return LoadoutPreset(
            char_name="测试干员",
            weapon_name="测试武器",
            char_level=1,
            weapon_level=1,
            trust_level=0,
            skill_levels=(1, 0, 0),
            calculation_mode="single_hit",
            weapon_scope="当前武器",
            equipment_scope="全部装备",
            fixed_equipment_names={
                "chest": chest,
                "gloves": None,
                "accessory_a": None,
                "accessory_b": None,
            },
            multi_skill_counts={"战技": 1, "连携技": 0, "终结技": 0},
            use_manual_multi_skill_counts=False,
        )

    def test_parallel_compare_orders_by_damage(self) -> None:
        rows = compare_presets_parallel(
            [self._preset("胸甲A"), self._preset("胸甲B")],
            characters=[self._char()],
            weapons=[self._weapon()],
            equipments=self._equipments(),
            max_workers=2,
        )
        self.assertEqual(len(rows), 2)
        self.assertFalse(any(r.error for r in rows))
        self.assertGreaterEqual(rows[0].final_damage, rows[1].final_damage)

    def test_missing_character_reports_error_row(self) -> None:
        bad = LoadoutPreset(
            char_name="不存在",
            weapon_name="测试武器",
            char_level=1,
            weapon_level=1,
            trust_level=0,
            skill_levels=(1, 0, 0),
            calculation_mode="single_hit",
            weapon_scope="",
            equipment_scope="",
            fixed_equipment_names={},
            multi_skill_counts={},
            use_manual_multi_skill_counts=False,
        )
        rows = compare_presets_parallel(
            [bad],
            characters=[self._char()],
            weapons=[self._weapon()],
            equipments=self._equipments(),
        )
        self.assertEqual(len(rows), 1)
        self.assertIn("未找到角色", rows[0].error)


if __name__ == "__main__":
    unittest.main()
