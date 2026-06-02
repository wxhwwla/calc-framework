# SPDX-License-Identifier: AGPL-3.0
"""通用搜索/枚举引擎子包。

提供游戏无关的搜索基础设施：抽象搜索引擎、Top-N 追踪、取消令牌、并行执行器、基础结果类型。

用法::

    from calc_framework.search import (
        SearchConfig, SearchEngine, SearchResult,
        TopNTracker, SearchCancelToken, run_parallel,
    )

    class MySearch(SearchEngine[MyTask, MyScore]):
        ...

    result = MySearch().run(SearchConfig(top_n=20))
"""

from calc_framework.search.engine import SearchConfig, SearchEngine
from calc_framework.search.parallel import ParallelProgress, run_parallel
from calc_framework.search.persist import SearchRunStore
from calc_framework.search.result import SearchCancelToken, SearchResult
from calc_framework.search.session import SearchSession
from calc_framework.search.tracker import TopNTracker

__all__ = [
    "ParallelProgress",
    "SearchCancelToken",
    "SearchConfig",
    "SearchEngine",
    "SearchResult",
    "SearchRunStore",
    "SearchSession",
    "TopNTracker",
    "run_parallel",
]
