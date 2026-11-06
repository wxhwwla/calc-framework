# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""装备裁剪与排序的覆盖扩展测试（P2-07 从 test_coverage_expansion.py 拆分）。"""

from __future__ import annotations


class TestEquipmentPruneExpanded:
    """equipment_stat_affinity_tier, equipment_prune_sort_key."""

    def test_stat_affinity_tier_both(self):
        from games.endfield.calc.equipment.prune import equipment_stat_affinity_tier

        item = {"属性词条": ["力量15", "敏捷10"]}
        tier = equipment_stat_affinity_tier(item, "力量", "敏捷")
        assert tier == 0

    def test_stat_affinity_tier_main_only(self):
        from games.endfield.calc.equipment.prune import equipment_stat_affinity_tier

        item = {"属性词条": ["力量15"]}
        tier = equipment_stat_affinity_tier(item, "力量", "敏捷")
        assert tier == 1

    def test_stat_affinity_tier_sub_only(self):
        from games.endfield.calc.equipment.prune import equipment_stat_affinity_tier

        item = {"属性词条": ["敏捷10"]}
        tier = equipment_stat_affinity_tier(item, "力量", "敏捷")
        assert tier == 2

    def test_stat_affinity_tier_neither(self):
        from games.endfield.calc.equipment.prune import equipment_stat_affinity_tier

        item = {"属性词条": ["智识5"]}
        tier = equipment_stat_affinity_tier(item, "力量", "敏捷")
        assert tier == 3

    def test_skill_affinity_tier_has_bonus(self):
        from games.endfield.calc.equipment.prune import equipment_skill_affinity_tier

        item = {"属性词条": ["战技伤害10%"]}
        tier = equipment_skill_affinity_tier(item, ("战技",))
        assert tier == 0

    def test_skill_affinity_tier_no_bonus(self):
        from games.endfield.calc.equipment.prune import equipment_skill_affinity_tier

        item = {"属性词条": ["普通攻击伤害10%"]}
        tier = equipment_skill_affinity_tier(item, ("战技",))
        assert tier == 1

    def test_skill_affinity_tier_empty_skills(self):
        from games.endfield.calc.equipment.prune import equipment_skill_affinity_tier

        item = {"属性词条": ["战技伤害10%"]}
        tier = equipment_skill_affinity_tier(item, ())
        assert tier == 1

    def test_prune_sort_key(self):
        from games.endfield.calc.equipment.prune import equipment_prune_sort_key

        item = {"名称": "测试装", "属性词条": ["力量15"]}
        key = equipment_prune_sort_key(item, "力量", "敏捷", ("战技",))
        assert isinstance(key, tuple)
        assert len(key) == 3

    def test_sort_equipment_catalog_by_priority(self):
        from games.endfield.calc.equipment.prune import sort_equipment_catalog_by_priority

        catalog = {
            "chest": [
                {"名称": "甲B", "属性词条": []},
                {"名称": "甲A", "属性词条": ["力量15"]},
            ],
            "gloves": [],
            "accessories": [],
        }
        sorted_cat = sort_equipment_catalog_by_priority(
            catalog, main_attr="力量", sub_attr="敏捷", skill_types=("战技",)
        )
        # 甲A before 甲B because it has the main stat
        names = [item["名称"] for item in sorted_cat["chest"]]
        assert names.index("甲A") < names.index("甲B")

    def test_character_ability_attrs(self):
        from games.endfield.calc.equipment.prune import character_ability_attrs

        char = {"主能力": "力量", "副能力": "敏捷"}
        main, sub = character_ability_attrs(char)
        assert main == "力量"
        assert sub == "敏捷"
