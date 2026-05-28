"""TopNTracker 单元测试。"""

from __future__ import annotations

import pytest

from calc_framework.search import TopNTracker


class TestTopNTracker:
    def test_offer_and_results(self):
        tracker = TopNTracker(3, key_fn=lambda x: x)
        for v in (10, 20, 5, 30, 15):
            tracker.offer(v)
        assert tracker.results() == (30, 20, 15)

    def test_less_items_than_top_n(self):
        tracker = TopNTracker(10, key_fn=lambda x: x)
        for v in (3, 1, 2):
            tracker.offer(v)
        assert tracker.results() == (3, 2, 1)

    def test_empty_tracker(self):
        tracker = TopNTracker(5, key_fn=lambda x: x)
        assert tracker.results() == ()

    def test_top_n_at_least_1(self):
        tracker = TopNTracker(0, key_fn=lambda x: x)
        assert tracker.top_n == 1

    def test_duplicate_scores(self):
        tracker = TopNTracker(3, key_fn=lambda x: x)
        for v in (5, 5, 5, 5, 5):
            tracker.offer(v)
        assert len(tracker.results()) == 3

    def test_custom_key_fn(self):
        data = [("a", 30), ("b", 10), ("c", 20)]
        tracker = TopNTracker(2, key_fn=lambda x: x[1])
        for item in data:
            tracker.offer(item)
        assert tracker.results() == (("a", 30), ("c", 20))

    def test_float_scores(self):
        tracker = TopNTracker(3, key_fn=lambda x: x)
        for v in (1.5, 2.7, 0.8, 3.1):
            tracker.offer(v)
        assert tracker.results() == (3.1, 2.7, 1.5)

    def test_count_property(self):
        tracker = TopNTracker(5, key_fn=lambda x: x)
        assert tracker.count == 0
        tracker.offer(1)
        tracker.offer(2)
        assert tracker.count == 2
