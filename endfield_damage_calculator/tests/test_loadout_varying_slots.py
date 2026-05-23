#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按用户选择的装备件数（1–4）控制遍历格数。"""

import unittest

from calculation.loadout_optimizer import (
    OptimizerConfig,
    WeaponCandidate,
    build_optimizer_search_plan,
    count_loadout_combinations,
    iter_optimizer_tasks,
)
from calculation.loadout_slot_search import varying_slot_mask_from_count


class TestLoadoutVaryingSlots(unittest.TestCase):
    def _catalog(self):
        mk = lambda name: {
            "名称": name,
            "属性词条": ["敏捷1"],
            "效果": [],
            "三件套效果": [],
        }
        return {
            "chest": [mk("胸1"), mk("胸2")],
            "gloves": [mk("手1"), mk("手2")],
            "accessories": [mk("件1"), mk("件2")],
        }

    def test_mask_opens_slots_in_order(self):
        m1 = varying_slot_mask_from_count(1)
        self.assertTrue(m1.chest and not m1.gloves and not m1.accessory_a and not m1.accessory_b)
        m4 = varying_slot_mask_from_count(4)
        self.assertTrue(m4.chest and m4.gloves and m4.accessory_a and m4.accessory_b)

    def test_one_slot_only_iterates_chest_count(self):
        catalog = self._catalog()
        total = count_loadout_combinations(
            catalog,
            allow_duplicate_accessory=True,
            varying_slot_count=1,
        )
        self.assertEqual(total, 2)

    def test_four_slots_full_cartesian(self):
        catalog = self._catalog()
        total = count_loadout_combinations(
            catalog,
            allow_duplicate_accessory=True,
            varying_slot_count=4,
        )
        self.assertEqual(total, 2 * 2 * 2 * 2)

    def test_fixed_slots_use_baseline_first_item_per_slot(self):
        catalog = self._catalog()
        plan = build_optimizer_search_plan(
            weapons=[WeaponCandidate(name="武", final_attack=100.0)],
            equipment_catalog=catalog,
            config=OptimizerConfig(
                varying_slot_count=1,
                prune_non_beneficial=False,
                warn_on_unfiltered=False,
            ),
        )
        loadouts = [
            task[1]
            for task in iter_optimizer_tasks(plan, allow_duplicate_accessory=True)
        ]
        self.assertEqual(len(loadouts), 2)
        self.assertEqual(loadouts[0][1].get("名称"), "手1")
        self.assertEqual(loadouts[0][2].get("名称"), "件1")
        self.assertEqual({loadouts[0][0].get("名称"), loadouts[1][0].get("名称")}, {"胸1", "胸2"})


if __name__ == "__main__":
    unittest.main()
