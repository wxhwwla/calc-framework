#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""武器特殊能力：技能等级 × 叠加层数。"""

import unittest

from character_weapon_equipment.weapon_data.special_fields import (
    add_special_picks_attack_percent,
    special_pick_bonus,
)


class TestSpecialPickBonus(unittest.TestCase):
    def test_stackable_special_multiplies_tier_value_by_stack_count(self) -> None:
        curve = [float(i * 21) for i in range(1, 10)]
        self.assertAlmostEqual(special_pick_bonus(curve, 2, skill_level=8, stack_count=2), 336.0)
        self.assertAlmostEqual(special_pick_bonus(curve, 2, skill_level=8, stack_count=0), 0.0)

    def test_non_stackable_special_ignores_zero_stack_count(self) -> None:
        curve = [5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0]
        self.assertAlmostEqual(special_pick_bonus(curve, 1, skill_level=3, stack_count=0), 15.0)

    def test_steel_echo_style_attack_percent(self) -> None:
        weapon = {
            "特殊能力1": [
                True,
                "造成'''物理异常'''时获得攻击力+",
                [21.0, 42.0, 63.0, 84.0, 105.0, 126.0, 147.0, 168.0, 189.0],
                2,
            ],
            "特殊能力2": [False],
        }
        self.assertAlmostEqual(
            add_special_picks_attack_percent(
                weapon,
                ws_name="造成'''物理异常'''时获得攻击力+",
                ws_level=8,
                ws_stack=2,
                target_name="攻击力+",
            ),
            336.0,
        )
        self.assertAlmostEqual(
            add_special_picks_attack_percent(
                weapon,
                ws_name="造成'''物理异常'''时获得攻击力+",
                ws_level=8,
                ws_stack=0,
                target_name="攻击力+",
            ),
            0.0,
        )

    def test_conditional_special_matches_attack_percent_by_substring(self) -> None:
        weapon = {
            "特殊能力1": [True, "造成物理异常时获得攻击力+", [10.0, 20.0, 30.0], 1],
            "特殊能力2": [False],
        }
        self.assertAlmostEqual(
            add_special_picks_attack_percent(
                weapon,
                ws_name="造成物理异常时获得攻击力+",
                ws_level=2,
                target_name="攻击力+",
            ),
            20.0,
        )


if __name__ == "__main__":
    unittest.main()
