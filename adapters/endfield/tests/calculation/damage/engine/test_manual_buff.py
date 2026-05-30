#!/usr/bin/env python3
"""手动场外 buff 注入单段伤害计算。"""

import unittest

from adapters.endfield.calc.damage.engine import (
    DamageContext,
    calculate_single_hit_damage,
)


class TestManualBuffInjection(unittest.TestCase):
    def test_context_field_buff_adds_to_zone(self):
        result = calculate_single_hit_damage(
            DamageContext(
                final_attack=1000.0,
                skill_multiplier=1.0,
                enemy_defense=0.0,
                crit_rate=0.05,
                crit_damage=0.5,
            ),
            crit_mode="expected",
            manual_buffs=[
                {"effect_type": "暴击率", "value": 0.20},
                {"effect_type": "暴击伤害", "value": 0.30},
            ],
        )
        self.assertAlmostEqual(result.zone_values["暴击区"], 1.0 + 0.25 * 0.80)

    def test_damage_type_bonus_buff_adds_to_damage_bonus_zone(self):
        result = calculate_single_hit_damage(
            DamageContext(
                final_attack=1000.0,
                skill_multiplier=1.0,
                enemy_defense=0.0,
                damage_type="物理",
            ),
            manual_buffs=[
                {"effect_type": "伤害类型加成", "value": 0.15},
            ],
        )
        self.assertAlmostEqual(result.zone_values["伤害加成区"], 1.15)

    def test_amplify_vulnerable_fragile_buffs_inject_as_effects(self):
        result = calculate_single_hit_damage(
            DamageContext(
                final_attack=1000.0,
                skill_multiplier=1.0,
                enemy_defense=0.0,
            ),
            manual_buffs=[
                {"effect_type": "增幅", "value": 0.10},
                {"effect_type": "脆弱", "value": 0.15},
                {"effect_type": "易伤", "value": 0.20},
            ],
        )
        self.assertAlmostEqual(result.zone_values["增幅区"], 1.10)
        self.assertAlmostEqual(result.zone_values["脆弱区"], 1.15)
        self.assertAlmostEqual(result.zone_values["易伤区"], 1.20)

    def test_damage_reduction_combo_special_inject_as_effects(self):
        result = calculate_single_hit_damage(
            DamageContext(
                final_attack=1000.0,
                skill_multiplier=1.0,
                enemy_defense=0.0,
            ),
            manual_buffs=[
                {"effect_type": "伤害减免", "value": 0.10},
                {"effect_type": "连击增伤", "value": 0.25},
                {"effect_type": "特殊乘区", "value": 1.50},
            ],
        )
        self.assertAlmostEqual(result.zone_values["伤害减免区"], 0.90)
        self.assertAlmostEqual(result.zone_values["连击增伤区"], 1.25)
        self.assertAlmostEqual(result.zone_values["特殊乘区"], 1.50)

    def test_multiple_buffs_on_same_type_sum_together(self):
        result = calculate_single_hit_damage(
            DamageContext(
                final_attack=1000.0,
                skill_multiplier=1.0,
                enemy_defense=0.0,
            ),
            manual_buffs=[
                {"effect_type": "增幅", "value": 0.10},
                {"effect_type": "增幅", "value": 0.15},
            ],
        )
        self.assertAlmostEqual(result.zone_values["增幅区"], 1.25)

    def test_empty_and_none_manual_buffs_no_effect(self):
        result_empty = calculate_single_hit_damage(
            DamageContext(
                final_attack=1000.0,
                skill_multiplier=1.0,
                enemy_defense=0.0,
            ),
            manual_buffs=[],
        )
        result_none = calculate_single_hit_damage(
            DamageContext(
                final_attack=1000.0,
                skill_multiplier=1.0,
                enemy_defense=0.0,
            ),
            manual_buffs=None,
        )
        self.assertAlmostEqual(result_empty.zone_values["增幅区"], 1.0)
        self.assertAlmostEqual(result_none.zone_values["增幅区"], 1.0)

    def test_skill_type_bonus_and_imbalance_other_bonuses(self):
        result = calculate_single_hit_damage(
            DamageContext(
                final_attack=1000.0,
                skill_multiplier=1.0,
                enemy_defense=0.0,
                skill_type="战技",
            ),
            manual_buffs=[
                {"effect_type": "技能类型加成", "value": 0.30},
                {"effect_type": "失衡伤害加成", "value": 0.10},
                {"effect_type": "其他伤害加成", "value": 0.05},
            ],
        )
        self.assertAlmostEqual(result.zone_values["伤害加成区"], 1.45)


if __name__ == "__main__":
    unittest.main()
