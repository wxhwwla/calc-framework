#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""NGA 终批：破防轮转状态机、生存估算、Web API。"""

import unittest

from games.endfield.calc.damage.engine import DamageContext, calculate_single_hit_damage
from games.endfield.calc.damage.physical_abnormal_state import (
    break_defense_stacks_at_hit,
    build_rotation_hit_index,
    iter_rotation_hits,
    ordered_rotation_keys,
)
from games.endfield.calc.survival.estimate import build_survival_estimate


class TestNgaBatch13(unittest.TestCase):
    def test_rotation_hit_order(self) -> None:
        counts = {"战技:1": 2, "连携技:1": 1, "猛击:1": 3}
        keys = ordered_rotation_keys(counts)
        self.assertEqual(keys, ["战技:1", "连携技:1"])
        hits = list(iter_rotation_hits(counts, preferred_order=keys))
        self.assertEqual(len(hits), 3)
        self.assertEqual(hits[-1][2], 3)

    def test_break_defense_rotation_weighted_sum(self) -> None:
        counts = {"战技:1": 2, "战技:2": 1}
        order = ["战技:1", "战技:2"]
        hit_map = build_rotation_hit_index(counts, preferred_order=order)
        base = DamageContext(final_attack=1000.0, skill_multiplier=1.0, enemy_defense=100.0)
        flat_total = 0.0
        rotated_total = 0.0
        for key, occ, _gh in iter_rotation_hits(counts, preferred_order=order):
            gh = hit_map[(key, occ)]
            flat_total += calculate_single_hit_damage(
                DamageContext(
                    final_attack=base.final_attack,
                    skill_multiplier=1.0,
                    enemy_defense=base.enemy_defense,
                    break_defense_stacks=4,
                ),
                crit_mode="non_crit",
            ).final_damage
            rotated_total += calculate_single_hit_damage(
                DamageContext(
                    final_attack=base.final_attack,
                    skill_multiplier=1.0,
                    enemy_defense=base.enemy_defense,
                    break_defense_stacks=break_defense_stacks_at_hit(4, gh),
                ),
                crit_mode="non_crit",
            ).final_damage
        self.assertGreater(rotated_total, 0.0)
        self.assertNotAlmostEqual(flat_total, rotated_total)

    def test_build_survival_estimate(self) -> None:
        out = build_survival_estimate(
            char_data={
                "名称": "T",
                "力量": [100] * 90,
                "意志": [400] * 90,
                "基础攻击力": [500] * 90,
                "武器": "单手剑",
            },
            weapon_data={"名称": "W", "类型": "单手剑", "基础攻击力": [400] * 90},
            char_level=90,
            weapon_level=90,
        )
        self.assertGreater(out["imbalance_cap"], 0.0)
        self.assertGreater(out["healing_amount"], 0.0)

    def test_rotation_hit_index_matches_occurrence(self) -> None:
        idx = build_rotation_hit_index({"战技:1": 2}, preferred_order=["战技:1"])
        self.assertEqual(idx[("战技:1", 1)], 1)
        self.assertEqual(idx[("战技:1", 2)], 2)


if __name__ == "__main__":
    unittest.main()
