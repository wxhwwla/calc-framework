#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""伤害快照（仪表盘数据）测试。"""

import unittest

from gui_design.damage_snapshot import build_damage_snapshot


class TestDamageSnapshot(unittest.TestCase):
    def _char(self):
        return {
            "名称": "测试",
            "战技倍率": [[200] * 3],
            "连携技倍率": [[100] * 3],
            "终结技倍率": [[50] * 3],
            "基础攻击力": [100] * 3,
        }

    def _weapon(self):
        return {"名称": "武", "基础攻击力": [100] * 3}

    def test_skill_breakdown_respects_manual_counts(self) -> None:
        snap = build_damage_snapshot(
            char_data=self._char(),
            weapon_data=self._weapon(),
            char_level=1,
            weapon_level=1,
            skill_levels=(1, 1, 0),
            skill_counts={"战技:1": 2, "连携技:1": 1, "终结技:1": 0},
            use_manual_counts=True,
        )
        self.assertGreater(snap.segment_damage["战技:1"], 0)
        self.assertGreater(snap.weighted_total_damage, snap.segment_damage["连携技:1"])
        self.assertIn("战技:1", snap.rotation_share_percent)

    def test_zone_shares_sum_to_about_100(self) -> None:
        snap = build_damage_snapshot(
            char_data=self._char(),
            weapon_data=self._weapon(),
            char_level=1,
            weapon_level=1,
            skill_levels=(1, 0, 0),
            skill_counts={"战技:1": 1, "连携技:1": 0, "终结技:1": 0},
            use_manual_counts=False,
        )
        total = sum(snap.zone_share_percent.values())
        self.assertAlmostEqual(total, 100.0, delta=0.5)


if __name__ == "__main__":
    unittest.main()
