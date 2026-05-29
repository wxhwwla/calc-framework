from __future__ import annotations

import unittest

from gui_design.presentation.damage_snapshot import (
    DamageSnapshot,
    _zone_share_percent,
)


class TestDamageSnapshot(unittest.TestCase):
    def test_dataclass_defaults(self) -> None:
        snap = DamageSnapshot(
            segment_damage={"战技:1": 1000.0},
            segment_counts={"战技:1": 3},
            segment_totals={"战技:1": 3000.0},
            skill_type_totals={"战技": 3000.0},
            weighted_total_damage=3000.0,
            rotation_share_percent={"战技:1": 100.0},
            zone_share_percent={"攻击力": 50.0, "增伤": 50.0},
            selected_skill_label="战技",
        )
        self.assertEqual(snap.weighted_total_damage, 3000.0)
        self.assertEqual(snap.segment_damage, {"战技:1": 1000.0})
        self.assertEqual(snap.segment_counts, {"战技:1": 3})
        self.assertEqual(snap.skill_damage, {"战技:1": 1000.0})
        self.assertEqual(snap.skill_counts, {"战技:1": 3})

    def test_dataclass_empty_segments(self) -> None:
        snap = DamageSnapshot(
            segment_damage={},
            segment_counts={},
            segment_totals={},
            skill_type_totals={},
            weighted_total_damage=0.0,
            rotation_share_percent={},
            zone_share_percent={},
            selected_skill_label="",
        )
        self.assertEqual(snap.weighted_total_damage, 0.0)
        self.assertEqual(snap.skill_damage, {})
        self.assertEqual(snap.skill_counts, {})


class TestZoneSharePercent(unittest.TestCase):
    def test_all_equal(self) -> None:
        zones = {"基础伤害区": 2000.0, "暴击区": 2.0, "防御区": 0.5}
        result = _zone_share_percent(zones)
        # 基础伤害区: log(2000)=7.6, 暴击区: log(2)=0.693, 防御区: log(0.5)=0.693
        # 实际已取绝对值, 所以防御区也是 0.693
        self.assertAlmostEqual(sum(result.values()), 100.0, places=4)

    def test_skip_identity(self) -> None:
        zones = {"暴击区": 1.0, "防御区": 2.0}
        result = _zone_share_percent(zones)
        # 暴击区: log(1)=0 → weights[name]==0 → excluded
        self.assertNotIn("暴击区", result)
        self.assertIn("防御区", result)

    def test_zero_no_division_error(self) -> None:
        zones = {name: 0.0 for name in ["基础伤害区", "暴击区", "防御区"]}
        result = _zone_share_percent(zones)
        # 全零值时 weights 为 log(1e-9)*abs=20.7, 因此有值
        self.assertGreater(len(result), 0)
        self.assertAlmostEqual(sum(result.values()), 100.0, places=4)

    def test_mixed_values(self) -> None:
        zones = {"暴击区": 1.5, "防御区": 1.2, "伤害加成区": 2.0}
        result = _zone_share_percent(zones)
        self.assertAlmostEqual(sum(result.values()), 100.0, places=4)

    def test_empty(self) -> None:
        result = _zone_share_percent({})
        self.assertEqual(result, {})
