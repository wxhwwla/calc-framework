#!/usr/bin/env python3
"""TopN 追踪器测试。"""

import unittest

from calculation.core.top_n_tracker import TopNTracker
from calculation.loadout.optimizer import LoadoutScore


class TestTopNTracker(unittest.TestCase):
    def test_keeps_only_highest_damage_scores(self):
        tracker = TopNTracker(top_n=2, key_fn=lambda score: score.final_damage)
        for damage in (10.0, 50.0, 30.0, 40.0):
            tracker.offer(
                LoadoutScore(
                    weapon_name="武器",
                    final_damage=damage,
                    loadout_names={"chest": "a"},
                )
            )
        results = tracker.results()
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].final_damage, 50.0)
        self.assertEqual(results[1].final_damage, 40.0)


if __name__ == "__main__":
    unittest.main()
