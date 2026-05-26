#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""手动 buff 数据模型测试。"""

import unittest

from calculation.manual_buff.model import (
    MANUAL_BUFF_ZONE_OPTIONS,
    ManualBuffEntry,
    build_active_keys_from_counts,
    empty_buff_dict,
    get_buffs_for_key,
    set_buffs_for_key,
)


class TestManualBuffModel(unittest.TestCase):
    def test_zone_options_has_12_entries(self):
        self.assertEqual(len(MANUAL_BUFF_ZONE_OPTIONS), 12)
        labels = {label for label, _ in MANUAL_BUFF_ZONE_OPTIONS}
        self.assertIn("暴击率", labels)
        self.assertIn("增幅", labels)
        self.assertIn("特殊乘区", labels)
        self.assertNotIn("庇护", labels)
        self.assertNotIn("虚弱", labels)

    def test_empty_buff_dict(self):
        self.assertEqual(empty_buff_dict(), {})

    def test_get_set_buffs(self):
        store: dict[str, list[dict[str, float]]] = {}
        set_buffs_for_key(
            store,
            "战技:1:2",
            [{"effect_type": "易伤", "value": 0.30}],
        )
        self.assertEqual(
            get_buffs_for_key(store, "战技:1:2"),
            [{"effect_type": "易伤", "value": 0.30}],
        )
        self.assertEqual(get_buffs_for_key(store, "战技:1:1"), [])

    def test_set_empty_buffs_removes_key(self):
        store: dict[str, list[dict[str, float]]] = {}
        set_buffs_for_key(
            store,
            "猛击:0:1",
            [{"effect_type": "增幅", "value": 0.10}],
        )
        self.assertIn("猛击:0:1", store)
        set_buffs_for_key(store, "猛击:0:1", [])
        self.assertNotIn("猛击:0:1", store)

    def test_build_active_keys_skill_segments(self):
        counts = {"战技:1": 2, "连携技:2": 1, "终结技:1": 0}
        keys = build_active_keys_from_counts(
            skill_counts=counts,
            physical_abnormal_counts={},
            spell_abnormal_counts={},
        )
        self.assertIn("战技:1:1", keys)
        self.assertIn("战技:1:2", keys)
        self.assertIn("连携技:2:1", keys)
        self.assertNotIn("终结技:1:1", keys)
        self.assertNotIn("战技:1:3", keys)

    def test_build_active_keys_physical_abnormal(self):
        pab = {"猛击:2": 2, "倒地:0": 1}
        keys = build_active_keys_from_counts(
            skill_counts={},
            physical_abnormal_counts=pab,
            spell_abnormal_counts={},
        )
        self.assertIn("猛击:2:1", keys)
        self.assertIn("猛击:2:2", keys)
        self.assertIn("倒地:0:1", keys)

    def test_build_active_keys_sorts_by_label(self):
        counts = {"连携技:2": 1, "战技:1": 2}
        keys = build_active_keys_from_counts(
            skill_counts=counts,
            physical_abnormal_counts={},
            spell_abnormal_counts={},
        )
        self.assertEqual(keys[0], "战技:1:1")
        self.assertEqual(keys[1], "战技:1:2")
        self.assertEqual(keys[2], "连携技:2:1")


if __name__ == "__main__":
    unittest.main()
