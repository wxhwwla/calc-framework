# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""P3-01 基准结果比较与 Markdown / JSON 摘要。"""

from __future__ import annotations

import os
import platform
from collections.abc import Sequence
from dataclasses import asdict
from datetime import datetime
from typing import Any

from .search_benchmark_model import (
    _TARGET_SECONDS,
    EXPECTED_COMBINATIONS,
    EXPECTED_DATA_VERSION,
    BenchmarkRun,
    BenchmarkSetup,
    CancelResumeReport,
    _canonical_loadout,
)

__all__ = [
    "cancel_resume_markdown",
    "discover_platform",
    "summarize_json",
    "summarize_markdown",
    "topn_consistent",
]


def _format_rss(run: BenchmarkRun) -> str:
    return "N/A" if run.peak_rss_mb is None else f"{run.peak_rss_mb:.1f}"


def discover_platform() -> str:
    """可读的运行环境说明（写入摘要）。"""
    return f"{platform.system()} {platform.machine()} / Python {platform.python_version()} / {os.cpu_count()} CPUs"


def _top_result_sort_key(result: Any) -> tuple[float, str, tuple[tuple[str, str], ...]]:
    """按伤害降序、再按配装稳定排序，使等伤害并列项的先后不影响比较。"""
    return (-result.final_damage, result.weapon_name, _canonical_loadout(result.loadout))


def topn_consistent(runs: Sequence[BenchmarkRun], *, rel_tol: float = 1e-9) -> bool:
    """所有运行的前 N 结果构成同一多重集合（等伤害并列项顺序不敏感）。"""
    if len(runs) < 2:
        return True
    if not runs[0].top_results:
        return False
    baseline = sorted(runs[0].top_results, key=_top_result_sort_key)
    for run in runs[1:]:
        if len(run.top_results) != len(baseline):
            return False
        ordered = sorted(run.top_results, key=_top_result_sort_key)
        if not all(left.matches(right, rel_tol=rel_tol) for left, right in zip(baseline, ordered)):
            return False
    return True


def summarize_markdown(
    *,
    setup: BenchmarkSetup | Any,
    runs: Sequence[BenchmarkRun],
    parity_ok: bool,
) -> str:
    """生成人读摘要（Markdown 表格）。"""
    catalog = ", ".join(f"{key}={value}" for key, value in setup.catalog_sizes.items())
    lines = [
        "# 搜索性能基准（P3-01）",
        "",
        f"- 数据版本：{setup.data_version}",
        f"- 期望数据版本：{EXPECTED_DATA_VERSION}",
        f"- 固定组合数：{setup.total_combinations:,}（期望 {EXPECTED_COMBINATIONS:,}）",
        f"- 装备目录（剪枝后）：{catalog}",
        f"- 目标耗时：< {_TARGET_SECONDS:.0f}s",
        f"- 运行环境：{discover_platform()}",
        f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"- TopN 一致性：{'✅' if parity_ok else '❌'}",
        "",
        "| 模式 | 耗时(s) | 组合/秒 | 峰值RSS(MB) | processed/total | 取消 | <10s |",
        "|------|--------:|--------:|------------:|-----------------|------|------|",
    ]
    for run in runs:
        lines.append(
            (
                "| {mode} | {elapsed:.2f} | {throughput:,.0f} | {rss} | "
                "{processed:,}/{total:,} | {cancelled} | {target} |"
            ).format(
                mode=run.mode,
                elapsed=run.elapsed_seconds,
                throughput=run.throughput,
                rss=_format_rss(run),
                processed=run.processed_combinations,
                total=run.total_combinations,
                cancelled="是" if run.cancelled else "否",
                target="✅" if run.under_target else "❌",
            )
        )
    return "\n".join(lines) + "\n"


def cancel_resume_markdown(report: CancelResumeReport) -> str:
    first, second = report.cancelled_run, report.resumed_run
    return "\n".join(
        [
            "## 取消 / 续跑",
            "",
            f"- 模式：{report.mode}",
            f"- 取消阈值：中断阶段 processed={first.processed_combinations:,}，"
            f"cancelled={'是' if first.cancelled else '否'}",
            f"- 续跑阶段：skipped_preprocessed={second.skipped_preprocessed:,}，"
            f"processed={second.processed_combinations:,}/{second.total_combinations:,}，"
            f"耗时 {second.elapsed_seconds:.2f}s",
            "",
        ]
    )


def summarize_json(
    *,
    setup: BenchmarkSetup,
    runs: Sequence[BenchmarkRun],
    parity_ok: bool,
    cancel_resume: CancelResumeReport | None = None,
) -> dict[str, Any]:
    """机器可读摘要（JSON 序列化友好）。"""
    payload: dict[str, Any] = {
        "data_version": setup.data_version,
        "expected_data_version": EXPECTED_DATA_VERSION,
        "expected_combinations": EXPECTED_COMBINATIONS,
        "total_combinations": setup.total_combinations,
        "catalog_sizes": dict(setup.catalog_sizes),
        "platform": discover_platform(),
        "parity_ok": parity_ok,
        "runs": [asdict(run) for run in runs],
    }
    if cancel_resume is not None:
        payload["cancel_resume"] = asdict(cancel_resume)
    return payload
