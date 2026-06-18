#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""装备剪枝优先级测试。"""

import unittest

from games.endfield.calc.equipment.prune import (
    character_ability_attrs,
    equipment_prune_sort_key,
    equipment_skill_affinity_tier,
    equipment_stat_affinity_tier,
    sort_equipment_catalog_by_priority,
)


class TestEquipmentPrune(unittest.TestCase):
    def test_character_ability_attrs_reads_main_and_sub(self):
        main, sub = character_ability_attrs({"主能力": "敏捷", "副能力": "力量"})

        self.assertEqual(main, "敏捷")

        self.assertEqual(sub, "力量")

    def test_stat_tier_both_main_and_sub_flat(self):
        item = {
            "名称": "双属",
            "属性词条": ["敏捷10", "力量5"],
            "效果": [],
            "三件套效果": [],
        }

        self.assertEqual(equipment_stat_affinity_tier(item, "敏捷", "力量"), 0)

    def test_stat_tier_main_only_via_主能力词条(self):
        item = {"名称": "主", "属性词条": ["主能力20.70%"], "效果": [], "三件套效果": []}

        self.assertEqual(equipment_stat_affinity_tier(item, "敏捷", "力量"), 1)

    def test_stat_tier_sub_only(self):
        item = {"名称": "副", "属性词条": ["力量8"], "效果": [], "三件套效果": []}

        self.assertEqual(equipment_stat_affinity_tier(item, "敏捷", "力量"), 2)

    def test_stat_tier_neither(self):
        item = {"名称": "无", "属性词条": ["智识9"], "效果": [], "三件套效果": []}

        self.assertEqual(equipment_stat_affinity_tier(item, "敏捷", "力量"), 3)

    def test_skill_tier_prefers_matching_skill_bonus(self):
        war = {"名称": "战", "属性词条": ["战技伤害加成10.00%"], "效果": [], "三件套效果": []}

        plain = {"名称": "白", "属性词条": ["攻击力10"], "效果": [], "三件套效果": []}

        self.assertEqual(equipment_skill_affinity_tier(war, ("战技",)), 0)

        self.assertEqual(equipment_skill_affinity_tier(plain, ("战技",)), 1)

    def test_sort_key_orders_better_equipment_first(self):
        best = {"名称": "A", "属性词条": ["敏捷1", "力量1", "战技伤害加成5.00%"]}

        mid = {"名称": "B", "属性词条": ["敏捷1"]}

        worst = {"名称": "C", "属性词条": ["智识1"]}

        key_best = equipment_prune_sort_key(best, "敏捷", "力量", ("战技",))

        key_worst = equipment_prune_sort_key(worst, "敏捷", "力量", ("战技",))

        self.assertLess(key_best, key_worst)

        self.assertLess(key_best, equipment_prune_sort_key(mid, "敏捷", "力量", ("战技",)))

    def test_sort_catalog_within_slot(self):
        catalog = {
            "chest": [
                {"名称": "C", "属性词条": ["智识1"], "效果": [], "三件套效果": []},
                {"名称": "A", "属性词条": ["敏捷1", "力量1"], "效果": [], "三件套效果": []},
            ],
            "gloves": [],
            "accessories": [],
        }

        sorted_cat = sort_equipment_catalog_by_priority(
            catalog, main_attr="敏捷", sub_attr="力量", skill_types=("战技",)
        )

        self.assertEqual([x["名称"] for x in sorted_cat["chest"]], ["A", "C"])


if __name__ == "__main__":
    unittest.main()
