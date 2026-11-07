# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""性能门禁：pytest-benchmark 结果与预算对比的回归测试。"""

from __future__ import annotations

import json
from pathlib import Path

from tools.quality import check_benchmarks


def _payload(*entries: tuple[str, float]) -> dict:
    return {
        "machine_info": {"node": "ci-runner", "python": "3.12"},
        "commit_info": {"id": "abc123"},
        "benchmarks": [
            {
                "name": f"tests/benchmarks/test_dag_benchmark.py::TestX::{name}",
                "stats": {"mean": mean_seconds, "median": mean_seconds},
            }
            for name, mean_seconds in entries
        ],
    }


def test_no_violation_when_within_budget() -> None:
    """低于预算时通过。"""
    errors, warnings, results = check_benchmarks.check(
        _payload(("test_fast", 0.00001)),
        {"benchmarks": {"test_fast": {"budget_ms": 0.05, "tolerance": 3.0}}},
    )

    assert errors == []
    assert warnings == []
    assert results[0]["status"] == "pass"


def test_hard_failure_beyond_tolerance() -> None:
    """超过 预算 × 容差 时失败。"""
    errors, _, results = check_benchmarks.check(
        _payload(("test_slow", 0.0004)),
        {"benchmarks": {"test_slow": {"budget_ms": 0.05, "tolerance": 3.0}}},
    )

    assert any("超过预算上限" in error for error in errors)
    assert results[0]["status"] == "fail"


def test_over_budget_within_tolerance_only_warns() -> None:
    """超出目标但仍在容差内只告警，保留 CI 抖动空间。"""
    errors, warnings, results = check_benchmarks.check(
        _payload(("test_jitter", 0.0001)),
        {"benchmarks": {"test_jitter": {"budget_ms": 0.05, "tolerance": 3.0}}},
    )

    assert errors == []
    assert any("超过目标预算" in warning for warning in warnings)
    assert results[0]["status"] == "warn"


def test_missing_benchmark_is_error() -> None:
    """预算中的基准缺失（被跳过或改名）必须失败。"""
    errors, _, _ = check_benchmarks.check(
        _payload(),
        {"benchmarks": {"test_expected": {"budget_ms": 1.0, "tolerance": 2.0}}},
    )

    assert any("基准缺失" in error for error in errors)


def test_unknown_benchmark_is_warning() -> None:
    """未登记预算的基准只告警，提示后续补登记。"""
    errors, warnings, _ = check_benchmarks.check(
        _payload(("test_new", 0.00001)),
        {"benchmarks": {}},
    )

    assert errors == []
    assert any("未登记预算" in warning for warning in warnings)


def test_committed_budgets_cover_existing_benchmarks() -> None:
    """仓库预算文件必须登记全部现有基准测试名。"""
    budgets = check_benchmarks.load_budgets(check_benchmarks.BUDGETS_PATH)
    names = set(budgets["benchmarks"])
    source = (
        Path(__file__).resolve().parents[3] / "framework" / "tests" / "benchmarks" / "test_dag_benchmark.py"
    ).read_text(encoding="utf-8")

    for name in names:
        assert f"def {name}(" in source, f"预算登记了不存在的基准: {name}"


def test_main_writes_report(tmp_path: Path) -> None:
    """--json-out 应输出含机器信息与逐项状态的报告。"""
    payload = _payload(("test_fast", 0.00001))
    input_path = tmp_path / "benchmark.json"
    input_path.write_text(json.dumps(payload), encoding="utf-8")
    budgets_path = tmp_path / "budgets.json"
    budgets_path.write_text(
        json.dumps({"benchmarks": {"test_fast": {"budget_ms": 0.05, "tolerance": 3.0}}}),
        encoding="utf-8",
    )
    report_path = tmp_path / "benchmark-check.json"

    exit_code = check_benchmarks.main(
        [
            "--input",
            str(input_path),
            "--budgets",
            str(budgets_path),
            "--json-out",
            str(report_path),
        ]
    )

    assert exit_code == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["machine_info"]["node"] == "ci-runner"
    assert report["results"][0]["status"] == "pass"


def test_missing_budget_file_is_configuration_error(tmp_path: Path) -> None:
    """预算文件缺失属于配置错误，不能静默通过。"""
    input_path = tmp_path / "benchmark.json"
    input_path.write_text(json.dumps(_payload()), encoding="utf-8")

    assert (
        check_benchmarks.main(
            [
                "--input",
                str(input_path),
                "--budgets",
                str(tmp_path / "missing.json"),
            ]
        )
        == 1
    )
