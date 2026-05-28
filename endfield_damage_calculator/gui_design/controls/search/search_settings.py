#!/usr/bin/env python3
"""全量搜索相关 GUI 参数解析（可单测）。"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class WorkerOption:
    label: str
    worker_count: int


def get_cpu_parallel_info() -> tuple[int, int]:
    cpu_count = os.cpu_count() or 4
    recommended = max(1, cpu_count - 1)
    return cpu_count, recommended


def build_worker_option_labels() -> list[str]:
    import multiprocessing

    cpu_count = multiprocessing.cpu_count()
    options: list[str] = []
    for i in range(1, cpu_count + 1):
        if i == 1:
            options.append(f"1（单线程）")
        elif i == cpu_count:
            options.append(f"{i}（满核）")
        elif i == cpu_count - 1:
            options.append(f"{i}（推荐）")
        else:
            options.append(str(i))
    return options


def resolve_parallel_workers(choice: str) -> int:
    if choice and choice[0].isdigit():
        return int(choice.split("（")[0])
    cpu_count = os.cpu_count() or 4
    return max(1, cpu_count - 1)


def resolve_top_n(choice: str) -> int:
    return int(choice) if choice else 10


def format_parallel_workers_help(choice: str) -> str:
    cpu_count, recommended = get_cpu_parallel_info()
    chosen = resolve_parallel_workers(choice)
    return f"CPU 逻辑核 {cpu_count} 核，推荐 {recommended} 线程，当前 {chosen} 线程"


def format_search_progress_text(
    processed: int,
    total: int,
    current_score: float | None = None,
) -> str:
    pct = (processed / total * 100) if total > 0 else 0.0
    score_part = f" 当前最优: {current_score:.1f}" if current_score is not None else ""
    return f"已评估: {processed}/{total} ({pct:.1f}%){score_part}"
