# -*- coding: utf-8 -*-
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

    def test_progress_includes_preprocessed_offset(self):
        calls = []

        run_parallel(
            range(3),
            square,
            max_workers=1,
            progress_callback=calls.append,
            total_candidates=8,
            processed_offset=5,
        )

        assert calls[-1].processed == 8
        assert calls[-1].total == 8
        assert calls[-1].estimated_remaining == 0

    def test_zero_time_budget_stops_before_evaluating(self):
        evaluated = []

        def evaluate(x):
            evaluated.append(x)
            return x

        results = run_parallel(range(5), evaluate, max_workers=1, max_seconds=0)

        assert results == []
        assert evaluated == []

    def test_time_budget_stops_submitting_new_tasks(self):
        import time

        def slow_square(x):
            time.sleep(0.02)
            return x * x

        results = run_parallel(range(100), slow_square, max_workers=1, max_seconds=0.04)

        assert 0 < len(results) < 100

    def test_manual_cancel_during_wait_is_not_reported_as_timeout(self):
        import threading
        import time

        cancel = SearchCancelToken()
        started = threading.Event()

        def blocking_square(x):
            started.set()
            time.sleep(0.08)
            return x * x

        timer = threading.Timer(0.01, cancel.cancel)
        timer.start()
        try:
            run_parallel(
                range(2),
                blocking_square,
                max_workers=1,
                cancel_token=cancel,
                max_seconds=0.03,
            )
        finally:
            timer.cancel()

        assert started.is_set()
        assert cancel.is_cancelled is True
        assert cancel.timed_out is False

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
