#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""法术异常骨架测试。"""

import unittest

from calculation.damage_engine import DamageContext
from calculation.spell_abnormal import (
    evaluate_spell_abnormal_total,
    format_spell_abnormal_breakdown_lines,
    get_spell_abnormal_param_snapshot,
    normalize_spell_abnormal_counts,
)


class TestSpellAbnormal(unittest.TestCase):
    def test_spell_param_snapshot_contains_all_core_entries(self) -> None:
        snapshot = get_spell_abnormal_param_snapshot()
        self.assertIn("灼热异常", snapshot)
        self.assertIn("灼热爆发", snapshot)
        self.assertIn("电磁异常", snapshot)
        self.assertIn("电磁爆发", snapshot)
        self.assertIn("寒冷异常", snapshot)
        self.assertIn("寒冷爆发", snapshot)
        self.assertIn("自然异常", snapshot)
        self.assertIn("自然爆发", snapshot)
        for item in snapshot.values():
            coeffs = tuple(item["level_coeffs"])  # type: ignore[index]
            self.assertEqual(len(coeffs), 5)
            self.assertTrue(all(v > 0 for v in coeffs))

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
        )
        self.assertGreater(total, 0.0)
        self.assertIn("灼热异常:1", breakdown)
        self.assertIn("电磁爆发:3", breakdown)

    def test_format_spell_abnormal_breakdown_lines_include_event_kind(self) -> None:
        lines = format_spell_abnormal_breakdown_lines(
            single_hit_breakdown={"灼热异常:2": 123.4, "电磁爆发:1": 88.0},
            counts={"灼热异常:2": 2, "电磁爆发:1": 1},
            indent="  ",
        )
        joined = "\n".join(lines)
        self.assertIn("灼热异常(异常)", joined)
        self.assertIn("电磁爆发(爆发)", joined)
        self.assertIn("×2", joined)


if __name__ == "__main__":
    unittest.main()
