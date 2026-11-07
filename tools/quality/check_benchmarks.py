#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""性能预算门禁：对比 pytest-benchmark JSON 与 ``benchmark_budgets.json``。

判定规则：

- ``mean`` 超过 ``budget_ms × tolerance`` → 失败；
- 超过 ``budget_ms`` 但仍在容差内 → 告警；
- 预算登记的基准缺失 → 失败（防止测试被跳过或改名后静默失效）；
- 未登记预算的基准 → 告警。

用法（仓库根目录）::

    python tools/quality/check_benchmarks.py --input framework/benchmark.json
    python tools/quality/check_benchmarks.py --input benchmark.json --json-out report.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BUDGETS_PATH = REPO / "tools" / "quality" / "benchmark_budgets.json"


def load_budgets(path: Path = BUDGETS_PATH) -> dict:
    """读取并校验预算文件。

    Raises:
        FileNotFoundError: 预算文件不存在
        ValueError: 结构不合法
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    benchmarks = data.get("benchmarks")
    if not isinstance(benchmarks, dict) or not benchmarks:
        raise ValueError(f"预算文件缺少 benchmarks: {path}")
    for name, config in benchmarks.items():
        if not isinstance(config, dict) or not isinstance(config.get("budget_ms"), int | float):
            raise ValueError(f"基准 {name} 缺少数值 budget_ms")
        config.setdefault("tolerance", 2.0)
        if not isinstance(config["tolerance"], int | float) or config["tolerance"] <= 0:
            raise ValueError(f"基准 {name} 的 tolerance 必须为正数")
    return data


def load_benchmark_payload(path: Path) -> dict:
    """读取 pytest-benchmark 生成的 JSON。"""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data.get("benchmarks"), list):
        raise ValueError(f"不是 pytest-benchmark JSON: {path}")
    return data


def _stats_by_name(payload: dict) -> dict[str, dict]:
    stats: dict[str, dict] = {}
    for item in payload.get("benchmarks", []):
        name = str(item.get("name", "")).rsplit("::", 1)[-1]
        values = item.get("stats", {})
        mean = values.get("mean")
        if not name or not isinstance(mean, int | float):
            continue
        median = values.get("median", mean)
        stats[name] = {
            "mean_ms": float(mean) * 1000.0,
            "median_ms": float(median) * 1000.0,
        }
    return stats


def check(payload: dict, budgets: dict) -> tuple[list[str], list[str], list[dict]]:
    """对比基准结果与预算，返回 (错误, 告警, 明细)。"""
    stats = _stats_by_name(payload)
    errors: list[str] = []
    warnings: list[str] = []
    results: list[dict] = []

    for name, config in sorted(budgets["benchmarks"].items()):
        budget_ms = float(config["budget_ms"])
        tolerance = float(config.get("tolerance", 2.0))
        limit_ms = budget_ms * tolerance
        if name not in stats:
            errors.append(f"基准缺失: {name}（被跳过、改名或未运行）")
            results.append(
                {
                    "name": name,
                    "status": "missing",
                    "budget_ms": budget_ms,
                    "tolerance": tolerance,
                    "limit_ms": limit_ms,
                }
            )
            continue
        actual = stats[name]["mean_ms"]
        entry = {
            "name": name,
            "mean_ms": round(actual, 6),
            "median_ms": round(stats[name]["median_ms"], 6),
            "budget_ms": budget_ms,
            "tolerance": tolerance,
            "limit_ms": limit_ms,
        }
        if actual > limit_ms:
            entry["status"] = "fail"
            errors.append(
                f"{name}: mean {actual:.4f} ms 超过预算上限 {limit_ms:.4f} ms（目标 {budget_ms} × {tolerance}）"
            )
        elif actual > budget_ms:
            entry["status"] = "warn"
            warnings.append(
                f"{name}: mean {actual:.4f} ms 超过目标预算 {budget_ms} ms，仍在容差上限 {limit_ms:.4f} ms 内"
            )
        else:
            entry["status"] = "pass"
        results.append(entry)

    for name in sorted(set(stats) - set(budgets["benchmarks"])):
        warnings.append(f"{name}: 未登记预算（如属核心路径请补充 benchmark_budgets.json）")
        results.append(
            {
                "name": name,
                "status": "unbudgeted",
                "mean_ms": round(stats[name]["mean_ms"], 6),
            }
        )

    return errors, warnings, results


def _write_report(
    path: Path,
    *,
    payload: dict,
    budgets_path: Path,
    results: list[dict],
    errors: list[str],
    warnings: list[str],
) -> None:
    report = {
        "budgets_file": str(budgets_path),
        "machine_info": payload.get("machine_info", {}),
        "commit_info": payload.get("commit_info", {}),
        "datetime": payload.get("datetime"),
        "results": results,
        "errors": errors,
        "warnings": warnings,
    }
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    """CLI 入口：读取基准结果并执行预算门禁。"""
    parser = argparse.ArgumentParser(description="检查性能基准是否超出预算")
    parser.add_argument("--input", type=Path, default=Path("benchmark.json"))
    parser.add_argument("--budgets", type=Path, default=BUDGETS_PATH)
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        budgets = load_budgets(args.budgets)
        payload = load_benchmark_payload(args.input)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: 无法读取性能门禁输入: {exc}")
        return 1

    errors, warnings, results = check(payload, budgets)
    if args.json_out is not None:
        _write_report(
            args.json_out,
            payload=payload,
            budgets_path=args.budgets,
            results=results,
            errors=errors,
            warnings=warnings,
        )

    for result in results:
        print(f"{result['status'].upper():10} {result['name']}")
    for warning in warnings:
        print(f"WARN: {warning}")
    for error in errors:
        print(f"ERROR: {error}")

    if errors:
        print(f"性能预算检查失败：{len(errors)} 个错误，{len(warnings)} 个告警。")
        return 1
    print(f"性能预算检查通过（{len(results)} 项，{len(warnings)} 个告警）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
