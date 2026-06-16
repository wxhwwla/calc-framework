#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""有界并行的搜索任务执行（不一次性提交全部 future）。

保留原始增量算法，组件（TopNTracker / SearchCancelToken）来自框架。
支持 ``thread``（默认单线程调试）与 ``process``（多核，绕 GIL）。
新增 ``batch_size`` 参数：将任务分组批量提交，减少 Python↔Rust FFI 调用次数。
"""

from __future__ import annotations

import time
from collections.abc import Callable, Iterable
from concurrent.futures import FIRST_COMPLETED, Future, ProcessPoolExecutor, ThreadPoolExecutor, wait
from typing import Any, Literal, TypeVar

from calc_framework.search import SearchCancelToken, TopNTracker

from ..evaluate.process_worker import ProcessWorkerPayload, init_process_worker

T = TypeVar("T")
R = TypeVar("R")

ParallelBackend = Literal["auto", "thread", "process"]


def _resolve_parallel_backend(
    *,
    max_workers: int,
    parallel_backend: ParallelBackend,
    process_payload: ProcessWorkerPayload | None,
) -> Literal["thread", "process"]:
    if parallel_backend == "thread":
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
    workers = max(1, int(max_workers))
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

    # ── 批量化处理 ──
    if batch_size > 1 and batch_evaluate is not None:
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

        # 决定批量用 thread 还是 process
        if process_payload is not None:
            from ..evaluate.process_worker import evaluate_optimizer_batch_in_process

            _batch_executor_cls: type[ProcessPoolExecutor] | type[ThreadPoolExecutor] = ProcessPoolExecutor
            _batch_executor_kwargs: dict = {
                "max_workers": workers,
                "initializer": init_process_worker,
                "initargs": (process_payload,),
            }
            _batch_eval_fn = evaluate_optimizer_batch_in_process
        else:
            _batch_executor_cls = ThreadPoolExecutor
            _batch_executor_kwargs = {"max_workers": workers}
            _batch_eval_fn = batch_evaluate

        _run_parallel_loop(
            work_iter=batched_items,
            total=total,
            evaluate=_batch_eval_fn,  # type: ignore[arg-type]
            on_result=_on_batch_result,
            max_inflight=max_inflight,
            executor_cls=_batch_executor_cls,
            executor_kwargs=_batch_executor_kwargs,
            token=token,
            progress_callback=progress_callback,
            all_results=all_results,
            tracker=tracker,
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

        _run_parallel_loop(
            work_iter=work_iter,
            total=total,
            evaluate=evaluate,
            on_result=_on_single_result,
            max_inflight=max_inflight,
            executor_cls=executor_cls,
            executor_kwargs=executor_kwargs,
            token=token,
            progress_callback=progress_callback,
            all_results=all_results,
            tracker=tracker,
            started_at=started_at,
        )
        cancelled = token.should_cancel(processed)

    if tracker is not None:
        return tracker.results(), processed, cancelled
    assert all_results is not None
    return tuple(all_results), processed, cancelled


def _run_parallel_loop(
    *,
    work_iter: Iterable[Any],
    total: int,
    evaluate: Callable[[Any], Any],
    on_result: Callable[[Any, Any], None],
    max_inflight: int,
    executor_cls: type,
    executor_kwargs: dict,
    token: SearchCancelToken,
    progress_callback: Callable[[dict], None] | None,
    all_results: list | None,
    tracker: TopNTracker | None,
    started_at: float,
) -> None:
    """内部循环：提交 → 等待完成 → 处理结果。"""
    processed = 0
    with executor_cls(**executor_kwargs) as executor:
        pending: dict[Future[Any], Any] = {}

        def _submit_until_full() -> None:
            for item in work_iter:
                pending[executor.submit(evaluate, item)] = item
                if len(pending) >= max_inflight:
                    return

        _submit_until_full()
        while pending:
            if token.should_cancel(processed):
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
                    _submit_until_full()
                    continue

                on_result(item, result)

                elapsed = max(1e-6, time.perf_counter() - started_at)
                speed = processed / elapsed
                remain = max(0, int(total) - processed)
                eta = remain / speed if speed > 0 else 0.0
                if progress_callback:
                    progress_callback(
                        {
                            "processed": processed,
                            "total": int(total),
                            "speed_per_sec": speed,
                            "eta_seconds": eta,
                        }
                    )
                if token.should_cancel(processed):
                    for pending_future in list(pending.keys()):
                        pending_future.cancel()
                    pending.clear()
                    break
                _submit_until_full()
