#!/usr/bin/env python3
"""流式遍历任务生成测试。"""

import unittest

from adapters.endfield.calc.loadout.optimizer import (
    OptimizerConfig,
    WeaponCandidate,
    build_optimizer_search_plan,
    iter_optimizer_tasks,
)


class TestStreamingOptimizer(unittest.TestCase):
    def test_each_weapon_repeats_all_loadout_combinations(self):
        catalog = {
            "chest": [{"名称": "c1", "效果": [1], "三件套效果": []}],
            "gloves": [{"名称": "g1", "效果": [1], "三件套效果": []}],
            "accessories": [
                {"名称": "a1", "效果": [1], "三件套效果": []},
                {"名称": "a2", "效果": [1], "三件套效果": []},
            ],
        }
        weapons = [
            WeaponCandidate(name="w1", final_attack=100.0),
            WeaponCandidate(name="w2", final_attack=200.0),
        ]
        plan = build_optimizer_search_plan(
            weapons=weapons,
            equipment_catalog=catalog,
            config=OptimizerConfig(prune_non_beneficial=False, warn_on_unfiltered=False),
        )
        tasks = list(iter_optimizer_tasks(plan, allow_duplicate_accessory=True))
        self.assertEqual(len(tasks), plan.total_combinations)
        self.assertEqual(len(tasks), 8)
        weapon_names = {task[0].name for task in tasks}
        self.assertEqual(weapon_names, {"w1", "w2"})


if __name__ == "__main__":
    unittest.main()
