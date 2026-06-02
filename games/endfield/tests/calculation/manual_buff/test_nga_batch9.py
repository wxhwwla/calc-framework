#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""NGA 第九批：破防状态机、敌人生命插件、承伤/失衡 GUI。"""

import unittest

from games.endfield.calc.damage.enemy_growth import enemy_growth_note, resolve_enemy_max_hp
from games.endfield.calc.damage.incoming import enemy_burn_tick_damage
from games.endfield.calc.damage.physical_abnormal_state import (
    break_defense_after_rotation_hits,
    consume_break_defense_stacks,
    is_physical_abnormal_key,
)
from games.endfield.calc.damage.engine import DamageContext, calculate_single_hit_damage
from games.endfield.gui.app.confirm_refresh import build_display_pending_signature


class TestNgaBatch9(unittest.TestCase):
    def test_physical_abnormal_key_detection(self) -> None:
        self.assertTrue(is_physical_abnormal_key("猛击:2"))
        self.assertFalse(is_physical_abnormal_key("战技:1"))

    def test_break_defense_consumed_by_skill_hits_not_abnormal(self) -> None:
        remaining = break_defense_after_rotation_hits(
            4,
            {"战技:1": 2, "猛击:3": 5},
        )
        self.assertEqual(remaining, 2)
        self.assertEqual(consume_break_defense_stacks(3, consuming_hits=2), 1)

    def test_display_signature_includes_break_defense(self) -> None:
        sig_a = build_display_pending_signature(
            calculation_mode="single_hit",
            char_name="A",
            char_level=1,
            weapon_name="W",
            weapon_level=1,
            trust_level=0,
            skill_levels=(1, 0, 0),
            weapon_specials=tuple(),
            use_manual_multi_skill_counts=False,
            multi_skill_manual_counts={"战技": 1},
            break_defense_stacks=0,
        )
        sig_b = build_display_pending_signature(
            calculation_mode="single_hit",
            char_name="A",
            char_level=1,
            weapon_name="W",
            weapon_level=1,
            trust_level=0,
            skill_levels=(1, 0, 0),
            weapon_specials=tuple(),
            use_manual_multi_skill_counts=False,
            multi_skill_manual_counts={"战技": 1},
            break_defense_stacks=3,
        )
        self.assertNotEqual(sig_a, sig_b)

    def test_enemy_growth_note_and_burn(self) -> None:
        self.assertIn("未硬编码", enemy_growth_note())
        self.assertIsNone(resolve_enemy_max_hp(""))
        tick = enemy_burn_tick_damage(6605.0)
        self.assertGreater(tick, 0.0)

    def test_abnormal_eval_context_break_defense_via_engine(self) -> None:
        ctx = DamageContext(
            final_attack=1000.0,
            skill_multiplier=1.0,
            enemy_defense=100.0,
            break_defense_stacks=4,
            skill_type="异常",
        )
        dmg = calculate_single_hit_damage(ctx, crit_mode="non_crit", damage_pipeline="abnormal").final_damage
        self.assertGreater(dmg, 0.0)


if __name__ == "__main__":
    unittest.main()
