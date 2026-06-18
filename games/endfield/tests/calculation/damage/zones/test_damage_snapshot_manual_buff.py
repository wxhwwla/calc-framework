#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""伤害快照接入手动 buff 测试。"""

import unittest

from games.endfield.gui.presentation.damage_snapshot import build_damage_snapshot


class TestDamageSnapshotManualBuff(unittest.TestCase):
    def _char(self):
        return {
            "名称": "测试",
            "战技倍率": [[200] * 3],
            "基础攻击力": [100] * 3,
        }

    def _weapon(self):
        return {"名称": "武", "基础攻击力": [100] * 3}

    def test_per_occurrence_buffs_affect_weighted_total(self):
        snap = build_damage_snapshot(
            char_data=self._char(),
            weapon_data=self._weapon(),
            char_level=1,
            weapon_level=1,
            skill_levels=(1, 0, 0),
            skill_counts={"战技:1": 3},
            use_manual_counts=True,
            manual_buffs={
                "战技:1:1": [{"effect_type": "易伤", "value": 0.30}],
                "战技:1:3": [{"effect_type": "增幅", "value": 0.20}],
            },
        )

        self.assertGreater(snap.weighted_total_damage, 0)

        base_without_buffs = snap.segment_damage.get("战技:1", 0)

        with_buffs_once = base_without_buffs * 1.30

        with_buffs_amplify = base_without_buffs * 1.20

        expected = base_without_buffs + with_buffs_once + with_buffs_amplify

        self.assertAlmostEqual(snap.weighted_total_damage, expected)

    def test_no_manual_buffs_same_as_before(self):
        snap = build_damage_snapshot(
            char_data=self._char(),
            weapon_data=self._weapon(),
            char_level=1,
            weapon_level=1,
            skill_levels=(1, 0, 0),
            skill_counts={"战技:1": 2},
            use_manual_counts=True,
        )

        self.assertGreater(snap.weighted_total_damage, 0)

        base = snap.segment_damage["战技:1"]

        self.assertAlmostEqual(snap.weighted_total_damage, base * 2)


if __name__ == "__main__":
    unittest.main()
