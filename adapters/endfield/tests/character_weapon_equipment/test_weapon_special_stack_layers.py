#!/usr/bin/env python3
"""武器特殊能力：技能等级 × 叠加层数。"""

import unittest

from adapters.endfield.calc.skills.special_fields import (
    add_special_picks_attack_percent,
    special_pick_bonus,
)


class TestSpecialPickBonus(unittest.TestCase):
    def test_stackable_special_multiplies_tier_value_by_stack_count(self) -> None:
        # 九档为「每层叠加%」；8 档每层 18%，叠 2 层 → 36%
        curve = [7.5, 9.0, 10.5, 12.0, 13.5, 15.0, 16.5, 18.0, 21.0]
        self.assertAlmostEqual(special_pick_bonus(curve, 2, skill_level=8, stack_count=2), 36.0)
        self.assertAlmostEqual(special_pick_bonus(curve, 2, skill_level=8, stack_count=0), 0.0)

    def test_non_stackable_special_ignores_zero_stack_count(self) -> None:
        curve = [5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0]
        self.assertAlmostEqual(special_pick_bonus(curve, 1, skill_level=3, stack_count=0), 15.0)

    def test_steel_echo_style_attack_percent(self) -> None:
        weapon = {
            "特殊能力1": [
                True,
                "造成'''物理异常'''时获得攻击力+",
                [7.5, 9.0, 10.5, 12.0, 13.5, 15.0, 16.5, 18.0, 21.0],
                2,
            ],
            "特殊能力2": [False],
        }
        self.assertAlmostEqual(
            add_special_picks_attack_percent(
                weapon,
                ws_name="造成'''物理异常'''时获得攻击力+",
                ws_level=4,
                ws_stack=1,
                target_name="攻击力+",
            ),
            12.0,
        )
        self.assertAlmostEqual(
            add_special_picks_attack_percent(
                weapon,
                ws_name="造成'''物理异常'''时获得攻击力+",
                ws_level=9,
                ws_stack=2,
                target_name="攻击力+",
            ),
            42.0,
        )
        self.assertAlmostEqual(
            add_special_picks_attack_percent(
                weapon,
                ws_name="造成'''物理异常'''时获得攻击力+",
                ws_level=8,
                ws_stack=2,
                target_name="攻击力+",
            ),
            36.0,
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
