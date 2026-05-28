"""通用搜索/枚举引擎子包。

提供游戏无关的搜索基础设施：Top-N 追踪、取消令牌、并行执行器、基础结果类型。

用法::

    from calc_framework.search import TopNTracker, SearchCancelToken, run_parallel

    tracker = TopNTracker(10, key_fn=lambda r: r.score)
    cancel = SearchCancelToken(cancel_after=5000)
    results = run_parallel(tasks, evaluator, max_workers=4, cancel_token=cancel,
                           progress_callback=my_cb, top_n_tracker=tracker)
"""

from calc_framework.search.cancel import SearchCancelToken
from calc_framework.search.parallel import ParallelProgress, run_parallel
from calc_framework.search.result import SearchResult
from calc_framework.search.tracker import TopNTracker

__all__ = [
    "ParallelProgress",
    "SearchCancelToken",
    "SearchResult",
    "TopNTracker",
    "run_parallel",
]
