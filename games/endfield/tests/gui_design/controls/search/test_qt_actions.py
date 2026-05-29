from __future__ import annotations

import unittest

from calculation.loadout.optimizer import LoadoutScore
from gui_design.controls.search.qt_actions import _build_tree_items


class TestBuildTreeItems(unittest.TestCase):
    def test_empty_results_flat_list(self) -> None:
        items = _build_tree_items(
            ["标题行", "内容行"], None,
            damage_metric="伤害",
            segment_counts=None,
            abnormal_counts=None,
            spell_abnormal_counts=None,
        )
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].text(0), "标题行")

    def test_no_top_results_empty_lines(self) -> None:
        items = _build_tree_items(
            [], None,
            damage_metric="伤害",
            segment_counts=None,
            abnormal_counts=None,
            spell_abnormal_counts=None,
        )
        self.assertEqual(len(items), 0)

    def test_top_results_no_segment_breakdown(self) -> None:
        scores = [
            LoadoutScore(
                weapon_name="测试剑",
                final_damage=5000.0,
                loadout_names={"chest": "甲", "gloves": "手", "accessory_a": "A", "accessory_b": "B"},
            )
        ]
        items = _build_tree_items(
            [], scores,
            damage_metric="伤害",
            segment_counts=None,
            abnormal_counts=None,
            spell_abnormal_counts=None,
        )
        self.assertEqual(len(items), 1)
        self.assertIn("测试剑", items[0].text(0))
        self.assertIn("5000.0", items[0].text(0))
        self.assertEqual(items[0].childCount(), 0)

    def test_top_results_with_segment_breakdown(self) -> None:
        scores = [
            LoadoutScore(
                weapon_name="多段剑",
                final_damage=6000.0,
                loadout_names={"chest": "甲", "gloves": "手", "accessory_a": "A", "accessory_b": "B"},
                segment_breakdown={"战技:1": 2000.0, "连携技:1": 4000.0},
            )
        ]
        items = _build_tree_items(
            [], scores,
            damage_metric="加权总伤",
            segment_counts={"战技:1": 1, "连携技:1": 1},
            abnormal_counts=None,
            spell_abnormal_counts=None,
        )
        self.assertEqual(len(items), 1)
        root = items[0]
        self.assertIn("多段剑", root.text(0))
        self.assertIn("6000.0", root.text(0))
        self.assertGreaterEqual(root.childCount(), 2)
        child_texts = [root.child(i).text(0) for i in range(root.childCount())]
        has_segment = any("第1段" in t for t in child_texts)
        self.assertTrue(has_segment)
        has_total = any("加权合计" in t for t in child_texts)
        self.assertTrue(has_total)

    def test_rank_in_header(self) -> None:
        scores = [
            LoadoutScore(weapon_name=f"武器{n}", final_damage=float(n) * 1000, loadout_names={})
            for n in range(1, 4)
        ]
        items = _build_tree_items(
            [], scores,
            damage_metric="伤害",
            segment_counts=None,
            abnormal_counts=None,
            spell_abnormal_counts=None,
        )
        for idx, item in enumerate(items, start=1):
            self.assertIn(f"Top{idx}", item.text(0))

    def test_damage_metric_in_header(self) -> None:
        scores = [
            LoadoutScore(weapon_name="剑", final_damage=5000.0, loadout_names={})
        ]
        items = _build_tree_items(
            [], scores,
            damage_metric="加权总伤",
            segment_counts=None,
            abnormal_counts=None,
            spell_abnormal_counts=None,
        )
        self.assertIn("加权总伤", items[0].text(0))

    def test_empty_loadout_names(self) -> None:
        scores = [LoadoutScore(weapon_name="剑", final_damage=100.0, loadout_names={})]
        items = _build_tree_items(
            [], scores,
            damage_metric="伤害",
            segment_counts=None,
            abnormal_counts=None,
            spell_abnormal_counts=None,
        )
        self.assertIn("剑", items[0].text(0))
        self.assertIn("100.0", items[0].text(0))
