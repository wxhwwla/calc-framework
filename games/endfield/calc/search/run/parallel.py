#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""有界并行的搜索任务执行（不一次性提交全部 future）。

保留原始增量算法，组件（TopNTracker / SearchCancelToken）来自框架。
支持 ``thread``（默认单线程调试）与 ``process``（多核，绕 GIL）。
新增 ``batch_size`` 参数：将任务分组批量提交，减少 Python↔Rust FFI 调用次数。
"""

from __future__ import annotations

import sys
import time
from collections.abc import Callable, Iterable
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from typing import Any, Literal, TypeVar, cast

from calc_framework.search import SearchCancelToken, TopNTracker
from utils.frozen_runtime import (
    describe_frozen_search_capabilities,
    frozen_allow_multi_workers,
    frozen_use_batch_thread_pool,
    frozen_use_thread_pool,
)

from ..evaluate.process_worker import ProcessWorkerPayload, init_process_worker
from .parallel_loops import _run_inline_loop, _run_parallel_loop, _search_log

T = TypeVar("T")
R = TypeVar("R")

ParallelBackend = Literal["auto", "thread", "process"]


def _pyinstaller_frozen() -> bool:
    """PyInstaller onefile 冻结模式（子进程会重跑 exe，不宜 ProcessPool）。"""
    return bool(getattr(sys, "frozen", False))


def _use_inline_executor(*, batch_mode: bool) -> bool:
    """打包 exe 下是否顺序内联（phase 3–4 默认；phase 5 batch 可走 ThreadPool）。"""
    if not _pyinstaller_frozen():
        return False
    if batch_mode and frozen_use_batch_thread_pool():
        return False
    return not (not batch_mode and frozen_use_thread_pool())


def _resolve_max_workers(max_workers: int) -> int:
    """打包 exe phase<2 时单线程；phase 2/5 尊重 GUI 线程数。"""
    return frozen_allow_multi_workers(max_workers)


def _resolve_parallel_backend(
    *,
    max_workers: int,
    parallel_backend: ParallelBackend,
    process_payload: ProcessWorkerPayload | None,
) -> Literal["thread", "process"]:
    if parallel_backend == "thread":
        return "thread"
    # 打包 exe：ProcessPool 在 Windows spawn 下会反复启动 onefile，易与 Qt/Rust 冲突崩溃
    if _pyinstaller_frozen():
        return "thread"
    if parallel_backend == "process":
        return "process" if process_payload is not None else "thread"
    if max_workers > 1 and process_payload is not None:
        return "process"
    return "thread"


def _make_batch_iter(
    work_iter: Iterable[T],
    batch_size: int,
) -> Iterable[list[T]]:
    """将任务流分组为 batch。"""
    buf: list[T] = []
    for item in work_iter:
        buf.append(item)
        if len(buf) >= batch_size:
            yield buf
            buf = []
    if buf:
        yield buf


def run_bounded_parallel(
    *,
    work_items: Iterable[T],
    total: int,
    evaluate: Callable[[T], R],
    max_workers: int,
    cancel_token: SearchCancelToken | None = None,
    progress_callback: Callable[[dict], None] | None = None,
    on_result: Callable[[T, R], None] | None = None,
    top_n: int | None = None,
    top_key: Callable[[R], float] = lambda score: float(score),  # type: ignore[arg-type]
    parallel_backend: ParallelBackend = "auto",
    process_payload: ProcessWorkerPayload | None = None,
    process_evaluate: Callable[[T], R] | None = None,
    batch_size: int = 1,
    batch_evaluate: Callable[[list[T]], list[R]] | None = None,
) -> tuple[tuple[R, ...], int, bool]:
    """流式提交任务，限制在途 future 数量。

    若提供 ``batch_size > 1`` 和 ``batch_evaluate``，则每 batch_size 个任务
    打包为一次提交，减少 Python↔Rust FFI 开销。

    其余参数含义不变。
    """
    token = cancel_token or SearchCancelToken()
    workers = _resolve_max_workers(max_workers)
    backend = _resolve_parallel_backend(
        max_workers=workers,
        parallel_backend=parallel_backend,
        process_payload=process_payload,
    )
    if backend == "process":
        if process_payload is None or process_evaluate is None:
            backend = "thread"
        else:
            evaluate = process_evaluate
    batch_mode = batch_size > 1 and batch_evaluate is not None
    use_inline_single = _use_inline_executor(batch_mode=False)
    use_inline_batch = _use_inline_executor(batch_mode=True)
    executor_label = "inline"
    if _pyinstaller_frozen():
        if batch_mode and not use_inline_batch:
            executor_label = "BatchThreadPool"
        elif not batch_mode and not use_inline_single:
            executor_label = "ThreadPool"
        else:
            executor_label = "inline"
    elif backend == "process":
        executor_label = "ProcessPool"
    elif batch_mode or workers > 1:
        executor_label = "ThreadPool"
    _search_log().info(
        "run_bounded_parallel | total=%s workers=%s (req=%s) backend=%s batch_size=%s "
        "batch_eval=%s frozen=%s caps=%s executor=%s batch_pool=%s",
        total,
        workers,
        max(1, int(max_workers)),
        backend,
        batch_size,
        batch_evaluate is not None,
        _pyinstaller_frozen(),
        describe_frozen_search_capabilities(),
        executor_label,
        batch_mode and not use_inline_batch,
    )
    max_inflight = max(workers * 4, 8)
    tracker: TopNTracker[R] | None = None
    all_results: list[R] | None = None
    if top_n is not None:
        tracker = TopNTracker(top_n, key_fn=top_key)
    else:
        all_results = []

    processed = 0
    cancelled = False
    started_at = time.perf_counter()

    def _report_progress(*, inline: bool) -> None:
        p = processed
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
                "inline" if inline else "pool",
            )

    # ── 批量化处理 ──
    if batch_mode:
        batched_items = _make_batch_iter(work_items, batch_size)

        def _on_batch_result(batch: list[T], batch_results: list[R]) -> None:
            nonlocal processed
            for item, result in zip(batch, batch_results):
                if on_result is not None:
                    on_result(item, result)
                if tracker is not None:
                    tracker.offer(result)
                elif on_result is None and all_results is not None:
                    all_results.append(result)
                processed += 1

        assert batch_evaluate is not None
        if backend == "process" and process_payload is not None:
            from ..evaluate.process_worker import evaluate_optimizer_batch_keyed_in_process

            _batch_executor_cls: type[ProcessPoolExecutor] | type[ThreadPoolExecutor] = ProcessPoolExecutor
            _batch_executor_kwargs: dict = {
                "max_workers": workers,
                "initializer": init_process_worker,
                "initargs": (process_payload,),
            }
            _batch_eval_fn: Callable[[Any], Any] = evaluate_optimizer_batch_keyed_in_process
        else:
            _batch_executor_cls = ThreadPoolExecutor
            _batch_executor_kwargs = {"max_workers": workers}
            _batch_eval_fn = cast(Callable[[Any], Any], batch_evaluate)

        if use_inline_batch:
            _run_inline_loop(
                work_iter=batched_items,
                evaluate=_batch_eval_fn,
                on_result=_on_batch_result,
                get_processed=lambda: processed,
                cancel_token=token,
                report_progress=lambda: _report_progress(inline=True),
            )
        else:
            _run_parallel_loop(
                work_iter=batched_items,
                total=total,
                evaluate=_batch_eval_fn,
                on_result=_on_batch_result,
                max_inflight=max_inflight,
                executor_cls=_batch_executor_cls,
                executor_kwargs=_batch_executor_kwargs,
                get_processed=lambda: processed,
                cancel_token=token,
                progress_callback=progress_callback,
                started_at=started_at,
            )
        cancelled = token.should_cancel(processed)
    else:
        work_iter = iter(work_items)
        executor_cls: type[ThreadPoolExecutor] | type[ProcessPoolExecutor]
        executor_kwargs: dict
        if backend == "process":
            executor_cls = ProcessPoolExecutor
            executor_kwargs = {
                "max_workers": workers,
                "initializer": init_process_worker,
                "initargs": (process_payload,),
            }
        else:
            executor_cls = ThreadPoolExecutor
            executor_kwargs = {"max_workers": workers}

        def _on_single_result(item: T, result: R) -> None:
            nonlocal processed
            if on_result is not None:
                on_result(item, result)
            if tracker is not None:
                tracker.offer(result)
            elif on_result is None and all_results is not None:
                all_results.append(result)
            processed += 1

        if use_inline_single:
            _run_inline_loop(
                work_iter=work_iter,
                evaluate=evaluate,
                on_result=_on_single_result,
                get_processed=lambda: processed,
                cancel_token=token,
                report_progress=lambda: _report_progress(inline=True),
            )
        else:
            _run_parallel_loop(
                work_iter=work_iter,
                total=total,
                evaluate=evaluate,
                on_result=_on_single_result,
                max_inflight=max_inflight,
                executor_cls=executor_cls,
                executor_kwargs=executor_kwargs,
                get_processed=lambda: processed,
                cancel_token=token,
                progress_callback=progress_callback,
                started_at=started_at,
            )
        cancelled = token.should_cancel(processed)

    if tracker is not None:
        return tracker.results(), processed, cancelled
    assert all_results is not None
    return tuple(all_results), processed, cancelled
