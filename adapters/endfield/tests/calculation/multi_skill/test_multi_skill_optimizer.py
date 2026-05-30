#!/usr/bin/env python3
"""多技能加权总伤遍历测试。"""

import unittest

from adapters.endfield.calc.damage.engine import DamageContext, DamageEffect
from adapters.endfield.calc.equipment.system import build_runtime_equipment_from_wiki_draft
from adapters.endfield.calc.loadout.optimizer import WeaponCandidate
from adapters.endfield.calc.multi_skill.optimizer import (
    MultiSkillConfig,
    SkillScenario,
    optimize_multi_skill_loadouts,
)


class TestMultiSkillOptimizer(unittest.TestCase):
    def _catalog(self):
        return {
            "chest": [
                build_runtime_equipment_from_wiki_draft(
                    {"名称": "胸甲A", "_wiki_params": {"装备种类": "护甲", "所属套组": "套装A"}}
                )
            ],
            "gloves": [
                build_runtime_equipment_from_wiki_draft(
                    {"名称": "护手A", "_wiki_params": {"部位": "护手", "套装": "套装A"}}
                )
            ],
            "accessories": [
                build_runtime_equipment_from_wiki_draft(
                    {"名称": "配件A", "_wiki_params": {"部位": "配件", "套装": "套装A"}}
                )
            ],
        }

    def test_default_weight_policy_uses_selected_skill(self):
        result = optimize_multi_skill_loadouts(
            base_context=DamageContext(final_attack=0.0, skill_multiplier=1.0, enemy_defense=0.0),
            weapons=[WeaponCandidate(name="武器A", final_attack=1000.0)],
            equipment_catalog=self._catalog(),
            scenarios=[
                SkillScenario(skill_name="战技", skill_multiplier=1.0),
                SkillScenario(skill_name="终结技", skill_multiplier=2.0),
            ],
            config=MultiSkillConfig(selected_skill="终结技", top_n=1),
        )
        self.assertEqual(result.skill_count_map["战技:1"], 0)
        self.assertEqual(result.skill_count_map["终结技:1"], 1)
        self.assertAlmostEqual(result.top_results[0].skill_breakdown["终结技:1"], 2000.0)

    def test_all_zero_counts_raise_error(self):
        with self.assertRaises(ValueError):
            optimize_multi_skill_loadouts(
                base_context=DamageContext(final_attack=0.0, skill_multiplier=1.0, enemy_defense=0.0),
                weapons=[WeaponCandidate(name="武器A", final_attack=1000.0)],
                equipment_catalog=self._catalog(),
                scenarios=[SkillScenario(skill_name="战技", skill_multiplier=1.0)],
                config=MultiSkillConfig(skill_counts={"战技": 0}),
            )

    def test_each_skill_can_have_independent_external_effects(self):
        result = optimize_multi_skill_loadouts(
            base_context=DamageContext(final_attack=0.0, skill_multiplier=1.0, enemy_defense=0.0),
            weapons=[WeaponCandidate(name="武器A", final_attack=1000.0)],
            equipment_catalog=self._catalog(),
            scenarios=[
                SkillScenario(skill_name="战技", skill_multiplier=1.0),
                SkillScenario(
                    skill_name="终结技",
                    skill_multiplier=1.0,
                    external_effects=(DamageEffect(effect_type="易伤", value=0.5),),
                ),
            ],
            config=MultiSkillConfig(skill_counts={"战技": 1, "终结技": 1}, top_n=1),
        )
        self.assertAlmostEqual(result.top_results[0].skill_breakdown["战技:1"], 1000.0)
        self.assertAlmostEqual(result.top_results[0].skill_breakdown["终结技:1"], 1500.0)
        self.assertAlmostEqual(result.top_results[0].weighted_total_damage, 2500.0)


if __name__ == "__main__":
    unittest.main()
