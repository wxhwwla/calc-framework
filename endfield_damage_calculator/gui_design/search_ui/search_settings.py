#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全量搜索相关 GUI 参数解析（可单测）。"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class CpuParallelInfo:
    """本机并行能力摘要（供 GUI 展示）。"""

    logical_cores: int
    recommended_workers: int
    max_workers: int


def get_cpu_parallel_info(*, cpu_count: int | None = None) -> CpuParallelInfo:
    """读取本机逻辑核数、推荐线程与硬上限。"""
    cores = max(1, int(cpu_count if cpu_count is not None else (os.cpu_count() or 1)))
    recommended = max(1, cores - 1)
    return CpuParallelInfo(
        logical_cores=cores,
        recommended_workers=recommended,
        max_workers=cores,
    )


def default_parallel_workers(*, cpu_count: int | None = None) -> int:
    """默认并行线程数：保留 1 核给系统。"""
    return get_cpu_parallel_info(cpu_count=cpu_count).recommended_workers


def build_worker_option_labels(*, cpu_count: int | None = None) -> list[str]:
    """生成并行线程下拉选项（不超过本机逻辑核数）。"""
    info = get_cpu_parallel_info(cpu_count=cpu_count)
    labels = [f"自动 ({info.recommended_workers} 线程)"]
    for n in (1, 2, 4, 8, 16, 32):
        if 1 <= n <= info.max_workers and str(n) not in labels:
            labels.append(str(n))
    if str(info.max_workers) not in labels and info.max_workers not in (1, 2, 4, 8, 16, 32):
        labels.append(str(info.max_workers))
    return labels


def resolve_parallel_workers(choice: str, *, cpu_count: int | None = None) -> int:
    """将下拉选项解析为线程数（超过本机逻辑核数时自动压低）。"""
    info = get_cpu_parallel_info(cpu_count=cpu_count)
    text = (choice or "").strip()
    if text.startswith("自动"):
        return info.recommended_workers
    try:
        workers = int(text)
    except ValueError:
        return info.recommended_workers
    return max(1, min(workers, info.max_workers))


def format_parallel_workers_help(
    info: CpuParallelInfo,
    *,
    selected_workers: int,
) -> str:
    """生成并行线程说明文案。"""
    return (
        f"本机逻辑处理器：{info.logical_cores} 核；"
        f"当前将使用 {selected_workers} 线程（硬上限 {info.max_workers}）。\n"
        f"「自动」= {info.recommended_workers} 线程（预留 1 核给系统/UI）。\n"
        f"超过上限会自动压低；一般不会死机，但线程过多时电脑可能明显变卡。"
    )


def resolve_top_n(choice: str, *, default: int = 10) -> int:
    """将 TopN 下拉选项解析为整数。"""
    try:
        return max(1, int((choice or "").strip()))
    except ValueError:
        return default


def format_duration_human(seconds: float) -> str:
    """将秒数格式化为中文可读时长（re-export）。"""
    from utils.search_format import format_duration_human as _fmt

    return _fmt(seconds)


def format_workload_estimate_line(*, workload, duration) -> str:
    """生成 GUI 预估文案（re-export）。"""
    from utils.search_format import format_workload_estimate_line as _fmt

    return _fmt(workload=workload, duration=duration)


def format_search_progress_text(
    *,
    prefix: str,
    processed: int,
    total: int,
    eta_seconds: float,
    estimated_total_seconds: float | None = None,
) -> str:
    """格式化状态栏进度文案。"""
    if total <= 0:
        return f"{prefix}：准备中…"
    if eta_seconds > 0:
        remain_text = format_duration_human(eta_seconds)
        if estimated_total_seconds and estimated_total_seconds > 0:
            total_text = format_duration_human(estimated_total_seconds)
            return (
                f"{prefix}：{processed}/{total}\n"
                f"剩余 {remain_text}，总预计 {total_text}"
            )
        return f"{prefix}：{processed}/{total}\n剩余 {remain_text}"
    return f"{prefix}：{processed}/{total}"
