#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""法术异常计算测试。"""

import unittest

from games.endfield.calc.manual_buff.spell import (
    evaluate_spell_abnormal_total,
    format_spell_abnormal_breakdown_lines,
    get_spell_abnormal_param_snapshot,
    normalize_spell_abnormal_counts,
)
from games.endfield.calc.manual_buff.spell_params import (
    SPELL_LEVEL_COEFF_DIVISOR,
    base_multiplier_for_formula,
    calc_level_from_ui,
)
from games.endfield.calc.damage.engine import DamageContext


class TestSpellAbnormal(unittest.TestCase):
    def test_spell_param_snapshot_contains_formulas(self) -> None:
        snapshot = get_spell_abnormal_param_snapshot()
        self.assertIn("灼热异常", snapshot)
        self.assertEqual(snapshot["灼热异常"]["formula"], "burn")
        self.assertEqual(snapshot["灼热爆发"]["formula"], "burst")
        self.assertEqual(snapshot["电磁异常"]["formula"], "cross_anomaly")
        self.assertIn("碎冰", snapshot)
        self.assertEqual(snapshot["碎冰"]["formula"], "shatter_ice")
        self.assertEqual(snapshot["碎冰"]["damage_type"], "物理")
        multipliers = tuple(snapshot["灼热爆发"]["level_multipliers"])  # type: ignore[index]
        self.assertEqual(len(multipliers), 5)
        self.assertTrue(all(v > 0 for v in multipliers))

    def test_normalize_spell_counts_fill_missing_keys(self) -> None:
        counts = normalize_spell_abnormal_counts({"灼热异常:1": 2, "自然爆发:4": 1})
        self.assertEqual(counts["灼热异常:1"], 2)
        self.assertEqual(counts["自然爆发:4"], 1)
        self.assertEqual(counts["电磁异常:0"], 0)
        self.assertEqual(counts["寒冷爆发:3"], 0)

    def test_evaluate_spell_abnormal_total_returns_positive_total(self) -> None:
        total, breakdown = evaluate_spell_abnormal_total(
            context=DamageContext(
                final_attack=1000.0,
                skill_multiplier=1.0,
                damage_type="法术-灼热",
                skill_type="异常",
                enemy_defense=100.0,
                crit_rate=0.0,
                crit_damage=0.0,
            ),
            crit_mode="non_crit",
            effects=[],
            counts={"灼热异常:1": 2, "电磁爆发:3": 1},
            char_level=90,
        )
        self.assertGreater(total, 0.0)
        self.assertIn("灼热异常:1", breakdown)
        self.assertIn("电磁爆发:3", breakdown)

    def test_burst_multiplier_independent_of_ui_level(self) -> None:
        """爆发固定 160%，各 UI 等级基础倍率相同。"""
        level_a = base_multiplier_for_formula("burst", calc_level=calc_level_from_ui(0))
        level_d = base_multiplier_for_formula("burst", calc_level=calc_level_from_ui(4))
        self.assertAlmostEqual(level_a, level_d)

    def test_char_level_increases_spell_damage(self) -> None:
        _, low = evaluate_spell_abnormal_total(
            context=DamageContext(
                final_attack=1000.0,
                skill_multiplier=1.0,
                damage_type="法术-电磁",
                skill_type="异常",
                enemy_defense=0.0,
                crit_rate=0.0,
                crit_damage=0.0,
            ),
            crit_mode="non_crit",
            effects=[],
            counts={"电磁异常:0": 1},
            char_level=1,
        )
        _, high = evaluate_spell_abnormal_total(
            context=DamageContext(
                final_attack=1000.0,
                skill_multiplier=1.0,
                damage_type="法术-电磁",
                skill_type="异常",
                enemy_defense=0.0,
                crit_rate=0.0,
                crit_damage=0.0,
            ),
            crit_mode="non_crit",
            effects=[],
            counts={"电磁异常:0": 1},
            char_level=90,
        )
        self.assertGreater(high["电磁异常:0"], low["电磁异常:0"])
        ratio = high["电磁异常:0"] / low["电磁异常:0"]
        expected_ratio = (1.0 + 89 / SPELL_LEVEL_COEFF_DIVISOR) / 1.0
        self.assertAlmostEqual(ratio, expected_ratio, places=2)

    def test_format_spell_abnormal_breakdown_lines_include_event_kind(self) -> None:
        lines = format_spell_abnormal_breakdown_lines(
            single_hit_breakdown={"灼热异常:2": 123.4, "电磁爆发:1": 88.0},
            counts={"灼热异常:2": 2, "电磁爆发:1": 1},
            indent="  ",
        )
        joined = "\n".join(lines)
        self.assertIn("灼热异常(燃烧)", joined)
        self.assertIn("电磁爆发(爆发)", joined)
        self.assertIn("×2", joined)


if __name__ == "__main__":
    unittest.main()
