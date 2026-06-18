#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""多技能次数加权测试。"""

import unittest

from games.endfield.calc.damage.engine import DamageContext, DamageEffect
from games.endfield.calc.equipment.system import build_runtime_equipment_from_wiki_draft
from games.endfield.calc.loadout.optimizer import WeaponCandidate
from games.endfield.calc.multi_skill.optimizer import (
    MultiSkillConfig,
    SkillScenario,
    optimize_multi_skill_loadouts,
)


class TestMultiSkillCounts(unittest.TestCase):
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

    def test_default_counts_only_selected_skill_once(self):
        result = optimize_multi_skill_loadouts(
            base_context=DamageContext(final_attack=0.0, skill_multiplier=1.0, enemy_defense=0.0),
            weapons=[WeaponCandidate(name="武器A", final_attack=1000.0)],
            equipment_catalog=self._catalog(),
            scenarios=[
                SkillScenario(skill_name="战技", skill_multiplier=1.0, skill_type="战技"),
                SkillScenario(skill_name="连携技", skill_multiplier=1.0, skill_type="连携技"),
            ],
            config=MultiSkillConfig(selected_skill="连携技", top_n=1),
        )

        self.assertEqual(result.skill_count_map["战技:1"], 0)

        self.assertEqual(result.skill_count_map["连携技:1"], 1)

        self.assertAlmostEqual(result.top_results[0].weighted_total_damage, 1000.0)

    def test_manual_counts_sum_damage_by_cast_times(self):
        result = optimize_multi_skill_loadouts(
            base_context=DamageContext(final_attack=0.0, skill_multiplier=1.0, enemy_defense=0.0),
            weapons=[WeaponCandidate(name="武器A", final_attack=1000.0)],
            equipment_catalog=self._catalog(),
            scenarios=[
                SkillScenario(skill_name="战技", skill_multiplier=1.0, skill_type="战技"),
                SkillScenario(
                    skill_name="终结技",
                    skill_multiplier=1.0,
                    skill_type="终结技",
                    external_effects=(DamageEffect(effect_type="易伤", value=0.5),),
                ),
            ],
            config=MultiSkillConfig(
                skill_counts={"战技": 1, "终结技": 2},
                top_n=1,
            ),
        )

        war = result.top_results[0].skill_breakdown["战技:1"]

        fin = result.top_results[0].skill_breakdown["终结技:1"]

        self.assertAlmostEqual(result.top_results[0].weighted_total_damage, war * 1 + fin * 2)

    def test_all_zero_counts_raise_error(self):
        with self.assertRaises(ValueError):
            optimize_multi_skill_loadouts(
                base_context=DamageContext(final_attack=0.0, skill_multiplier=1.0, enemy_defense=0.0),
                weapons=[WeaponCandidate(name="武器A", final_attack=1000.0)],
                equipment_catalog=self._catalog(),
                scenarios=[SkillScenario(skill_name="战技", skill_multiplier=1.0)],
                config=MultiSkillConfig(skill_counts={"战技": 0}),
            )


if __name__ == "__main__":
    unittest.main()
