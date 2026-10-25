# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""SearchEngine 额外路径测试 — 持久化、进度回调、自定义键。"""

from __future__ import annotations

import tempfile
from pathlib import Path

from calc_framework.search import SearchCancelToken, SearchConfig, SearchEngine
from calc_framework.search.persist import SearchRunStore
from calc_framework.search.result import ParallelProgress, SearchResult


class _SquareEngine(SearchEngine[int, int]):
    def __init__(self, numbers: list[int]) -> None:
        self._numbers = numbers

    def generate_candidates(self) -> list[int]:
        return list(self._numbers)

    def evaluate(self, candidate: int) -> int:
        return candidate * candidate

    def score_key(self, result: int) -> float:
        return float(result)


class _CustomKeyEngine(_SquareEngine):
    def __init__(self, numbers: list[int]) -> None:
        super().__init__(numbers)

        self._numbers = numbers

    def candidate_key(self, candidate: int) -> str:
        return f"num_{candidate}"


class TestRunWithPersist:
    def setup_method(self) -> None:
        self._tmpdir = tempfile.mkdtemp()

        self.db_path = Path(self._tmpdir) / "search_runs.db"

    def teardown_method(self) -> None:
        if self.db_path.exists():
            self.db_path.unlink()

        Path(self._tmpdir).rmdir()

    def test_run_with_persist_basic(self):
        engine = _SquareEngine([1, 2, 3, 4, 5])

        store = SearchRunStore(self.db_path)

        result = engine.run(
            SearchConfig(top_n=10, max_workers=2),
            run_store=store,
            run_signature="test-basic",
        )

        assert isinstance(result, SearchResult)

        assert set(result.items) == {1, 4, 9, 16, 25}

        assert result.total_evaluated == 5

        assert result.total_candidates == 5

        assert store.run_status("test-basic") == "completed"

    def test_run_with_persist_skips_processed(self):
        engine = _SquareEngine([1, 2, 3, 4, 5])

        store = SearchRunStore(self.db_path)

        store.ensure_run("test-skip", 5)

        store.mark_processed_batch("test-skip", ["1", "2", "3"])

        result = engine.run(
            SearchConfig(top_n=10, max_workers=2),
            run_store=store,
            run_signature="test-skip",
        )

        assert set(result.items) == {16, 25}

        assert result.total_evaluated == 5

        assert result.metadata.get("skipped_preprocessed") == 3

    def test_run_with_persist_cancel(self):
        engine = _SquareEngine(list(range(100)))

        store = SearchRunStore(self.db_path)

        cancel = SearchCancelToken(cancel_after=5)

        result = engine.run(
            SearchConfig(top_n=50, max_workers=4),
            cancel_token=cancel,
            run_store=store,
            run_signature="test-cancel",
        )

        assert result.total_evaluated <= 10

        assert result.metadata["cancelled"] is True

        assert store.run_status("test-cancel") == "cancelled"

    def test_run_with_persist_flush_remaining_batch(self):
        numbers = list(range(5))

        engine = _SquareEngine(numbers)

        store = SearchRunStore(self.db_path)

        engine.run(
            SearchConfig(top_n=10, max_workers=2),
            run_store=store,
            run_signature="test-flush",
        )

        processed = store.get_processed_keys("test-flush")

        assert len(processed) == 5

        assert store.run_status("test-flush") == "completed"


class TestCandidateKey:
    def test_default_candidate_key(self):
        engine = _SquareEngine([1, 2, 3])

        assert engine.candidate_key(1) == "1"

        assert engine.candidate_key(42) == "42"

    def test_custom_candidate_key(self):
        engine = _CustomKeyEngine([1, 2, 3])

        assert engine.candidate_key(1) == "num_1"

        assert engine.candidate_key(42) == "num_42"

    def test_custom_key_used_for_dedup_in_persist(self):
        engine = _CustomKeyEngine([1, 2, 3])

        store = SearchRunStore(self.db_path)

        store.ensure_run("test-custom-key", 3)

        store.mark_processed_batch("test-custom-key", ["num_1"])

        result = engine.run(
            SearchConfig(top_n=10, max_workers=2),
            run_store=store,
            run_signature="test-custom-key",
        )

        assert result.metadata["skipped_preprocessed"] == 1

    def setup_method(self) -> None:
        self._tmpdir = tempfile.mkdtemp()

        self.db_path = Path(self._tmpdir) / "search_runs.db"

    def teardown_method(self) -> None:
        if self.db_path.exists():
            self.db_path.unlink()

        Path(self._tmpdir).rmdir()


class TestProgressCallback:
    def test_progress_callback_called(self):
        engine = _SquareEngine([1, 2, 3, 4, 5])

        calls: list[ParallelProgress] = []

        def progress(p: ParallelProgress) -> None:
            calls.append(p)

        engine.run(
            SearchConfig(top_n=10, max_workers=2),
            progress_callback=progress,
        )

        assert len(calls) > 0

        assert calls[-1].processed == 5

        assert calls[-1].total == 5

    def test_progress_callback_with_persist(self):
        engine = _SquareEngine([1, 2, 3, 4, 5])

        store = SearchRunStore(Path(tempfile.mkdtemp()) / "progress.db")

        calls: list[ParallelProgress] = []

        def progress(p: ParallelProgress) -> None:
            calls.append(p)

        engine.run(
            SearchConfig(top_n=10, max_workers=2),
            progress_callback=progress,
            run_store=store,
            run_signature="test-progress-persist",
        )

        assert len(calls) > 0

        assert calls[-1].processed == 5

        assert calls[-1].total == 5


class TestRunDefaultPaths:
    def test_run_without_config(self):
        engine = _SquareEngine([1, 2, 3])

        result = engine.run()

        assert len(result.items) == 3

        assert result.total_evaluated == 3

    def test_run_without_cancel_token(self):
        engine = _SquareEngine([1, 2, 3])

        result = engine.run(SearchConfig(top_n=10))

        assert result.metadata["cancelled"] is False

    def test_run_signature_without_store(self):
        engine = _SquareEngine([1, 2, 3])

        result = engine.run(
            SearchConfig(top_n=10),
            run_signature="orphan-sig",
        )

        assert len(result.items) == 3

    def test_empty_candidates(self):
        engine = _SquareEngine([])

        result = engine.run()

        assert result.items == ()

        assert result.total_evaluated == 0

    def test_no_candidates_metadata(self):
        engine = _SquareEngine([])

        result = engine.run(SearchConfig(top_n=10))

        assert "cancelled" in result.metadata
