#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""单技能最优搜索 V1 测试。"""

import unittest

from calculation.damage.engine import DamageContext, DamageEffect
from calculation.equipment.system import build_runtime_equipment_from_wiki_draft
from calculation.loadout.slot_search import FixedLoadoutSelection
from calculation.loadout.optimizer import (
    OptimizerConfig,
    WeaponCandidate,
    build_optimizer_search_plan,
    search_best_single_skill_loadouts,
)
from calculation.search.plan.estimate import preview_search_workload
from calculation.search.plan.job import SingleSkillSearchJob
from calculation.search.run.single_skill import estimate_single_skill_search


class TestLoadoutOptimizer(unittest.TestCase):
    def _build_equipment_catalog(self):
        return {
            "chest": [
                build_runtime_equipment_from_wiki_draft(
                    {
                        "名称": "胸甲A",
                        "_wiki_params": {"装备种类": "护甲", "所属套组": "寒霜协议", "效果1": "寒冷伤害+10%"},
                    }
                ),
                build_runtime_equipment_from_wiki_draft(
                    {
                        "名称": "胸甲B",
                        "_wiki_params": {"装备种类": "护甲", "所属套组": "散件"},
                    }
                ),
            ],
            "gloves": [
                build_runtime_equipment_from_wiki_draft(
                    {
                        "名称": "护手A",
                        "_wiki_params": {"部位": "护手", "套装": "寒霜协议", "效果1": "易伤+5%"},
                    }
                ),
            ],
            "accessories": [
                build_runtime_equipment_from_wiki_draft(
                    {
                        "名称": "配件A",
                        "_wiki_params": {"部位": "配件", "套装": "寒霜协议", "三件套效果1": "易伤+10%"},
                    }
                ),
                build_runtime_equipment_from_wiki_draft(
                    {
                        "名称": "配件B",
                        "_wiki_params": {"部位": "配件", "套装": "散件"},
                    }
                ),
            ],
        }

    def test_search_returns_top_n_results(self):
        result = search_best_single_skill_loadouts(
            base_context=DamageContext(
                final_attack=0.0,
                skill_multiplier=1.0,
                enemy_defense=0.0,
                damage_type="法术-寒冷",
            ),
            weapons=[
                WeaponCandidate(name="武器A", final_attack=1000.0),
                WeaponCandidate(name="武器B", final_attack=900.0),
            ],
            equipment_catalog=self._build_equipment_catalog(),
            config=OptimizerConfig(top_n=3, prune_non_beneficial=False),
        )
        self.assertEqual(len(result.top_results), 3)
        self.assertGreaterEqual(result.top_results[0].final_damage, result.top_results[1].final_damage)
        self.assertEqual(result.top_results[0].weapon_name, "武器A")

    def test_search_applies_candidate_filters_and_warns_when_unfiltered(self):
        catalog = self._build_equipment_catalog()
        result = search_best_single_skill_loadouts(
            base_context=DamageContext(final_attack=0.0, skill_multiplier=1.0, enemy_defense=0.0),
            weapons=[WeaponCandidate(name="武器A", final_attack=1000.0)],
            equipment_catalog=catalog,
            config=OptimizerConfig(top_n=1),
        )
        self.assertTrue(any("未筛选" in w for w in result.warnings))

        filtered = search_best_single_skill_loadouts(
            base_context=DamageContext(final_attack=0.0, skill_multiplier=1.0, enemy_defense=0.0),
            weapons=[WeaponCandidate(name="武器A", final_attack=1000.0)],
            equipment_catalog=catalog,
            config=OptimizerConfig(
                top_n=1,
                candidate_equipment_names={"胸甲A", "护手A", "配件A"},
            ),
        )
        self.assertEqual(filtered.total_combinations, 1)
        self.assertEqual(filtered.top_results[0].loadout_names["chest"], "胸甲A")

    def test_affix_only_equipment_counts_as_beneficial_when_pruning(self):
        catalog = {
            "chest": [
                {"名称": "战技甲", "属性词条": ["战技伤害加成10.00%"], "效果": [], "三件套效果": []},
                {"名称": "白板甲", "属性词条": [], "效果": [], "三件套效果": []},
            ],
            "gloves": [{"名称": "手", "属性词条": ["攻击力10"], "效果": [], "三件套效果": []}],
            "accessories": [{"名称": "件", "属性词条": [], "效果": [], "三件套效果": []}],
        }
        pruned = build_optimizer_search_plan(
            weapons=[WeaponCandidate(name="武", final_attack=100.0)],
            equipment_catalog=catalog,
            config=OptimizerConfig(prune_non_beneficial=True, warn_on_unfiltered=False),
        )
        self.assertEqual([x["名称"] for x in pruned.equipment_catalog["chest"]], ["战技甲"])
        self.assertEqual(pruned.total_combinations, 1)

    def test_estimate_matches_full_search_total_with_default_prune(self):
        catalog = {
            "chest": [{"名称": "c1", "属性词条": ["敏捷1"], "效果": [], "三件套效果": []}],
            "gloves": [{"名称": "g1", "属性词条": ["力量1"], "效果": [], "三件套效果": []}],
            "accessories": [
                {"名称": "a1", "属性词条": ["战技伤害加成5.00%"], "效果": [], "三件套效果": []},
                {"名称": "a2", "属性词条": ["连携技伤害加成5.00%"], "效果": [], "三件套效果": []},
            ],
        }
        job = SingleSkillSearchJob(
            char_data={"名称": "测试"},
            char_level=1,
            weapon_level=1,
            trust_level=0,
            skill_label="战技",
            weapon_scope="当前武器",
            equipment_scope="全部装备",
            fixed_loadout=FixedLoadoutSelection(),
            base_context=DamageContext(final_attack=0.0, skill_multiplier=1.0, skill_type="战技", enemy_defense=100.0),
            weapon_candidates=(WeaponCandidate(name="武", final_attack=100.0),),
            equipment_catalog=catalog,
            weapon_data_by_name={},
            run_signature="sig",
        )
        estimate = estimate_single_skill_search(job, max_workers=4, top_n=10)
        search_plan = build_optimizer_search_plan(
            weapons=list(job.weapon_candidates),
            equipment_catalog=job.equipment_catalog,
            config=OptimizerConfig(top_n=10, warn_on_unfiltered=False),
        )
        self.assertEqual(estimate.workload.total_combinations, search_plan.total_combinations)

    def test_search_prunes_obviously_non_beneficial_weapons(self):
        result = search_best_single_skill_loadouts(
            base_context=DamageContext(final_attack=0.0, skill_multiplier=1.0, enemy_defense=0.0),
            weapons=[
                WeaponCandidate(name="有效武器", final_attack=1000.0),
                WeaponCandidate(name="无效武器", final_attack=0.0),
            ],
            equipment_catalog=self._build_equipment_catalog(),
            config=OptimizerConfig(top_n=1, prune_non_beneficial=True),
        )
        self.assertEqual(result.pruned_weapon_count, 1)
        self.assertEqual(result.top_results[0].weapon_name, "有效武器")

    def test_weapon_effects_participate_in_damage(self):
        result = search_best_single_skill_loadouts(
            base_context=DamageContext(final_attack=0.0, skill_multiplier=1.0, enemy_defense=0.0),
            weapons=[
                WeaponCandidate(name="普通武器", final_attack=1000.0),
                WeaponCandidate(
                    name="增伤武器",
                    final_attack=1000.0,
                    effects=[DamageEffect(effect_type="易伤", value=0.1)],
                ),
            ],
            equipment_catalog=self._build_equipment_catalog(),
            config=OptimizerConfig(top_n=1),
        )
        self.assertEqual(result.top_results[0].weapon_name, "增伤武器")


if __name__ == "__main__":
    unittest.main()
