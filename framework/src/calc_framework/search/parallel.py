# SPDX-License-Identifier: AGPL-3.0
"""通用并行执行器 — 支持取消、进度回调、Top-N 追踪。"""



from __future__ import annotations

import time
from collections.abc import Callable, Iterable
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from typing import TypeVar

from .cancel import SearchCancelToken
from .result import ParallelProgress
from .tracker import TopNTracker

T = TypeVar("T")

R = TypeVar("R")





def run_parallel(

    tasks: Iterable[T],

    evaluator: Callable[[T], R],

    *,

    max_workers: int = 4,

    cancel_token: SearchCancelToken | None = None,

    progress_callback: Callable[[ParallelProgress], None] | None = None,

    top_n_tracker: TopNTracker[R] | None = None,

    submit_batch_size: int = 100,

    on_result: Callable[[T, R], None] | None = None,

) -> list[R]:

    """并行评估一组任务，支持取消和进度回调。



    Args:

        tasks: 待评估的任务迭代器

        evaluator: 评估函数，接收任务返回结果

        max_workers: 最大并行线程数

        cancel_token: 可选取消令牌

        progress_callback: 进度回调，每完成一批调用一次

        top_n_tracker: 可选 Top-N 追踪器，仅保留最优结果

        submit_batch_size: 每批提交的任务数

        on_result: 可选逐结果回调，接收 (task, result)，用于续跑写入等



    Returns:

        所有结果列表（若提供 top_n_tracker，则仅含其最终结果）

    """

    cancel = cancel_token or SearchCancelToken()

    total = 0

    results: list[R] = []

    processed = 0

    start = time.perf_counter()



    with ThreadPoolExecutor(max_workers=max_workers) as executor:

        task_iter = iter(tasks)

        futures: set[Future[R]] = set()

        _task_map: dict[Future[R], T] = {}



        def _wrap_task(task: T) -> R:

            """_wrap_task。"""
            return evaluator(task)



        def _submit_batch(count: int) -> int:
            """_submit_batch。"""

            submitted = 0

            for _ in range(count):

                if cancel.should_cancel(processed):

                    break

                try:

                    task = next(task_iter)

                except StopIteration:

                    break

                future = executor.submit(_wrap_task, task)

                futures.add(future)

                _task_map[future] = task

                submitted += 1

            return submitted



        _submit_batch(max_workers * 2)



        while futures:

            done, futures = wait(futures, return_when=FIRST_COMPLETED)

            for f in done:

                processed += 1

                task = _task_map.pop(f, None)

                try:

                    result = f.result()

                    if on_result is not None and task is not None:

                        on_result(task, result)

                    results.append(result)

                    if top_n_tracker is not None:

                        top_n_tracker.offer(result)

                except Exception:

                    pass



            if cancel.should_cancel(processed):

                for f in futures:

                    f.cancel()

                futures.clear()

                break



            if progress_callback is not None:

                elapsed = time.perf_counter() - start

                rate = (processed + 1) / max(elapsed, 0.001)

                remaining = (total - processed) / rate if rate > 0 and total > 0 else 0.0

                progress_callback(ParallelProgress(

                    processed=processed,

                    total=total or processed,

                    elapsed=elapsed,

                    estimated_remaining=remaining,

                ))



            to_submit = min(submit_batch_size, max_workers * 4 - len(futures))

            if to_submit > 0 and not cancel.is_cancelled:

                _submit_batch(to_submit)



    if top_n_tracker is not None:

        return list(top_n_tracker.results())

    return results

