#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""单技能搜索编排（无头）测试。"""

import unittest

from games.endfield.calc.damage.engine import DamageContext
from games.endfield.calc.loadout.optimizer import WeaponCandidate
from games.endfield.calc.loadout.slot_search import FixedLoadoutSelection
from games.endfield.calc.search.plan.job import SingleSkillSearchJob
from games.endfield.calc.search.run.single_skill import estimate_single_skill_search


class TestSingleSkillSearchRunner(unittest.TestCase):
    def _job(self) -> SingleSkillSearchJob:
        catalog = {
            "chest": [{"名称": "甲", "效果": [1], "三件套效果": []}],
            "gloves": [{"名称": "手", "效果": [1], "三件套效果": []}],
            "accessories": [{"名称": "件", "效果": [1], "三件套效果": []}],
        }

        return SingleSkillSearchJob(
            char_data={"名称": "测试"},
            char_level=1,
            weapon_level=1,
            trust_level=0,
            skill_label="战技",
            weapon_scope="当前武器",
            equipment_scope="全部装备",
            fixed_loadout=FixedLoadoutSelection(),
            base_context=DamageContext(
                final_attack=0.0,
                skill_multiplier=1.0,
                skill_type="战技",
                enemy_defense=100.0,
            ),
            weapon_candidates=(WeaponCandidate(name="A", final_attack=100.0),),
            equipment_catalog=catalog,
            weapon_data_by_name={"A": {"名称": "A", "基础攻击力": [100.0] * 90}},
            run_signature="sig1234567890abcd",
        )

    def test_estimate_single_skill_search_returns_human_text(self):
        estimate = estimate_single_skill_search(self._job(), max_workers=4, top_n=10)

        self.assertIn("预计组合数", estimate.text)

        self.assertGreater(estimate.estimated_seconds, 0.0)


if __name__ == "__main__":
    unittest.main()
