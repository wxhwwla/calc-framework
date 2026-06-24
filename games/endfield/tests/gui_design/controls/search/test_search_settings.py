# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
from __future__ import annotations

from games.endfield.gui.controls.search.search_settings import (
    CpuParallelInfo,
    build_worker_option_labels,
    default_parallel_workers,
    format_duration_human,
    format_parallel_workers_help,
    format_search_progress_text,
    format_workload_estimate_line,
    get_cpu_parallel_info,
    resolve_parallel_workers,
    resolve_top_n,
)


class TestGetCpuParallelInfo:
    def test_with_explicit_count(self) -> None:
        info = get_cpu_parallel_info(cpu_count=8)

        assert info.logical_processors == 8

        assert info.physical_cores == 8

        assert info.recommended_workers == 1

        assert info.max_workers == 8

        assert info.logical_cores == 8

    def test_minimum_one(self) -> None:
        info = get_cpu_parallel_info(cpu_count=0)

        assert info.logical_processors == 1

        assert info.recommended_workers == 1

    def test_dataclass(self) -> None:
        info = get_cpu_parallel_info(cpu_count=4)

        assert isinstance(info, CpuParallelInfo)


class TestDefaultParallelWorkers:
    def test_explicit_count(self) -> None:
        assert default_parallel_workers(cpu_count=4) == 1


class TestBuildWorkerOptionLabels:
    def test_contains_auto(self) -> None:
        labels = build_worker_option_labels(cpu_count=8)

        auto_labels = [lb for lb in labels if "自动" in lb]

        assert len(auto_labels) == 1

    def test_with_small_cpu(self) -> None:
        labels = build_worker_option_labels(cpu_count=2)

        assert len(labels) >= 1


class TestResolveParallelWorkers:
    def test_auto_choice(self) -> None:
        assert resolve_parallel_workers("自动 (7 线程)", cpu_count=8) == 1

    def test_auto_prefix(self) -> None:
        assert resolve_parallel_workers("自动", cpu_count=4) == 1

    def test_numeric_choice(self) -> None:
        assert resolve_parallel_workers("4", cpu_count=8) == 1

    def test_capped_by_max(self) -> None:
        assert resolve_parallel_workers("16", cpu_count=4) == 1

    def test_minimum_one(self) -> None:
        assert resolve_parallel_workers("0", cpu_count=4) == 1

    def test_empty_choice(self) -> None:
        assert resolve_parallel_workers("", cpu_count=4) == 1

    def test_garbage_text(self) -> None:
        assert resolve_parallel_workers("not a number", cpu_count=4) == 1


class TestFormatParallelWorkersHelp:
    def test_contains_core_info(self) -> None:
        info = CpuParallelInfo(
            logical_processors=8,
            physical_cores=4,
            recommended_workers=7,
            max_workers=8,
        )

        text = format_parallel_workers_help(info, selected_workers=4)

        assert "逻辑线程 8" in text

        assert "物理核心约 4" in text

        assert "4 个搜索 worker" in text

        assert "7 worker" in text


class TestResolveTopN:
    def test_normal(self) -> None:
        assert resolve_top_n("5", default=10) == 5

    def test_minimum_one(self) -> None:
        assert resolve_top_n("0", default=10) == 1

    def test_empty_string(self) -> None:
        assert resolve_top_n("", default=10) == 10

    def test_garbage(self) -> None:
        assert resolve_top_n("abc", default=20) == 20

    def test_whitespace(self) -> None:
        assert resolve_top_n("  3  ", default=10) == 3


class TestFormatDurationHuman:
    def test_re_export_seconds(self) -> None:
        assert "30 秒" in format_duration_human(30)

    def test_re_export_hours(self) -> None:
        assert "2 小时" in format_duration_human(7200)


class TestFormatWorkloadEstimateLine:
    def test_re_export(self) -> None:
        from unittest.mock import MagicMock

        workload = MagicMock(total_combinations=100, weapon_count=2, loadout_combinations=50)

        duration = MagicMock(estimated_seconds=60, max_workers=4)

        text = format_workload_estimate_line(workload=workload, duration=duration)

        assert "100" in text


class TestFormatSearchProgressText:
    def test_preparing_when_total_zero(self) -> None:
        text = format_search_progress_text(
            prefix="搜索",
            processed=0,
            total=0,
            eta_seconds=0,
        )

        assert "准备中" in text

    def test_with_eta(self) -> None:
        text = format_search_progress_text(
            prefix="搜索",
            processed=50,
            total=100,
            eta_seconds=30,
        )

        assert "50/100" in text

        assert "30 秒" in text

    def test_with_estimated_total(self) -> None:
        text = format_search_progress_text(
            prefix="搜索",
            processed=50,
            total=100,
            eta_seconds=30,
            estimated_total_seconds=120,
        )

        assert "总预计" in text

        assert "2 分钟" in text

    def test_no_eta(self) -> None:
        text = format_search_progress_text(
            prefix="搜索",
            processed=50,
            total=100,
            eta_seconds=0,
        )

        assert "50/100" in text

        assert "剩余" not in text
