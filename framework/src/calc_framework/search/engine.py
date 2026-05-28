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

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from calc_framework.search.cancel import SearchCancelToken
from calc_framework.search.parallel import run_parallel
from calc_framework.search.result import SearchResult
from calc_framework.search.tracker import TopNTracker

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

    def estimate_workload(self) -> int:
        return len(self.generate_candidates())

    def run(
        self,
        config: SearchConfig | None = None,
        *,
        cancel_token: SearchCancelToken | None = None,
        progress_callback: Any | None = None,
        db_path: str | None = None,
        run_signature: str | None = None,
    ) -> SearchResult[R]:
        cfg = config or SearchConfig()
        cancel = cancel_token or SearchCancelToken()
        candidates = self.generate_candidates()
        total = len(candidates)

        tracker = TopNTracker[R](cfg.top_n, key_fn=self.score_key)

        def _progress(p):
            if progress_callback is not None:
                progress_callback(p)

        results = run_parallel(
            tasks=candidates,
            evaluator=self.evaluate,
            max_workers=cfg.max_workers,
            cancel_token=cancel,
            progress_callback=_progress,
            top_n_tracker=tracker,
        )

        return SearchResult[R](
            items=tuple(results),
            total_evaluated=len(results),
            total_candidates=total,
            metadata={
                "cancelled": cancel.is_cancelled,
                "max_workers": cfg.max_workers,
            },
        )
