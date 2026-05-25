#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""并行评估多条配装任务测试。"""

import unittest

from calculation.loadout.optimizer import LoadoutScore, WeaponCandidate
from calculation.core.parallel_evaluate import evaluate_tasks_parallel


def _dummy_task(i: int):
    slot = {
        "名称": "件",
        "装备种类": "护甲",
        "部位": "护甲",
        "套装": "",
        "效果": [],
        "三件套效果": [],
    }
    return (
        WeaponCandidate(name=f"w{i}", final_attack=1000.0 + i),
        (slot, slot, slot, slot),
    )


class TestParallelEvaluate(unittest.TestCase):
    def test_parallel_matches_serial_order(self) -> None:
        tasks = [_dummy_task(i) for i in range(6)]

        def evaluator(task) -> LoadoutScore:
            weapon, _ = task
            return LoadoutScore(
                weapon_name=weapon.name,
                final_damage=float(weapon.final_attack),
                loadout_names={},
            )

        parallel = evaluate_tasks_parallel(tasks, evaluator, max_workers=2)
        serial = [evaluator(t) for t in tasks]
        self.assertEqual(
            [s.final_damage for s in parallel],
            [s.final_damage for s in serial],
        )


if __name__ == "__main__":
    unittest.main()
