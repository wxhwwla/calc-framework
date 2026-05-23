#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全量搜索编排（search_controller）行为测试。"""

import unittest

from calculation.loadout_optimizer import OptimizerConfig
from calculation.loadout_slot_search import FixedLoadoutSelection
from calculation.search_controller import (
    SearchJobInputs,
    optimizer_config_for_search_job,
    prepare_search_job,
)
from calculation.single_skill_search_runner import estimate_single_skill_search


class TestSearchController(unittest.TestCase):
    def _char(self) -> dict:
        return {
            "名称": "测试干员",
            "武器": "单手剑",
            "战技倍率": [[200] * 3],
            "连携技倍率": [[100] * 3],
            "终结技倍率": [[50] * 3],
            "基础攻击力": [100] * 3,
        }

    def _weapon(self, name: str = "测试武器") -> dict:
        return {
            "名称": name,
            "类型": "单手剑",
            "星级": 5,
            "基础攻击力": [100] * 3,
        }

    def _catalog(self) -> dict:
        slot = {
            "名称": "甲",
            "效果": [1],
            "三件套效果": [],
            "属性词条": [],
        }
        return {
            "chest": [slot],
            "gloves": [dict(slot, 名称="手")],
            "accessories": [dict(slot, 名称="件")],
        }

    def _base_inputs(self, **overrides) -> SearchJobInputs:
        data = dict(
            char_data=self._char(),
            char_level=1,
            weapon_level=1,
            trust_level=0,
            skill_name="战技",
            skill_type="战技",
            skill_multiplier=2.0,
            weapon_scope_label="当前武器",
            equipment_scope_label="全部装备",
            all_weapons=[self._weapon()],
            current_weapon=self._weapon(),
            equipment_catalog=self._catalog(),
            fixed_loadout=FixedLoadoutSelection(),
            enemy_defense=250.0,
            use_manual_multi_skill_counts=False,
            skill_1_level=1,
            skill_2_level=1,
            skill_3_level=0,
            manual_counts={"战技": 2, "连携技": 1, "终结技": 0},
        )
        data.update(overrides)
        return SearchJobInputs(**data)

    def test_prepare_search_job_applies_enemy_defense_to_base_context(self) -> None:
        job, err = prepare_search_job(self._base_inputs(enemy_defense=333.0))
        self.assertIsNone(err)
        assert job is not None
        self.assertEqual(job.base_context.enemy_defense, 333.0)

    def test_manual_multi_skill_attaches_eval_for_estimate_and_run(self) -> None:
        single, err1 = prepare_search_job(self._base_inputs(use_manual_multi_skill_counts=False))
        multi, err2 = prepare_search_job(
            self._base_inputs(use_manual_multi_skill_counts=True)
        )
        self.assertIsNone(err1)
        self.assertIsNone(err2)
        assert single is not None and multi is not None
        self.assertIsNone(single.multi_skill_eval)
        self.assertIsNotNone(multi.multi_skill_eval)
        self.assertNotEqual(single.run_signature, multi.run_signature)

    def test_optimizer_config_for_search_job_matches_estimate_priority(self) -> None:
        job, _ = prepare_search_job(
            self._base_inputs(use_manual_multi_skill_counts=True)
        )
        assert job is not None and job.multi_skill_eval is not None
        cfg = optimizer_config_for_search_job(job, top_n=5)
        self.assertIsInstance(cfg, OptimizerConfig)
        estimate = estimate_single_skill_search(job, max_workers=1, top_n=5)
        self.assertIn("预计组合数", estimate.text)


if __name__ == "__main__":
    unittest.main()
