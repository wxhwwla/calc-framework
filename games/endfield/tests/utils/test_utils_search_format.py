# SPDX-License-Identifier: AGPL-3.0
from __future__ import annotations

from unittest.mock import MagicMock

from utils.search_format import format_duration_human, format_workload_estimate_line


class TestFormatDurationHuman:
    def test_less_than_one_second(self) -> None:
        assert format_duration_human(0) == "少于 1 秒"

    def test_fractional_second(self) -> None:
        assert format_duration_human(0.5) == "少于 1 秒"

    def test_seconds_only(self) -> None:
        assert format_duration_human(30) == "约 30 秒"

    def test_minutes_and_seconds(self) -> None:
        assert format_duration_human(90) == "约 1 分 30 秒"

    def test_exact_minutes(self) -> None:
        assert format_duration_human(120) == "约 2 分钟"

    def test_hours_and_minutes(self) -> None:
        assert format_duration_human(3660) == "约 1 小时 1 分"

    def test_exact_hours(self) -> None:
        assert format_duration_human(7200) == "约 2 小时"

    def test_negative(self) -> None:
        assert format_duration_human(-5) == "少于 1 秒"


class TestFormatWorkloadEstimateLine:
    def test_zero_total(self) -> None:
        workload = MagicMock(total_combinations=0, weapon_count=0, loadout_combinations=0)
        duration = MagicMock(estimated_seconds=0, max_workers=1)
        result = format_workload_estimate_line(workload=workload, duration=duration)
        assert "0（请检查候选范围" in result

    def test_positive_total(self) -> None:
        workload = MagicMock(total_combinations=42000, weapon_count=5, loadout_combinations=8400)
        duration = MagicMock(estimated_seconds=300, max_workers=7)
        result = format_workload_estimate_line(workload=workload, duration=duration)
        assert "42,000" in result
        assert "5 武器" in result
        assert "8,400" in result
        assert "约 5 分" in result
        assert "7 线程" in result
