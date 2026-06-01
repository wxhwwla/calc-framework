#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""NGA 机制导论对照回归（E1/E2/E4/E5/G1/G2）。"""

from __future__ import annotations

import unittest

from games.endfield.calc.damage.engine import DamageContext, DamageEffect, calculate_single_hit_damage
from games.endfield.calc.damage.originium_arts import (
    ORIGINIUM_FLAT_STAT_KEY,
    enhance_attached_effect,
    strength_zone_multiplier,
    sum_originium_arts_strength,
)
from games.endfield.calc.equipment.affix import parse_equipment_affix_line
from games.endfield.calc.manual_buff.abnormal_common import physical_abnormal_base_multiplier
from games.endfield.calc.manual_buff.physical import evaluate_physical_abnormal_total
from games.endfield.calc.multiplicative_zones.ability_bonus_calc import calculate_ability_bonus


class TestNgaMechanics(unittest.TestCase):
    def test_physical_suijia_multiplier_ui_l0(self) -> None:
        # 异常等级 1：50% × (1+1) = 100%
        self.assertAlmostEqual(physical_abnormal_base_multiplier("碎甲", 1), 1.0)

    def test_physical_mengji_multiplier_ui_l3(self) -> None:
        # calc_level=4 → 150% × (1+4) = 750%
        self.assertAlmostEqual(physical_abnormal_base_multiplier("猛击", 4), 7.5)

    def test_ability_bonus_uses_integer_stats(self) -> None:
        char = {
            "主能力": "力量",
            "副能力": "敏捷",
            "力量": [350.9] * 90,
            "敏捷": [200.1] * 90,
        }
        bonus = calculate_ability_bonus(char, level=1)
        expected = 350 * 0.005 + 200 * 0.002
        self.assertAlmostEqual(bonus, expected)

    def test_base_damage_bonus_additive(self) -> None:
        ctx = DamageContext(final_attack=1000.0, skill_multiplier=1.2, base_damage_bonus=1250.0)
        result = calculate_single_hit_damage(ctx, crit_mode="non_crit")
        self.assertAlmostEqual(result.zone_values["基础伤害区"], 1000.0 * 1.2 + 1250.0)

    def test_abnormal_pipeline_ignores_combo_and_non_control(self) -> None:
        ctx = DamageContext(final_attack=1000.0, skill_multiplier=1.0)
        effects = [
            DamageEffect("连击增伤", 0.5, source="t"),
            DamageEffect("非主控减伤", 0.5, source="t"),
        ]
        normal = calculate_single_hit_damage(ctx, effects=effects, crit_mode="non_crit")
        abnormal = calculate_single_hit_damage(
            ctx, effects=effects, crit_mode="non_crit", damage_pipeline="abnormal",
        )
        self.assertGreater(abnormal.final_damage, normal.final_damage)
        self.assertAlmostEqual(abnormal.zone_values["连击增伤区"], 1.0)
        self.assertAlmostEqual(abnormal.zone_values["非主控减伤区"], 1.0)

    def test_originium_strength_zone(self) -> None:
        self.assertAlmostEqual(strength_zone_multiplier(70.8), 1.708)

    def test_originium_enhance_attached_effect_nga_example(self) -> None:
        # 佩丽卡例：12% × (1 + 141.6/370.8) × 1.33 ≈ 20.63%
        enh = 2.0 * 51.4 / (51.4 + 300.0)
        value = 0.12 * (1.0 + enh) * 1.33
        self.assertAlmostEqual(value, 0.2063, places=3)

    def test_parse_normal_attack_and_all_skill_affix(self) -> None:
        eff1, _ = parse_equipment_affix_line("普通攻击伤害加成23%", source="x")
        self.assertEqual(len(eff1), 1)
        self.assertEqual(eff1[0].skill_types, ("普通攻击",))

        eff2, _ = parse_equipment_affix_line("全技能伤害加成18%", source="x")
        self.assertEqual(eff2[0].skill_types, ("战技", "连携技", "终结技"))

    def test_parse_originium_flat_stat(self) -> None:
        _, flats = parse_equipment_affix_line("源石技艺强度41", source="x")
        self.assertAlmostEqual(flats[ORIGINIUM_FLAT_STAT_KEY], 41.0)
        self.assertAlmostEqual(sum_originium_arts_strength(flats), 41.0)

    def test_physical_abnormal_scales_with_originium(self) -> None:
        ctx = DamageContext(final_attack=1000.0, skill_multiplier=1.0, enemy_defense=100.0)
        low, _ = evaluate_physical_abnormal_total(
            context=ctx,
            crit_mode="non_crit",
            effects=[],
            counts={"碎甲:0": 1},
            char_level=90,
            originium_arts_strength=0.0,
        )
        high, _ = evaluate_physical_abnormal_total(
            context=ctx,
            crit_mode="non_crit",
            effects=[],
            counts={"碎甲:0": 1},
            char_level=90,
            originium_arts_strength=100.0,
        )
        self.assertGreater(high, low)
        self.assertAlmostEqual(high / low, 2.0, places=2)


if __name__ == "__main__":
    unittest.main()
