# SPDX-License-Identifier: AGPL-3.0
"""SearchEngine + SearchConfig 测试。"""

from __future__ import annotations

from calc_framework.search import SearchCancelToken, SearchConfig, SearchEngine
from calc_framework.search.result import SearchResult


class _SquareEngine(SearchEngine[int, int]):
    """测试用搜索引擎：对数字求平方、按平方值排序。"""

    def __init__(self, numbers: list[int]) -> None:
        self._numbers = numbers

    def generate_candidates(self) -> list[int]:
        return list(self._numbers)

    def evaluate(self, candidate: int) -> int:
        return candidate * candidate

    def score_key(self, result: int) -> float:
        return float(result)


class TestSearchEngine:
    def test_run_returns_all_results(self):
        engine = _SquareEngine([1, 2, 3, 4, 5])
        result = engine.run(SearchConfig(top_n=10, max_workers=2))
        assert isinstance(result, SearchResult)
        assert set(result.items) == {1, 4, 9, 16, 25}
        assert result.total_evaluated == 5
        assert result.total_candidates == 5

    def test_top_n_limits_results(self):
        engine = _SquareEngine([1, 2, 3, 4, 5])
        result = engine.run(SearchConfig(top_n=2, max_workers=2))
        assert len(result.items) == 2
        assert 25 in result.items
        assert 16 in result.items

    def test_empty_candidates(self):
        engine = _SquareEngine([])
        result = engine.run(SearchConfig())
        assert result.items == ()
        assert result.total_evaluated == 0

    def test_cancel_token_stops_early(self):
        engine = _SquareEngine(list(range(100)))
        cancel = SearchCancelToken(cancel_after=5)
        result = engine.run(SearchConfig(top_n=50, max_workers=4), cancel_token=cancel)
        assert result.total_evaluated <= 10

    def test_estimate_workload(self):
        engine = _SquareEngine([1, 2, 3])
        assert engine.estimate_workload() == 3

    def test_cancel_before_run(self):
        engine = _SquareEngine(list(range(100)))
        cancel = SearchCancelToken()
        cancel.cancel()
        result = engine.run(SearchConfig(top_n=10), cancel_token=cancel)
        assert result.total_evaluated == 0
