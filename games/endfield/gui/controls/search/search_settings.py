#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""全量搜索相关 GUI 参数解析（可单测）。"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass

from calc_framework.ui.i18n import tr
from utils.frozen_runtime import frozen_allow_multi_workers, search_recommended_workers


@dataclass(frozen=True)
class CpuParallelInfo:
    """本机并行能力摘要（供 GUI 展示）。

    ``logical_processors`` 来自 ``os.cpu_count()``（Windows 上通常为逻辑线程数，含超线程）。
    ``physical_cores`` 在 Windows 上通过 kernel32 统计；失败时与逻辑数相同。
    并行 worker 上限与「自动」推荐均基于 **逻辑处理器**（与 ThreadPool 语义一致）。
    """

    logical_processors: int
    physical_cores: int
    recommended_workers: int
    max_workers: int

    @property
    def logical_cores(self) -> int:
        """兼容旧字段名。"""
        return self.logical_processors


_physical_cores_cache: int | None = None


def _detect_physical_cores(*, logical: int) -> int:
    """尽力检测物理核心数（仅展示；worker 上限仍用逻辑处理器）。"""
    global _physical_cores_cache
    if _physical_cores_cache is not None:
        return _physical_cores_cache
    override = os.environ.get("CALC_PHYSICAL_CORES", "").strip()
    if override.isdigit() and int(override) > 0:
        _physical_cores_cache = int(override)
        return _physical_cores_cache
    physical = logical
    if sys.platform == "win32":
        try:
            from utils.platform_win32_patch import get_physical_processor_count

            detected = get_physical_processor_count(logical_fallback=logical)
            if detected > 0:
                physical = detected
        except (ImportError, OSError, ValueError):
            pass
    _physical_cores_cache = min(physical, logical)
    return _physical_cores_cache


def get_cpu_parallel_info(*, cpu_count: int | None = None) -> CpuParallelInfo:
    """读取本机逻辑线程数、物理核心（尽力）、推荐 worker 与硬上限。"""
    logical = max(1, int(cpu_count if cpu_count is not None else (os.cpu_count() or 1)))
    physical = _detect_physical_cores(logical=logical)
    recommended = search_recommended_workers(logical)
    return CpuParallelInfo(
        logical_processors=logical,
        physical_cores=physical,
        recommended_workers=recommended,
        max_workers=logical,
    )


def default_parallel_workers(*, cpu_count: int | None = None) -> int:
    """默认并行线程数：保留 1 核给系统。"""
    return get_cpu_parallel_info(cpu_count=cpu_count).recommended_workers


def _is_auto_workers_choice(text: str) -> bool:
    """识别「自动」worker 选项（兼容中/英显示文案与旧测试字面量）。"""
    t = (text or "").strip()
    if not t:
        return False
    if t.startswith("自动"):
        return True
    lower = t.lower()
    return lower == "auto" or lower.startswith("auto ") or lower.startswith("auto(")


def build_worker_option_labels(*, cpu_count: int | None = None) -> list[str]:
    """生成并行线程下拉选项（不超过本机逻辑核数）。"""
    info = get_cpu_parallel_info(cpu_count=cpu_count)
    labels = [tr("desktop.endfield.parallelWorkersAuto", n=info.recommended_workers)]
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
    if _is_auto_workers_choice(text):
        return info.recommended_workers
    try:
        workers = int(text)
    except ValueError:
        workers = info.recommended_workers
    return frozen_allow_multi_workers(max(1, min(workers, info.max_workers)))


def format_parallel_workers_help(
    info: CpuParallelInfo,
    *,
    selected_workers: int,
) -> str:
    """生成并行线程说明文案。"""
    base = tr(
        "desktop.endfield.parallelWorkersHelp",
        physical=info.physical_cores,
        logical=info.logical_processors,
        selected=selected_workers,
        max_workers=info.max_workers,
        auto_n=info.recommended_workers,
    )
    if info.recommended_workers == 1:
        return base + tr("desktop.endfield.parallelWorkersHelpSingle")
    return base + tr(
        "desktop.endfield.parallelWorkersHelpMulti",
        max_workers=info.max_workers,
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
        return tr("desktop.endfield.searchProgressPreparing", prefix=prefix)
    if eta_seconds > 0:
        remain_text = format_duration_human(eta_seconds)
        if estimated_total_seconds and estimated_total_seconds > 0:
            total_text = format_duration_human(estimated_total_seconds)
            return tr(
                "desktop.endfield.searchProgressWithTotalEta",
                prefix=prefix,
                processed=processed,
                total=total,
                remain=remain_text,
                total_eta=total_text,
            )
        return tr(
            "desktop.endfield.searchProgressWithEta",
            prefix=prefix,
            processed=processed,
            total=total,
            remain=remain_text,
        )
    return tr(
        "desktop.endfield.searchProgressCounts",
        prefix=prefix,
        processed=processed,
        total=total,
    )
