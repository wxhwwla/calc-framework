#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""有界并行搜索的内层执行循环（P2-07 从 ``parallel.py`` 拆出）。

- ``_run_inline_loop``：打包 exe 专用，在调用线程内顺序评估。
- ``_run_parallel_loop``：提交 → 等待完成 → 处理 future 的流式循环。
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Iterable
from concurrent.futures import FIRST_COMPLETED, Future, wait
from typing import Any

from calc_framework.search import SearchCancelToken
from utils.search_diagnostics import get_search_logger, summarize_work_item


def _search_log() -> logging.Logger:
    return get_search_logger()


def _run_inline_loop(
    *,
    work_iter: Iterable[Any],
    evaluate: Callable[[Any], Any],
    on_result: Callable[[Any, Any], None],
    get_processed: Callable[[], int],
    cancel_token: SearchCancelToken,
    report_progress: Callable[[], None],
) -> None:
    """打包 exe 专用：在调用线程内顺序评估，避免 ThreadPool + Qt/Rust 跨线程崩溃。"""
    heartbeat = 0
    for item in work_iter:
        if cancel_token.should_cancel(get_processed()):
            break
        try:
            result = evaluate(item)
        except Exception:
            _search_log().exception(
                "内联评估失败 item=%s",
                summarize_work_item(item),
            )
            continue
        on_result(item, result)
        heartbeat += 1
        report_progress()
        if heartbeat % 1000 == 0:
            _search_log().info("内联心跳 processed=%s", get_processed())
        if cancel_token.should_cancel(get_processed()):
            break


def _run_parallel_loop(
    *,
    work_iter: Iterable[Any],
    evaluate: Callable[[Any], Any],
    on_result: Callable[[Any, Any], None],
    max_inflight: int,
    executor_cls: type,
    executor_kwargs: dict,
    get_processed: Callable[[], int],
    cancel_token: SearchCancelToken,
    progress_callback: Callable[[dict], None] | None,
    total: int,
    started_at: float,
) -> None:
    """内部循环：提交 → 等待完成 → 处理结果。

    ``on_result`` 负责递增计数和更新 tracker；``get_processed`` 返回当前已处理数，
    供本函数做取消检查和进度回调。``cancel_token`` 由调用方提供，本函数只读取。
    """
    with executor_cls(**executor_kwargs) as executor:
        pending: dict[Future[Any], Any] = {}

        def _submit_until_full() -> None:
            for item in work_iter:
                pending[executor.submit(evaluate, item)] = item
                if len(pending) >= max_inflight:
                    return

        _submit_until_full()
        while pending:
            if cancel_token.should_cancel(get_processed()):
                for future in pending:
                    future.cancel()
                pending.clear()
                break

            done, _ = wait(pending.keys(), return_when=FIRST_COMPLETED)
            for future in done:
                item = pending.pop(future)
                try:
                    result = future.result()
                except Exception:
                    _search_log().exception(
                        "并行评估失败 item=%s",
                        summarize_work_item(item),
                    )
                    _submit_until_full()
                    continue

                on_result(item, result)
                p = get_processed()

                elapsed = max(1e-6, time.perf_counter() - started_at)
                speed = p / elapsed
                remain = max(0, int(total) - p)
                eta = remain / speed if speed > 0 else 0.0
                if progress_callback:
                    progress_callback(
                        {
                            "processed": p,
                            "total": int(total),
                            "speed_per_sec": speed,
                            "eta_seconds": eta,
                        }
                    )
                if p > 0 and (p % 5000 == 0 or p == int(total)):
                    _search_log().info(
                        "并行进度 processed=%s/%s speed=%.1f/s backend_loop=%s",
                        p,
                        total,
                        speed,
                        executor_cls.__name__,
                    )
                if cancel_token.should_cancel(p):
                    for pending_future in list(pending.keys()):
                        pending_future.cancel()
                    pending.clear()
                    break
                _submit_until_full()
