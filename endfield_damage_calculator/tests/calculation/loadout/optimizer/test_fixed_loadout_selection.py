#!/usr/bin/env python3
"""固定配装 vs 遍历部位组合数。"""

import unittest

from calculation.loadout.optimizer import OptimizerConfig, WeaponCandidate, build_optimizer_search_plan
from calculation.loadout.slot_search import FixedLoadoutSelection, count_loadout_combinations_for_selection


class TestFixedLoadoutSelection(unittest.TestCase):
    def _catalog(self):
        def mk(name):
            return {
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

    def test_zero_fixed_traverses_all_four_slots(self):
        catalog = self._catalog()
        selection = FixedLoadoutSelection()
        total = count_loadout_combinations_for_selection(catalog, selection=selection, allow_duplicate_accessory=True)
        self.assertEqual(total, 16)

    def test_fix_chest_only_varies_other_slots(self):
        catalog = self._catalog()
        selection = FixedLoadoutSelection(chest=catalog["chest"][0])
        total = count_loadout_combinations_for_selection(catalog, selection=selection, allow_duplicate_accessory=True)
        self.assertEqual(total, 2 * 2 * 2)

    def test_fix_all_four_slots_single_loadout(self):
        catalog = self._catalog()
        selection = FixedLoadoutSelection(
            chest=catalog["chest"][0],
            gloves=catalog["gloves"][0],
            accessory_a=catalog["accessories"][0],
            accessory_b=catalog["accessories"][1],
        )
        total = count_loadout_combinations_for_selection(catalog, selection=selection, allow_duplicate_accessory=True)
        self.assertEqual(total, 1)

    def test_optimizer_plan_uses_fixed_loadout(self):
        catalog = self._catalog()
        selection = FixedLoadoutSelection(gloves=catalog["gloves"][1])
        plan = build_optimizer_search_plan(
            weapons=[WeaponCandidate(name="武", final_attack=100.0)],
            equipment_catalog=catalog,
            config=OptimizerConfig(
                fixed_loadout=selection,
                prune_non_beneficial=False,
                warn_on_unfiltered=False,
            ),
        )
        self.assertEqual(plan.total_combinations, 2 * 2 * 2)


if __name__ == "__main__":
    unittest.main()
