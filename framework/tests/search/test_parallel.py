# SPDX-License-Identifier: AGPL-3.0
"""run_parallel 集成测试。"""

from __future__ import annotations

from calc_framework.search import SearchCancelToken, TopNTracker, run_parallel


def square(x: int) -> int:
    return x * x


class TestRunParallel:
    def test_all_results_returned(self):
        results = run_parallel(range(10), square, max_workers=2)
        assert set(results) == {0, 1, 4, 9, 16, 25, 36, 49, 64, 81}

    def test_empty_input(self):
        results = run_parallel([], square)
        assert results == []

    def test_cancel_token_stops_early(self):
        cancel = SearchCancelToken(cancel_after=5)
        results = run_parallel(range(100), square, max_workers=4, cancel_token=cancel)
        assert len(results) <= 10

    def test_manual_cancel(self):
        cancel = SearchCancelToken()
        cancel.cancel()
        results = run_parallel(range(100), square, cancel_token=cancel)
        assert results == []

    def test_top_n_tracker(self):
        tracker = TopNTracker(3, key_fn=lambda x: x)
        results = run_parallel(range(100), square, max_workers=4, top_n_tracker=tracker)
        assert len(results) == 3
        assert 9801 in results  # 99^2
        assert 9604 in results  # 98^2
        assert 9409 in results  # 97^2

    def test_progress_callback(self):
        calls = []

        def cb(progress):
            calls.append(progress.processed)

        run_parallel(range(20), square, max_workers=2, progress_callback=cb)
        assert len(calls) > 0
        assert calls[-1] == 20

    def test_single_worker(self):
        results = run_parallel(range(5), square, max_workers=1)
        assert sorted(results) == [0, 1, 4, 9, 16]

    def test_evaluator_exception_skipped(self):
        def broken(x):
            if x == 3:
                raise ValueError("oops")
            return x

        results = run_parallel(range(5), broken, max_workers=1)
        assert 3 not in results
        assert len(results) == 4
