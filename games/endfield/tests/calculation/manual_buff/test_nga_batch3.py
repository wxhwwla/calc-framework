#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""NGA 第三批机制测试。"""

from __future__ import annotations

import unittest

from games.endfield.calc.character_stats import total_max_hp
from games.endfield.calc.damage.corrosion import corrosion_total_resistance_shred
from games.endfield.calc.damage.imbalance import (
    imbalance_cap_for_tier,
    scaled_imbalance_gain,
)
from games.endfield.calc.damage.incoming import enemy_burn_tick_damage
from games.endfield.calc.manual_buff.spell import evaluate_spell_abnormal_total
from games.endfield.calc.damage.engine import DamageContext


class TestNgaBatch3(unittest.TestCase):
    def test_corrosion_duration_increases_shred(self) -> None:
        short = corrosion_total_resistance_shred(1, elapsed_seconds=0.0, originium_arts_strength=0.0)
        long = corrosion_total_resistance_shred(1, elapsed_seconds=15.0, originium_arts_strength=0.0)
        self.assertGreater(long, short)

    def test_potential_multiplier_on_conductive(self) -> None:
        ctx = DamageContext(final_attack=1000.0, enemy_defense=100.0)
        base, _ = evaluate_spell_abnormal_total(
            context=ctx, crit_mode="non_crit", effects=[], counts={"电磁异常:0": 1}, char_level=90,
            attached_effect_multiplier=1.0,
        )
        boosted, _ = evaluate_spell_abnormal_total(
            context=ctx, crit_mode="non_crit", effects=[], counts={"电磁异常:0": 1}, char_level=90,
            attached_effect_multiplier=1.33,
        )
        self.assertGreater(boosted, base)

    def test_enemy_burn_from_max_hp(self) -> None:
        dmg = enemy_burn_tick_damage(6605.0, hot_resistance_percent=0.0)
        self.assertAlmostEqual(dmg, 6605.0 * 0.02, delta=1.0)

    def test_imbalance_cap_by_tier(self) -> None:
        self.assertGreater(imbalance_cap_for_tier("精英"), imbalance_cap_for_tier("普通"))

    def test_scaled_imbalance_with_dianjian(self) -> None:
        self.assertAlmostEqual(scaled_imbalance_gain(10.0, imbalance_efficiency_bonus=0.2), 12.0)

    def test_total_max_hp(self) -> None:
        self.assertGreater(total_max_hp(350.0, level=90), 500.0)


if __name__ == "__main__":
    unittest.main()
