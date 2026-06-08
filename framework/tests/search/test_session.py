# SPDX-License-Identifier: AGPL-3.0
"""搜索会话编排单元测试。"""

from __future__ import annotations

from calc_framework.search.engine import SearchConfig, SearchEngine
from calc_framework.search.persist import SearchRunStore
from calc_framework.search.result import SearchResult
from calc_framework.search.session import SearchSession


class FakeEngine(SearchEngine[str, str]):
    """模拟搜索引擎。"""

    def __init__(self) -> None:
        self.last_config: SearchConfig | None = None

    def generate_candidates(self) -> list[str]:
        return ["candidate_a", "candidate_b"]

    def evaluate(self, candidate: str) -> str:
        return f"result_for_{candidate}"

    def score_key(self, result: str) -> float:
        return 1.0

    def run(
        self,
        config: SearchConfig,
        *,
        cancel_token=None,
        progress_callback=None,
        run_store=None,
        run_signature=None,
    ) -> SearchResult[str]:
        self.last_config = config
        return SearchResult(items=("result_a", "result_b"), total_evaluated=2)


class TestSearchSession:
    def test_construct(self) -> None:
        engine = FakeEngine()
        session = SearchSession(engine)
        assert session.engine is engine
        assert session.store is None

    def test_construct_with_store(self) -> None:
        engine = FakeEngine()
        store = SearchRunStore(":memory:")
        session = SearchSession(engine, store=store)
        assert session.store is store

    def test_engine_property(self) -> None:
        engine = FakeEngine()
        session = SearchSession(engine)
        assert session.engine == engine

    def test_store_property_none(self) -> None:
        session = SearchSession(FakeEngine())
        assert session.store is None

    def test_run_default_config(self) -> None:
        session = SearchSession(FakeEngine())
        result = session.run()
        assert result.total_evaluated == 2
        assert result.items == ("result_a", "result_b")

    def test_run_with_config(self) -> None:
        engine = FakeEngine()
        session = SearchSession(engine)
        config = SearchConfig(top_n=5)
        session.run(config)
        assert engine.last_config is not None
        assert engine.last_config.top_n == 5

    def test_run_with_signature(self) -> None:
        """带 run_signature 时应使用 store。"""
        engine = FakeEngine()
        store = SearchRunStore(":memory:")
        session = SearchSession(engine, store=store)
        result = session.run(run_signature="test-sig-123")
        assert result.total_evaluated == 2

    def test_run_with_cancel_token(self) -> None:
        from calc_framework.search.result import SearchCancelToken

        session = SearchSession(FakeEngine())
        token = SearchCancelToken()
        result = session.run(cancel_token=token)
        assert result is not None
