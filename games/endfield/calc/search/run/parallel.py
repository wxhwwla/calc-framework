#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""有界并行的搜索任务执行（不一次性提交全部 future）。



保留原始增量算法，组件（TopNTracker / SearchCancelToken）来自框架。

"""



from __future__ import annotations

import time
from collections.abc import Callable, Iterable
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from typing import TypeVar

from calc_framework.search import SearchCancelToken, TopNTracker

T = TypeVar("T")

R = TypeVar("R")





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

) -> tuple[tuple[R, ...], int, bool]:

    """

    流式提交任务，限制在途 future 数量（避免千万级组合时一次性 submit 占满内存）。



    若提供 top_n，则只保留得分最高的 top_n 条结果（适用于 LoadoutScore 等）。

    """

    token = cancel_token or SearchCancelToken()

    workers = max(1, int(max_workers))

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

    work_iter = iter(work_items)



    with ThreadPoolExecutor(max_workers=workers) as executor:

        pending: dict[Future[R], T] = {}



        def _submit_until_full() -> None:

            while len(pending) < max_inflight:

                try:

                    item = next(work_iter)

                except StopIteration:

                    return

                pending[executor.submit(evaluate, item)] = item
            """submit until full。"""



        _submit_until_full()

        while pending:

            if token.should_cancel(processed):

                cancelled = True

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



                if on_result is not None:

                    on_result(item, result)

                if tracker is not None:

                    tracker.offer(result)

                elif on_result is None and all_results is not None:

                    all_results.append(result)



                processed += 1

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

                    cancelled = True

                    for pending_future in list(pending.keys()):

                        pending_future.cancel()

                    pending.clear()

                    break

                _submit_until_full()

            if cancelled:

                break



    if tracker is not None:

        return tracker.results(), processed, cancelled

    assert all_results is not None

    return tuple(all_results), processed, cancelled

