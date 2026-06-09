# SPDX-License-Identifier: AGPL-3.0
"""搜索结果类型单元测试。"""

from __future__ import annotations

from calc_framework.search.result import (
    ParallelProgress,
    SearchCancelToken,
    SearchResult,
)


class TestSearchResult:
    def test_default_values(self) -> None:
        r = SearchResult()
        assert r.items == ()
        assert r.total_evaluated == 0
        assert r.total_candidates == 0
        assert r.elapsed_seconds == 0.0

    def test_with_items(self) -> None:
        r = SearchResult(items=("a", "b"), total_evaluated=10)
        assert r.items == ("a", "b")
        assert r.total_evaluated == 10

    def test_metadata(self) -> None:
        r = SearchResult(metadata={"game": "endfield"})
        assert r.metadata["game"] == "endfield"


class TestParallelProgress:
    def test_default_values(self) -> None:
        p = ParallelProgress()
        assert p.processed == 0
        assert p.total == 0
        assert p.elapsed == 0.0

    def test_progress_ratio(self) -> None:
        p = ParallelProgress(processed=30, total=100)
        assert p.processed / p.total == 0.3


class TestSearchCancelToken:
    def test_not_cancelled_by_default(self) -> None:
        t = SearchCancelToken()
        assert not t.should_cancel(0)
        assert not t.is_cancelled

    def test_cancel(self) -> None:
        t = SearchCancelToken()
        t.cancel()
        assert t.is_cancelled
        assert t.should_cancel(0)

    def test_under_limit(self) -> None:
        t = SearchCancelToken(cancel_after=5)
        assert not t.should_cancel(3)  # 3 < 5, not cancelled yet
        assert not t.is_cancelled

    def test_hits_limit(self) -> None:
        t = SearchCancelToken(cancel_after=5)
        assert t.should_cancel(10)  # 10 >= 5, auto-cancels

    def test_cancelled_persists(self) -> None:
        t = SearchCancelToken(cancel_after=5)
        t.should_cancel(10)  # triggers cancel
        assert t.should_cancel(0)  # still cancelled
