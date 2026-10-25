# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""SearchCancelToken 和 SearchResult 单元测试。"""

from __future__ import annotations

from calc_framework.search import SearchCancelToken, SearchResult


class TestSearchCancelToken:
    def test_not_cancelled_by_default(self):
        token = SearchCancelToken()

        assert not token.is_cancelled

        assert not token.should_cancel(0)

    def test_manual_cancel(self):
        token = SearchCancelToken()

        token.cancel()

        assert token.is_cancelled

        assert token.should_cancel(0)

    def test_cancel_after(self):
        token = SearchCancelToken(cancel_after=5)

        assert not token.should_cancel(0)

        assert not token.should_cancel(4)

        assert token.should_cancel(5)

        assert token.should_cancel(100)

    def test_cancel_after_with_manual_cancel(self):
        token = SearchCancelToken(cancel_after=100)

        token.cancel()

        assert token.should_cancel(0)


class TestSearchResult:
    def test_empty(self):
        r = SearchResult()

        assert r.items == ()

        assert r.total_evaluated == 0

        assert r.total_candidates == 0

    def test_with_items(self):
        r = SearchResult(items=(1, 2, 3), total_evaluated=100, total_candidates=1000)

        assert r.items == (1, 2, 3)

        assert r.total_evaluated == 100

        assert r.total_candidates == 1000

    def test_metadata(self):
        r = SearchResult(metadata={"game": "test"})

        assert r.metadata["game"] == "test"
