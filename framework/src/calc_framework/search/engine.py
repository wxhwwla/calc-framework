# SPDX-License-Identifier: AGPL-3.0
"""通用搜索引擎抽象 — SearchEngine ABC + SearchConfig。

用法（游戏适配器）::

    class MyGameSearch(SearchEngine[MyTask, MyScore]):
        def generate_candidates(self) -> list[MyTask]:
            ...
        def evaluate(self, candidate: MyTask) -> MyScore:
            ...
        def score_key(self, result: MyScore) -> float:
            return result.score
        def estimate_workload(self) -> int:
            return len(self.candidates)

    engine = MyGameSearch(...)
    result = engine.run(SearchConfig(top_n=20))
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from calc_framework.search.cancel import SearchCancelToken
from calc_framework.search.parallel import run_parallel
from calc_framework.search.result import SearchResult
from calc_framework.search.tracker import TopNTracker

if TYPE_CHECKING:
    from calc_framework.search.persist import SearchRunStore

C = TypeVar("C")
R = TypeVar("R")


@dataclass
class SearchConfig:
    """通用搜索配置。"""

    top_n: int = 10
    max_workers: int = 4
    max_seconds: float | None = None


class SearchEngine(ABC, Generic[C, R]):
    """游戏无关的搜索引擎基类。

    子类需要实现:
    - ``generate_candidates()`` — 生成所有候选
    - ``evaluate(candidate)`` — 评估单个候选返回评分
    - ``score_key(result)`` — 从评分提取排序键

    基类自动提供:
    - ``run()`` — 并行执行 + Top-N 追踪 + 取消 + 进度回调
    - ``estimate_workload()`` — 估算组合总数
    """

    @abstractmethod
    def generate_candidates(self) -> list[C]:
        ...

    @abstractmethod
    def evaluate(self, candidate: C) -> R:
        ...

    @abstractmethod
    def score_key(self, result: R) -> float:
        ...

    def candidate_key(self, candidate: C) -> str:
        """返回候选的唯一标识键，用于续跑去重。

        子类可覆盖以提供更精确的键（如武器名+装备名组合）。
        默认使用 ``str(candidate)``。
        """
        return str(candidate)

    def estimate_workload(self) -> int:
        return len(self.generate_candidates())

    def run(
        self,
        config: SearchConfig | None = None,
        *,
        cancel_token: SearchCancelToken | None = None,
        progress_callback: Any | None = None,
        run_store: SearchRunStore | None = None,
        run_signature: str | None = None,
    ) -> SearchResult[R]:
        cfg = config or SearchConfig()
        cancel = cancel_token or SearchCancelToken()
        total = self.estimate_workload()

        if run_store is not None and run_signature is not None:
            return self._run_with_persist(cfg, cancel, run_store, run_signature, progress_callback)

        return self._run_in_memory(cfg, cancel, progress_callback, total)

    def _run_in_memory(
        self,
        config: SearchConfig,
        cancel_token: SearchCancelToken,
        progress_callback: Any | None,
        total: int,
    ) -> SearchResult[R]:
        candidates = self.generate_candidates()
        tracker = TopNTracker[R](config.top_n, key_fn=self.score_key)
        evaluated_count = 0

        def _tracked_evaluate(candidate: C) -> R:
            nonlocal evaluated_count
            evaluated_count += 1
            return self.evaluate(candidate)

        def _progress(p):
            if progress_callback is not None:
                progress_callback(p)

        results = run_parallel(
            tasks=candidates,
            evaluator=_tracked_evaluate,
            max_workers=config.max_workers,
            cancel_token=cancel_token,
            progress_callback=_progress,
            top_n_tracker=tracker,
        )

        return SearchResult[R](
            items=tuple(results),
            total_evaluated=evaluated_count,
            total_candidates=total,
            metadata={
                "cancelled": cancel_token.is_cancelled,
                "max_workers": config.max_workers,
            },
        )

    def _run_with_persist(
        self,
        config: SearchConfig,
        cancel_token: SearchCancelToken,
        run_store: SearchRunStore,
        run_signature: str,
        progress_callback: Any | None,
    ) -> SearchResult[R]:
        """执行可续跑搜索：跳过已处理组合，批量写入 processed。"""
        from calc_framework.search.persist import PROCESSED_BATCH_SIZE

        total = self.estimate_workload()
        run_store.ensure_run(run_signature, total)
        existing_keys = run_store.get_processed_keys(run_signature)

        candidates = self.generate_candidates()
        pending = [(self.candidate_key(c), c) for c in candidates if self.candidate_key(c) not in existing_keys]
        skipped = len(candidates) - len(pending)

        tracker = TopNTracker[R](config.top_n, key_fn=self.score_key)
        processed_buf: list[str] = []
        processed_count = 0

        def _on_result(key_and_candidate: tuple[str, C], result: R) -> None:
            nonlocal processed_count
            key, _ = key_and_candidate
            processed_count += 1
            tracker.offer(result)
            processed_buf.append(key)
            if len(processed_buf) >= PROCESSED_BATCH_SIZE:
                run_store.mark_processed_batch(run_signature, processed_buf)
                processed_buf.clear()

        def _progress(p):
            if progress_callback is not None:
                total_with_skipped = processed_count + skipped
                progress_callback(p)

        from calc_framework.search.parallel import run_parallel as _run_parallel

        results = _run_parallel(
            tasks=pending,
            evaluator=lambda kc: self.evaluate(kc[1]),
            max_workers=config.max_workers,
            cancel_token=cancel_token,
            progress_callback=_progress,
            top_n_tracker=tracker,
            on_result=_on_result,
        )

        if processed_buf:
            run_store.mark_processed_batch(run_signature, processed_buf)

        cancelled = cancel_token.is_cancelled
        status = "cancelled" if cancelled else "completed"
        run_store.mark_run_status(run_signature, status)

        return SearchResult[R](
            items=tuple(results),
            total_evaluated=processed_count + skipped,
            total_candidates=total,
            metadata={
                "cancelled": cancelled,
                "skipped_preprocessed": skipped,
                "max_workers": config.max_workers,
            },
        )
