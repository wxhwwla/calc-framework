#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""配装最终攻击力：GUI 乘区链与搜索链 parity 测试。"""

import unittest

from calculation.loadout.attack_eval import final_attack_details_for_loadout
from calculation.multiplicative_zones.final_attack_zone import calculate_final_attack_with_details
from calculation.skills.weapon_selection import WeaponSkillSelection


class TestLoadoutAttackEval(unittest.TestCase):
    def _char(self) -> dict:
        return {
            "名称": "测试干员",
            "武器": "单手剑",
            "主能力": "敏捷",
            "副能力": "力量",
            "力量": [10.0] * 90,
            "敏捷": [20.0] * 90,
            "智识": [8.0] * 90,
            "意志": [11.0] * 90,
            "基础攻击力": [100.0] * 90,
        }

    def _weapon(self) -> dict:
        return {
            "名称": "测试武器",
            "类型": "单手剑",
            "星级": 5,
            "基础攻击力": [100.0] * 90,
            "normal_skills": [
                {
                    "zone": 1,
                    "effect": "攻击力+",
                    "curve": [3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 23.4, 26.0],
                },
            ],
            "special_skills": [],
        }

    def test_final_attack_matches_direct_zone_call_with_skill_kwargs(self) -> None:
        char = self._char()
        weapon = self._weapon()
        skills = WeaponSkillSelection.from_preset_view(
            weapon,
            weapon_normal_levels=[9],
            weapon_special_states=[],
        )
        kwargs = skills.calculation_kwargs()
        direct = calculate_final_attack_with_details(
            character=char,
            weapon=weapon,
            char_level=80,
            weapon_level=90,
            trust_level=2,
            **kwargs,
        )
        unified = final_attack_details_for_loadout(
            character=char,
            weapon=weapon,
            char_level=80,
            weapon_level=90,
            trust_level=2,
            weapon_skills=skills,
        )
        self.assertAlmostEqual(unified["final_attack"], direct["final_attack"], places=4)

    def test_prepare_job_carries_weapon_skill_fields(self) -> None:
        from calculation.loadout.slot_search import FixedLoadoutSelection
        from calculation.search.plan.job import prepare_single_skill_search_job

        char = self._char()
        weapon = self._weapon()
        catalog = {
            "chest": [{"名称": "甲", "效果": [], "三件套效果": [], "属性词条": []}],
            "gloves": [{"名称": "手", "效果": [], "三件套效果": [], "属性词条": []}],
            "accessories": [{"名称": "件", "效果": [], "三件套效果": [], "属性词条": []}],
        }
        job, err = prepare_single_skill_search_job(
            char_data=char,
            char_level=80,
            weapon_level=90,
            trust_level=0,
            skill_name="战技",
            skill_type="战技",
            skill_multiplier=1.0,
            weapon_scope_label="当前武器",
            equipment_scope_label="全部装备",
            all_weapons=[weapon],
            current_weapon=weapon,
            equipment_catalog=catalog,
            fixed_loadout=FixedLoadoutSelection(),
            weapon_normal_levels=[9],
            weapon_special_states=[{"level": 7, "stack": 2}],
        )
        assert err is None and job is not None
        self.assertEqual(job.weapon_normal_levels, (9,))
        self.assertEqual(job.weapon_special_states, ({"level": 7, "stack": 2},))

    def test_build_run_signature_includes_weapon_skill_levels(self) -> None:
        from calculation.loadout.slot_search import FixedLoadoutSelection
        from calculation.search.plan.job import build_run_signature

        char = self._char()
        base_kwargs = dict(
            char_data=char,
            char_level=80,
            weapon_level=90,
            trust_level=0,
            skill_name="战技",
            weapon_count=1,
            chest_count=1,
            weapon_scope_label="当前武器",
            equipment_scope_label="全部装备",
            fixed_loadout=FixedLoadoutSelection(),
        )
        sig_a = build_run_signature(**base_kwargs, weapon_normal_levels=[], weapon_special_states=[])
        sig_b = build_run_signature(**base_kwargs, weapon_normal_levels=[9], weapon_special_states=[])
        self.assertNotEqual(sig_a, sig_b)


if __name__ == "__main__":
    unittest.main()
