#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""伤害类型推断与段级读取测试。"""

import unittest

from games.endfield.calc.damage.engine import DamageContext, DamageEffect, calculate_single_hit_damage
from games.endfield.calc.damage.types import (
    DEFAULT_DAMAGE_TYPE,
    damage_type_matches_context,
    format_damage_type_display,
    format_damage_type_short,
    infer_segment_damage_type,
    resolve_segment_damage_type,
)


class TestDamageTypes(unittest.TestCase):
    def test_infer_segment_from_row_header(self) -> None:
        self.assertEqual(infer_segment_damage_type("灼热伤害倍率"), "法术-灼热")

        self.assertEqual(infer_segment_damage_type("物理伤害倍率"), "物理")

        self.assertEqual(infer_segment_damage_type("伤害倍率"), DEFAULT_DAMAGE_TYPE)

    def test_format_short_label(self) -> None:
        self.assertEqual(format_damage_type_short("法术-灼热"), "灼热")

        self.assertEqual(format_damage_type_short("物理"), "物理")

        self.assertEqual(format_damage_type_display("物理", is_default=True), "物理(默认物理)")

    def test_resolve_segment_damage_type(self) -> None:
        char = {
            "战技倍率": [[100]],
            "战技段伤害类型": ["法术-灼热"],
            "连携技倍率": [[100], [200]],
            "连携技段伤害类型": ["物理"],
        }

        self.assertEqual(resolve_segment_damage_type(char, "战技倍率", 1), ("法术-灼热", True))

        self.assertEqual(resolve_segment_damage_type(char, "连携技倍率", 2), (DEFAULT_DAMAGE_TYPE, False))

    def test_spell_umbrella_matches_element_scoped_effect(self) -> None:
        self.assertTrue(
            damage_type_matches_context("法术", ("法术-灼热",)),
        )

        self.assertFalse(
            damage_type_matches_context("物理", ("法术-灼热",)),
        )

    def test_scoped_bonus_applies_per_segment_damage_type(self) -> None:
        ctx_physical = DamageContext(
            final_attack=1000.0,
            skill_multiplier=1.0,
            damage_type="物理",
            skill_type="连携技",
            enemy_defense=0.0,
        )

        ctx_spell = DamageContext(
            final_attack=1000.0,
            skill_multiplier=1.0,
            damage_type="法术-灼热",
            skill_type="连携技",
            enemy_defense=0.0,
        )

        effect = DamageEffect(
            "伤害类型伤害加成",
            value=0.5,
            damage_types=("法术-灼热",),
            source="test",
        )

        physical = calculate_single_hit_damage(ctx_physical, effects=[effect]).final_damage

        spell = calculate_single_hit_damage(ctx_spell, effects=[effect]).final_damage

        self.assertAlmostEqual(physical, 1000.0)

        self.assertAlmostEqual(spell, 1500.0)


if __name__ == "__main__":
    unittest.main()
