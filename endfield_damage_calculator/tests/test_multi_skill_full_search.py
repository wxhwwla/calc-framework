#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全量搜索多技能加权评分测试。"""

import unittest

from calculation.damage_engine import DamageContext
from calculation.loadout_optimizer import WeaponCandidate, evaluate_task
from calculation.multi_skill_optimizer import SkillScenario, evaluate_multi_skill_task
from calculation.multi_skill_search_eval import build_multi_skill_search_eval
from calculation.single_skill_search_job import prepare_single_skill_search_job
from calculation.search_task_evaluator import make_loadout_task_evaluator


class TestMultiSkillFullSearch(unittest.TestCase):
    def _char(self):
        return {
            "名称": "测试",
            "武器": "单手剑",
            "战技倍率": [[200] * 3],
            "连携技倍率": [[100] * 3],
            "终结技倍率": [[50] * 3],
            "基础攻击力": [100] * 3,
        }

    def _weapon_row(self, name: str = "A"):
        return {
            "名称": name,
            "类型": "单手剑",
            "星级": 5,
            "基础攻击力": [100] * 3,
        }

    def _slot_item(self, name: str, slot: str):
        return {
            "名称": name,
            "装备种类": "护甲" if slot == "护甲" else slot,
            "部位": slot,
            "套装": "",
            "效果": [],
            "三件套效果": [],
        }

    def _catalog(self):
        return {
            "chest": [self._slot_item("胸甲", "护甲")],
            "gloves": [self._slot_item("护手", "护手")],
            "accessories": [self._slot_item("配件", "配件")],
        }

    def _task_tuple(self, weapon: WeaponCandidate):
        catalog = self._catalog()
        return (
            weapon,
            (
                catalog["chest"][0],
                catalog["gloves"][0],
                catalog["accessories"][0],
                catalog["accessories"][0],
            ),
        )

    def test_weighted_damage_equals_single_times_count(self):
        weapon = WeaponCandidate(name="A", final_attack=1000.0)
        task = self._task_tuple(weapon)
        shared = DamageContext(final_attack=0.0, skill_multiplier=1.0, enemy_defense=100.0)
        single = evaluate_task(
            base_context=DamageContext(
                final_attack=0.0,
                skill_multiplier=2.0,
                skill_type="战技",
                enemy_defense=100.0,
            ),
            crit_mode="non_crit",
            task=task,
        )
        multi = evaluate_multi_skill_task(
            shared_context=shared,
            crit_mode="non_crit",
            task=task,
            scenarios=(SkillScenario(skill_name="战技", skill_multiplier=2.0, skill_type="战技"),),
            skill_counts={"战技": 3, "连携技": 0, "终结技": 0},
        )
        self.assertAlmostEqual(multi.final_damage, single.final_damage * 3)

    def test_prepare_job_with_manual_counts_changes_signature(self):
        catalog = self._catalog()
        kwargs = dict(
            char_data=self._char(),
            char_level=1,
            weapon_level=1,
            trust_level=0,
            skill_name="战技",
            skill_type="战技",
            skill_multiplier=2.0,
            weapon_scope_label="当前武器",
            equipment_scope_label="全部装备",
            all_weapons=[self._weapon_row()],
            current_weapon=self._weapon_row(),
            equipment_catalog=catalog,
        )
        job_single, _ = prepare_single_skill_search_job(**kwargs)
        multi_eval, _ = build_multi_skill_search_eval(
            self._char(),
            skill_1_level=1,
            skill_2_level=1,
            skill_3_level=0,
            manual_counts={"战技": 2, "连携技": 1, "终结技": 0},
        )
        job_multi, _ = prepare_single_skill_search_job(**kwargs, multi_skill_eval=multi_eval)
        assert job_single and job_multi
        self.assertNotEqual(job_single.run_signature, job_multi.run_signature)
        self.assertIn("加权总伤", job_multi.skill_label)

    def test_make_evaluator_uses_multi_skill_when_configured(self):
        catalog = self._catalog()
        multi_eval, _ = build_multi_skill_search_eval(
            self._char(),
            skill_1_level=1,
            skill_2_level=0,
            skill_3_level=0,
            manual_counts={"战技": 2, "连携技": 0, "终结技": 0},
        )
        job, _ = prepare_single_skill_search_job(
            char_data=self._char(),
            char_level=1,
            weapon_level=1,
            trust_level=0,
            skill_name="战技",
            skill_type="战技",
            skill_multiplier=2.0,
            weapon_scope_label="当前武器",
            equipment_scope_label="全部装备",
            all_weapons=[self._weapon_row()],
            current_weapon=self._weapon_row(),
            equipment_catalog=catalog,
            multi_skill_eval=multi_eval,
        )
        assert job is not None
        evaluator = make_loadout_task_evaluator(job, crit_mode="non_crit")
        weapon = job.weapon_candidates[0]
        task = self._task_tuple(weapon)
        score = evaluator(task)
        single = evaluate_task(base_context=job.base_context, crit_mode="non_crit", task=task)
        self.assertAlmostEqual(score.final_damage, single.final_damage * 2)


if __name__ == "__main__":
    unittest.main()
