# SPDX-License-Identifier: AGPL-3.0
"""搜索会话编排 — SearchSession。



将 ``SearchEngine`` 与可选的 ``SearchRunStore`` 串联为端到端流程：

候选生成 → 续跑去重 → 并行评估 → 进度回调 → 结果持久化。



用法::



    from . import SearchConfig, SearchSession

    from .persist import SearchRunStore



    session = SearchSession(engine, store=SearchRunStore("runs.db"))

    result = session.run(SearchConfig(top_n=10), run_signature="abc123")

"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from .engine import SearchConfig, SearchEngine
from .persist import SearchRunStore
from .result import SearchCancelToken, SearchResult

C = TypeVar("C")

R = TypeVar("R")


class SearchSession(Generic[C, R]):
    """搜索会话编排。



    :param engine: 实现了 SearchEngine 接口的搜索引擎

    :param store: 可选 SQLite 持久化存储，提供续跑去重能力

    """

    def __init__(
        self,
        engine: SearchEngine[C, R],
        store: SearchRunStore | None = None,
    ) -> None:
        self._engine = engine

        self._store = store

    @property
    def engine(self) -> SearchEngine[C, R]:
        """engine。"""
        return self._engine

    @property
    def store(self) -> SearchRunStore | None:
        """store。"""

        return self._store

    def run(
        self,
        config: SearchConfig | None = None,
        *,
        cancel_token: SearchCancelToken | None = None,
        progress_callback: Any | None = None,
        run_signature: str | None = None,
    ) -> SearchResult[R]:
        """执行搜索会话。



        :param config: 搜索配置（top_n、max_workers 等）

        :param cancel_token: 取消令牌

        :param progress_callback: 进度回调，接收 ``dict``（兼容旧接口）

        :param run_signature: 运行签名，提供时启用续跑去重

        """

        cfg = config or SearchConfig()

        cancel = cancel_token or SearchCancelToken()

        run_store = self._store if run_signature is not None else None

        return self._engine.run(
            cfg,
            cancel_token=cancel,
            progress_callback=progress_callback,
            run_store=run_store,
            run_signature=run_signature,
        )
