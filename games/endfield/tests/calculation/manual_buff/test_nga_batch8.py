#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""NGA 第八批：破防接线、消耗品预设、技力/终结技估算。"""

import unittest

from games.endfield.calc.damage.combat_resources import (
    SP_NATURAL_REGEN_PER_SEC,
    ULTIMATE_CHARGE_PER_100_SP,
    estimate_ultimate_after_actions,
    sp_after_natural_regen,
    ultimate_charge_from_sp_gain,
)
from games.endfield.calc.damage.engine import DamageContext, calculate_single_hit_damage
from games.endfield.calc.manual_buff.consumable_presets import (
    apply_consumable_preset_to_store,
    consumable_preset_buffs,
)
from games.endfield.calc.search.plan.controller import SearchJobInputs, prepare_search_job
from games.endfield.calc.loadout.slot_search import FixedLoadoutSelection


class TestNgaBatch8(unittest.TestCase):
    def test_break_defense_stacks_increase_damage(self) -> None:
        base_ctx = DamageContext(
            final_attack=1000.0,
            skill_multiplier=1.0,
            enemy_defense=100.0,
            break_defense_stacks=0,
        )
        high_ctx = DamageContext(
            final_attack=1000.0,
            skill_multiplier=1.0,
            enemy_defense=100.0,
            break_defense_stacks=4,
        )
        low = calculate_single_hit_damage(base_ctx, crit_mode="non_crit").final_damage
        high = calculate_single_hit_damage(high_ctx, crit_mode="non_crit").final_damage
        self.assertGreater(high, low)

    def test_consumable_iron_bottle_preset(self) -> None:
        buffs = consumable_preset_buffs("铁瓶兴奋剂")
        self.assertEqual(len(buffs), 1)
        self.assertAlmostEqual(float(buffs[0]["value"]), 0.24)
        store: dict[str, list] = {}
        n = apply_consumable_preset_to_store(
            store,
            "铁瓶兴奋剂",
            skill_counts={"战技:1": 1},
            physical_abnormal_counts={},
            spell_abnormal_counts={},
        )
        self.assertEqual(n, 1)
        self.assertIn("战技:1:1", store)

    def test_combat_resources_sp_and_ultimate(self) -> None:
        self.assertAlmostEqual(sp_after_natural_regen(0.0, 5.0), 5.0 * SP_NATURAL_REGEN_PER_SEC)
        self.assertAlmostEqual(ultimate_charge_from_sp_gain(100.0), ULTIMATE_CHARGE_PER_100_SP)
        self.assertAlmostEqual(ultimate_charge_from_sp_gain(50.0, is_refund=True), 0.0)
        charge = estimate_ultimate_after_actions(0.0, sp_gains=(100.0,), link_skill_count=1)
        self.assertAlmostEqual(charge, ULTIMATE_CHARGE_PER_100_SP + 10.0)

    def test_search_job_carries_break_defense(self) -> None:
        char = {
            "名称": "测试",
            "武器": "单手剑",
            "战技倍率": [[200] * 3],
            "连携技倍率": [[100] * 3],
            "终结技倍率": [[50] * 3],
            "基础攻击力": [100] * 3,
        }
        weapon = {"名称": "剑", "类型": "单手剑", "星级": 5, "基础攻击力": [100] * 3}
        catalog = {
            "chest": [{"名称": "甲", "效果": [1], "三件套效果": [], "属性词条": []}],
            "gloves": [{"名称": "手", "效果": [1], "三件套效果": [], "属性词条": []}],
            "accessories": [{"名称": "件", "效果": [1], "三件套效果": [], "属性词条": []}],
        }
        inputs = SearchJobInputs(
            char_data=char,
            char_level=1,
            weapon_level=1,
            trust_level=0,
            skill_name="战技",
            skill_type="战技",
            skill_multiplier=2.0,
            damage_type="物理",
            weapon_scope_label="当前武器",
            equipment_scope_label="全部装备",
            all_weapons=[weapon],
            current_weapon=weapon,
            equipment_catalog=catalog,
            fixed_loadout=FixedLoadoutSelection(),
            break_defense_stacks=3,
        )
        job, err = prepare_search_job(inputs)
        self.assertIsNone(err)
        assert job is not None
        self.assertEqual(job.base_context.break_defense_stacks, 3)


if __name__ == "__main__":
    unittest.main()
