#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""NGA 第七批：搜索真实伤害、附表扩展、破防 API。"""

import unittest

from games.endfield.calc.damage.break_defense import (
    MAX_BREAK_DEFENSE_STACKS,
    vulnerability_bonus_from_break_defense,
)
from games.endfield.calc.equipment.display_corrections import (
    correct_flat_stat_value,
    correct_originium_display,
    correct_percent_display,
)
from games.endfield.calc.loadout.slot_search import FixedLoadoutSelection
from games.endfield.calc.search.plan.controller import prepare_search_job
from games.endfield.gui.app.loadout_state import LoadoutState


class TestNgaBatch7(unittest.TestCase):
    def test_search_job_from_loadout_carries_is_true_damage(self) -> None:
        char = {
            "名称": "测试",
            "武器": "单手剑",
            "战技倍率": [[200] * 3],
            "连携技倍率": [[100] * 3],
            "终结技倍率": [[50] * 3],
            "基础攻击力": [100] * 3,
        }
        weapon = {
            "名称": "剑",
            "类型": "单手剑",
            "星级": 5,
            "基础攻击力": [100] * 3,
        }
        catalog = {
            "chest": [{"名称": "甲", "效果": [1], "三件套效果": [], "属性词条": []}],
            "gloves": [{"名称": "手", "效果": [1], "三件套效果": [], "属性词条": []}],
            "accessories": [{"名称": "件", "效果": [1], "三件套效果": [], "属性词条": []}],
        }
        state = LoadoutState(
            char_data=char,
            weapon_data=weapon,
            char_level=1,
            weapon_level=1,
            trust_level=0,
            skill_levels=(1, 0, 0),
            skill_name="战技",
            skill_type="战技",
            skill_multiplier=2.0,
            damage_type="物理",
            calculation_mode="single_hit",
            weapon_scope_label="当前武器",
            equipment_scope_label="全部装备",
            fixed_loadout=FixedLoadoutSelection(),
            fixed_equipment_names={
                "chest": None,
                "gloves": None,
                "accessory_a": None,
                "accessory_b": None,
            },
            use_manual_multi_skill_counts=False,
            manual_counts={"战技": 1, "连携技": 0, "终结技": 0},
            enemy_defense=100.0,
            is_true_damage=True,
        )
        inputs = state.to_search_job_inputs(all_weapons=[weapon], equipment_catalog=catalog)
        self.assertTrue(inputs.is_true_damage)
        job, err = prepare_search_job(inputs)
        self.assertIsNone(err)
        assert job is not None
        self.assertTrue(job.base_context.is_true_damage)

    def test_display_corrections_extended(self) -> None:
        self.assertAlmostEqual(correct_flat_stat_value("防御力", 28), 28.8)
        self.assertAlmostEqual(correct_flat_stat_value("防御力", 36), 36.5)
        self.assertAlmostEqual(correct_originium_display(70), 70.8)
        self.assertAlmostEqual(correct_percent_display(12.3, stat_name="防御力"), 12.25)

    def test_break_defense_vulnerability(self) -> None:
        self.assertAlmostEqual(vulnerability_bonus_from_break_defense(0), 0.0)
        self.assertAlmostEqual(
            vulnerability_bonus_from_break_defense(MAX_BREAK_DEFENSE_STACKS),
            0.32,
        )
        self.assertAlmostEqual(
            vulnerability_bonus_from_break_defense(99),
            vulnerability_bonus_from_break_defense(MAX_BREAK_DEFENSE_STACKS),
        )


if __name__ == "__main__":
    unittest.main()
