#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""search_job Rust 批量评估测试。"""

from __future__ import annotations

import unittest
from dataclasses import replace

from games.endfield.calc.damage.engine import DamageContext
from games.endfield.calc.loadout.optimizer import OptimizerConfig, WeaponCandidate, enumerate_optimizer_tasks
from games.endfield.calc.loadout.slot_search import FixedLoadoutSelection
from games.endfield.calc.multi_skill.optimizer import SkillScenario
from games.endfield.calc.search.evaluate.multi_skill import MultiSkillSearchEval
from games.endfield.calc.search.evaluate.task import make_loadout_task_evaluator
from games.endfield.calc.search.evaluate.task_batch import (
    can_batch_search_job_eval,
    make_loadout_task_evaluator_batch,
)
from games.endfield.calc.search.plan.job import SingleSkillSearchJob


class TestSearchJobTaskBatch(unittest.TestCase):
    def _catalog(self) -> dict:
        return {
            "chest": [{"名称": "甲", "部位": "护甲", "效果": [], "三件套效果": [], "属性词条": []}],
            "gloves": [{"名称": "手", "部位": "护手", "效果": [], "三件套效果": [], "属性词条": []}],
            "accessories": [
                {"名称": "件1", "部位": "配件", "效果": [], "三件套效果": [], "属性词条": []},
                {"名称": "件2", "部位": "配件", "效果": [], "三件套效果": [], "属性词条": []},
            ],
        }

    def _single_skill_job(self) -> SingleSkillSearchJob:
        catalog = self._catalog()
        return SingleSkillSearchJob(
            char_data={"名称": "测试", "武器": "单手剑", "基础攻击力": [100] * 3},
            char_level=80,
            weapon_level=90,
            trust_level=0,
            skill_label="战技",
            weapon_scope="当前武器",
            equipment_scope="全部装备",
            fixed_loadout=FixedLoadoutSelection(),
            base_context=DamageContext(
                final_attack=0.0,
                skill_multiplier=2.0,
                skill_type="战技",
                damage_type="物理",
                enemy_defense=200.0,
            ),
            weapon_candidates=(
                WeaponCandidate(name="W1", final_attack=1200.0),
                WeaponCandidate(name="W2", final_attack=1300.0),
            ),
            equipment_catalog=catalog,
            weapon_data_by_name={
                "W1": {"名称": "W1", "类型": "单手剑", "基础攻击力": [100.0] * 90},
                "W2": {"名称": "W2", "类型": "单手剑", "基础攻击力": [110.0] * 90},
            },
            run_signature="batch-test-sig-0123456789ab",
        )

    def _multi_skill_job(self) -> SingleSkillSearchJob:
        scenario = SkillScenario(
            skill_name="战技:1",
            skill_multiplier=2.0,
            skill_type="战技",
            segment_index=1,
        )
        multi = MultiSkillSearchEval(scenarios=(scenario,), skill_counts={"战技:1": 1})
        return replace(self._single_skill_job(), multi_skill_eval=multi)

    def test_can_batch_false_for_multi_skill(self) -> None:
        self.assertFalse(can_batch_search_job_eval(self._multi_skill_job()))

    def test_batch_matches_single_evaluator(self) -> None:
        job = self._single_skill_job()
        if not can_batch_search_job_eval(job):
            self.skipTest("rust_search 不可用")
        config = OptimizerConfig(prune_non_beneficial=False, warn_on_unfiltered=False)
        tasks = list(
            enumerate_optimizer_tasks(
                base_context=job.base_context,
                weapons=list(job.weapon_candidates),
                equipment_catalog=dict(job.equipment_catalog),
                config=config,
            )[0]
        )
        self.assertGreater(len(tasks), 1)
        single = make_loadout_task_evaluator(job, crit_mode="non_crit")
        batch = make_loadout_task_evaluator_batch(job, crit_mode="non_crit")
        batch_scores = batch(tasks)
        self.assertEqual(len(batch_scores), len(tasks))
        for task, batch_score in zip(tasks, batch_scores):
            single_score = single(task)
            self.assertEqual(single_score.weapon_name, batch_score.weapon_name)
            self.assertAlmostEqual(single_score.final_damage, batch_score.final_damage, places=4)


if __name__ == "__main__":
    unittest.main()
