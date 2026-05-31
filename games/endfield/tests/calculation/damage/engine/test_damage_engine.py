#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""单段伤害引擎行为测试。"""

import unittest

from games.endfield.calc.damage.engine import (
    DamageContext,
    DamageEffect,
    calculate_single_hit_damage,
)


class TestDamageEngine(unittest.TestCase):
    def test_single_hit_contains_all_zones_with_non_crit_default(self):
        result = calculate_single_hit_damage(
            DamageContext(
                final_attack=1000.0,
                skill_multiplier=2.0,
            )
        )
        self.assertEqual(result.crit_mode, "non_crit")
        self.assertAlmostEqual(result.zone_values["基础伤害区"], 2000.0)
        self.assertAlmostEqual(result.zone_values["暴击区"], 1.0)
        self.assertAlmostEqual(result.zone_values["防御区"], 0.5)
        self.assertAlmostEqual(result.final_damage, 1000.0)
        self.assertEqual(
            tuple(result.zone_values.keys()),
            (
                "基础伤害区",
                "暴击区",
                "伤害加成区",
                "伤害减免区",
                "增幅区",
                "虚弱区",
                "庇护区",
                "脆弱区",
                "易伤区",
                "防御区",
                "失衡易伤区",
                "抗性区",
                "非主控减伤区",
                "连击增伤区",
                "特殊乘区",
            ),
        )

    def test_crit_modes_non_crit_expected_and_always_crit(self):
        base = DamageContext(
            final_attack=1000.0,
            skill_multiplier=1.0,
            enemy_defense=0.0,
            crit_rate=0.5,
            crit_damage=1.0,
        )
        non_crit = calculate_single_hit_damage(base)
        expected = calculate_single_hit_damage(base, crit_mode="expected")
        always = calculate_single_hit_damage(base, crit_mode="always_crit")

        self.assertAlmostEqual(non_crit.final_damage, 1000.0)
        self.assertAlmostEqual(expected.final_damage, 1500.0)
        self.assertAlmostEqual(always.final_damage, 2000.0)

    def test_unknown_effects_are_recorded_without_breaking_calculation(self):
        result = calculate_single_hit_damage(
            DamageContext(
                final_attack=1000.0,
                skill_multiplier=1.0,
                enemy_defense=0.0,
            ),
            effects=[
                DamageEffect(
                    effect_type="神秘增伤",
                    value=0.25,
                    source="测试来源",
                    raw_text="神秘增伤+25%",
                )
            ],
        )
        self.assertAlmostEqual(result.final_damage, 1000.0)
        self.assertEqual(len(result.unknown_effects), 1)
        self.assertEqual(result.unknown_effects[0]["effect_type"], "神秘增伤")
        self.assertTrue(any("神秘增伤" in w for w in result.warnings))

    def test_effect_scope_and_stack_rules_apply_as_expected(self):
        result = calculate_single_hit_damage(
            DamageContext(
                final_attack=1000.0,
                skill_multiplier=1.0,
                enemy_defense=0.0,
                damage_type="法术-寒冷",
            ),
            effects=[
                DamageEffect(effect_type="易伤", value=0.20, damage_types=("法术-寒冷",)),
                DamageEffect(effect_type="易伤", value=0.50, damage_types=("物理",)),
                DamageEffect(effect_type="虚弱", value=0.10),
                DamageEffect(effect_type="虚弱", value=0.20),
                DamageEffect(effect_type="庇护", value=0.30),
                DamageEffect(effect_type="庇护", value=0.90),
            ],
        )
        self.assertAlmostEqual(result.zone_values["易伤区"], 1.2)
        self.assertAlmostEqual(result.zone_values["虚弱区"], 0.72)
        self.assertAlmostEqual(result.zone_values["庇护区"], 0.1)
        self.assertAlmostEqual(result.final_damage, 86.4)


if __name__ == "__main__":
    unittest.main()
