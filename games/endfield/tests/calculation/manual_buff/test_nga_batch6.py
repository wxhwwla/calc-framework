#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""NGA 第六批：真实伤害/生命汲取、强制法术异常。"""

from __future__ import annotations

import unittest

from games.endfield.calc.damage.engine import DamageContext, calculate_single_hit_damage
from games.endfield.calc.damage.special_damage import (
    effective_defense_multiplier,
    life_steal_heal,
)
from games.endfield.calc.manual_buff.spell import (
    evaluate_spell_abnormal_total,
    partition_spell_abnormal_counts,
)


class TestNgaBatch6(unittest.TestCase):
    def test_true_damage_ignores_defense(self) -> None:
        ctx = DamageContext(final_attack=1000.0, skill_multiplier=1.0, enemy_defense=500.0)
        normal = calculate_single_hit_damage(ctx, crit_mode="non_crit").final_damage
        true_ctx = DamageContext(
            final_attack=1000.0,
            skill_multiplier=1.0,
            enemy_defense=500.0,
            is_true_damage=True,
        )
        true = calculate_single_hit_damage(true_ctx, crit_mode="non_crit").final_damage
        self.assertGreater(true, normal)
        self.assertAlmostEqual(effective_defense_multiplier(enemy_defense=500.0, is_true_damage=True), 1.0)

    def test_life_steal_heal(self) -> None:
        self.assertAlmostEqual(life_steal_heal(1000.0, life_steal_rate=0.15), 150.0)

    def test_forced_spell_abnormal_has_zero_initial(self) -> None:
        ctx = DamageContext(final_attack=1000.0, enemy_defense=100.0)
        normal, br_normal = evaluate_spell_abnormal_total(
            context=ctx,
            crit_mode="non_crit",
            effects=[],
            counts={"电磁异常:0": 1},
            char_level=90,
        )
        forced, br_forced = evaluate_spell_abnormal_total(
            context=ctx,
            crit_mode="non_crit",
            effects=[],
            counts={"强制:电磁异常:0": 1},
            char_level=90,
        )
        self.assertGreater(normal, 0.0)
        self.assertEqual(forced, 0.0)
        self.assertEqual(br_forced.get("电磁异常:0"), 0.0)
        self.assertGreater(br_normal.get("电磁异常:0", 0.0), 0.0)

    def test_partition_forced_prefix(self) -> None:
        counts, forced = partition_spell_abnormal_counts({"强制:灼热异常:1": 2, "碎冰:0": 1})
        self.assertIn("灼热异常:1", forced)
        self.assertEqual(counts.get("灼热异常:1"), 2)


if __name__ == "__main__":
    unittest.main()
