#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""NGA 第四批：失衡节点/快速打进、干员承伤抗性。"""

from __future__ import annotations

import unittest

from games.endfield.calc.damage.imbalance import (
    accumulation_multiplier_after_fast_break,
    imbalance_cap_for_tier,
    imbalance_node_thresholds,
    imbalance_nodes_crossed,
)
from games.endfield.calc.damage.incoming import (
    MIN_OPERATOR_RESISTANCE_MULT,
    enemy_incoming_damage_to_operator,
    operator_resistance_multiplier,
    operator_resistance_points,
)


class TestNgaBatch4(unittest.TestCase):
    def test_imbalance_node_thresholds_single_node(self) -> None:
        cap = imbalance_cap_for_tier("普通")
        self.assertAlmostEqual(imbalance_node_thresholds(cap, 1)[0], cap * 0.5)

    def test_imbalance_nodes_crossed(self) -> None:
        cap = 100.0
        self.assertEqual(imbalance_nodes_crossed(40.0, 55.0, cap, node_count=1), (1,))
        self.assertEqual(imbalance_nodes_crossed(55.0, 60.0, cap, node_count=1), ())

    def test_fast_break_penalty_multiplier(self) -> None:
        mult = accumulation_multiplier_after_fast_break(
            tier="普通",
            seconds_since_combat_start=1.0,
            seconds_since_last_imbalance_end=0.5,
            was_fast_break=True,
        )
        self.assertAlmostEqual(mult, 0.5)

    def test_operator_resistance_from_agility(self) -> None:
        # NGA：1000 敏捷 → 乘数 1/(0.001*1000+1)=0.5
        self.assertAlmostEqual(operator_resistance_multiplier(1000.0), 0.5)
        self.assertAlmostEqual(operator_resistance_points(1000.0), 50.0)

    def test_operator_resistance_floor(self) -> None:
        self.assertAlmostEqual(operator_resistance_multiplier(99999.0), MIN_OPERATOR_RESISTANCE_MULT)

    def test_incoming_damage_uses_intellect_for_spell(self) -> None:
        raw = 1000.0
        physical = enemy_incoming_damage_to_operator(raw, agility=1000.0, intellect=0.0, damage_type="物理")
        spell = enemy_incoming_damage_to_operator(raw, agility=0.0, intellect=1000.0, damage_type="法术-灼热")
        self.assertAlmostEqual(physical, 500.0)
        self.assertAlmostEqual(spell, 500.0)


if __name__ == "__main__":
    unittest.main()
