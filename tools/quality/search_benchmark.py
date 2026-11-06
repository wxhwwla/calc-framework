# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""P3-01 搜索性能基准（无头，固定 973,728 组合）。

用途：回答「约 97 万组合能否稳定 <10s」，并记录 Rust 开关、耗时、
内存峰值、TopN 一致性、取消/续跑结果。固定配置、数据模型与报告
分别见 ``search_benchmark_model`` / ``search_benchmark_report``。

用法（仓库根目录，需 ``-m`` 以便导入 ``games.*``）::

    .venv\\Scripts\\python.exe -m tools.quality.search_benchmark
    .venv\\Scripts\\python.exe -m tools.quality.search_benchmark \\
        --modes rust_full,rust_soa,python --cancel-after 100000 \\
        --out-json bench.json --out-md bench.md
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable, Generator, Sequence
from dataclasses import asdict
from pathlib import Path
from typing import Any

from games.endfield.calc.loadout.optimizer import LoadoutScore
from games.endfield.calc.search.run.cancel import SearchCancelToken
from games.endfield.calc.search.run.runner import SearchRunner

from .search_benchmark_model import (
    ALL_MODES,
    EXPECTED_COMBINATIONS,
    EXPECTED_DATA_VERSION,
    MODE_PYTHON,
    MODE_RUST_FULL,
    MODE_RUST_SOA,
    BenchmarkError,
    BenchmarkRun,
    BenchmarkSetup,
    CancelResumeReport,
    TopResult,
    _canonical_loadout,
    build_setup,
)
from .search_benchmark_model import (
    cancel_report_from_payload as _cancel_report_from_payload,
)
from .search_benchmark_model import (
    run_from_payload as _run_from_payload,
)
from .search_benchmark_report import (
    cancel_resume_markdown,
    summarize_json,
    summarize_markdown,
    topn_consistent,
)

__all__ = [
    "EXPECTED_COMBINATIONS",
    "EXPECTED_DATA_VERSION",
    "MODE_PYTHON",
    "MODE_RUST_FULL",
    "MODE_RUST_SOA",
    "BenchmarkError",
    "BenchmarkRun",
    "BenchmarkSetup",
    "CancelResumeReport",
    "TopResult",
    "build_setup",
    "main",
    "make_cancel_after_callback",
    "run_benchmark",
    "run_cancel_resume",
    "summarize_json",
    "summarize_markdown",
    "topn_consistent",
]

_ENV_KEYS = ("CALC_RUST_FULL_BATCH", "RUST_SEARCH_FALLBACK")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _child_env(mode: str) -> dict[str, str]:
    """子进程环境：Rust 开关必须在导入 ``games.*`` 前设置。"""
    if mode not in ALL_MODES:
        raise BenchmarkError(f"未知基准模式: {mode}")
    env = dict(os.environ)
    for key in _ENV_KEYS:
        env.pop(key, None)
    if mode == MODE_RUST_SOA:
        env["CALC_RUST_FULL_BATCH"] = "0"
    elif mode == MODE_PYTHON:
        env["RUST_SEARCH_FALLBACK"] = "1"
    return env


def _run_child(args: list[str], env: dict[str, str]) -> None:
    """以独立进程运行单个基准模式，避免缓存/导入期开关互相污染。"""
    completed = subprocess.run(
        [sys.executable, "-m", "tools.quality.search_benchmark", *args],
        cwd=str(_repo_root()),
        env=env,
        check=False,
    )
    if completed.returncode != 0:
        raise BenchmarkError(f"基准子进程失败（退出码 {completed.returncode}）：{' '.join(args)}")


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


@contextlib.contextmanager
def _mode_env(mode: str) -> Generator[None]:
    """按模式设置 Rust 开关，退出后恢复原环境。"""
    if mode not in ALL_MODES:
        raise BenchmarkError(f"未知基准模式: {mode}")
    saved = {key: os.environ.get(key) for key in _ENV_KEYS}
    try:
        for key in _ENV_KEYS:
            os.environ.pop(key, None)
        if mode == MODE_RUST_SOA:
            os.environ["CALC_RUST_FULL_BATCH"] = "0"
        elif mode == MODE_PYTHON:
            os.environ["RUST_SEARCH_FALLBACK"] = "1"
        yield
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _current_rss_mb() -> float | None:
    """当前进程 RSS（MB）；未安装 psutil 时返回 None。"""
    try:
        import psutil
    except ImportError:
        return None
    return float(psutil.Process().memory_info().rss) / (1024 * 1024)


class _PeakRssSampler:
    """后台采样进程 RSS 峰值（间隔 50ms）。"""

    def __init__(self, interval_seconds: float = 0.05) -> None:
        self._interval = interval_seconds
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.peak: float | None = None

    def _sample(self) -> None:
        current = _current_rss_mb()
        if current is not None and (self.peak is None or current > self.peak):
            self.peak = current

    def _loop(self) -> None:
        while not self._stop.is_set():
            self._sample()
            self._stop.wait(self._interval)

    def __enter__(self) -> _PeakRssSampler:
        self._sample()
        self._thread = threading.Thread(target=self._loop, name="bench-rss", daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *_exc_info: object) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
        self._sample()


def make_cancel_after_callback(threshold: int, token: SearchCancelToken) -> Callable[[dict[str, Any]], None]:
    """返回进度回调：已处理组合数达到阈值时请求取消。"""

    def callback(progress: dict[str, Any]) -> None:
        if int(progress.get("processed") or 0) >= threshold and not token.is_cancelled:
            token.cancel()

    return callback


def _to_top_results(scores: Sequence[LoadoutScore]) -> tuple[TopResult, ...]:
    return tuple(
        TopResult(
            weapon_name=score.weapon_name,
            final_damage=float(score.final_damage),
            loadout=_canonical_loadout(tuple(score.loadout_names.items())),
        )
        for score in scores
    )


def run_benchmark(
    setup: BenchmarkSetup,
    *,
    mode: str,
    cancel_after: int | None = None,
    db_path: Path | None = None,
    run_signature: str | None = None,
    max_workers: int = 1,
) -> BenchmarkRun:
    """按指定 Rust 模式执行一次基准搜索。"""
    cancel_token: SearchCancelToken | None = None
    progress_callback: Callable[[dict[str, Any]], None] | None = None
    if cancel_after is not None:
        cancel_token = SearchCancelToken()
        progress_callback = make_cancel_after_callback(cancel_after, cancel_token)

    started = time.perf_counter()
    with _PeakRssSampler() as sampler, _mode_env(mode):
        session = SearchRunner.run(
            base_context=setup.job.base_context,
            weapons=list(setup.job.weapon_candidates),
            equipment_catalog=setup.job.equipment_catalog,
            config=setup.config,
            max_workers=max_workers,
            cancel_token=cancel_token,
            progress_callback=progress_callback,
            db_path=db_path,
            run_signature=run_signature or setup.job.run_signature,
            search_eval=setup.search_eval,
            search_job=setup.job,
        )
    elapsed = time.perf_counter() - started
    return BenchmarkRun(
        mode=mode,
        elapsed_seconds=elapsed,
        total_combinations=int(session.total_combinations),
        processed_combinations=int(session.processed_combinations),
        cancelled=bool(session.cancelled),
        peak_rss_mb=sampler.peak,
        top_results=_to_top_results(session.top_results),
        skipped_preprocessed=int(getattr(session, "skipped_preprocessed", 0)),
    )


def run_cancel_resume(
    setup: BenchmarkSetup,
    *,
    cancel_after: int,
    mode: str = MODE_RUST_SOA,
    max_workers: int = 1,
) -> CancelResumeReport:
    """执行一次中断 + 一次续跑（使用临时 SQLite 库）。"""
    with tempfile.TemporaryDirectory(prefix="calc-search-bench-") as tmp:
        db_path = Path(tmp) / "search_benchmark.db"
        signature = f"{setup.job.run_signature}-bench"
        first = run_benchmark(
            setup,
            mode=mode,
            cancel_after=cancel_after,
            db_path=db_path,
            run_signature=signature,
            max_workers=max_workers,
        )
        second = run_benchmark(
            setup,
            mode=mode,
            db_path=db_path,
            run_signature=signature,
            max_workers=max_workers,
        )
    return CancelResumeReport(mode=mode, cancelled_run=first, resumed_run=second)


def _parse_modes(raw: str) -> list[str]:
    modes = [part.strip() for part in raw.split(",") if part.strip()]
    if "all" in modes:
        return list(ALL_MODES)
    unknown = [mode for mode in modes if mode not in ALL_MODES]
    if unknown:
        raise BenchmarkError(f"未知模式: {', '.join(unknown)}（可选: {', '.join(ALL_MODES)}, all）")
    return modes


def _run_internal(args: argparse.Namespace) -> int:
    """子进程分支：只跑一个模式/场景并写 JSON。"""
    if args.out_json is None:
        print("内部模式需要 --out-json", file=sys.stderr)
        return 2
    setup = build_setup()
    if args.internal_mode is not None:
        _write_json(args.out_json, asdict(run_benchmark(setup, mode=args.internal_mode)))
        return 0
    if args.cancel_after is None:
        print("--internal-cancel-resume 需要 --cancel-after", file=sys.stderr)
        return 2
    report = run_cancel_resume(setup, cancel_after=int(args.cancel_after))
    _write_json(args.out_json, asdict(report))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """命令行入口。"""
    parser = argparse.ArgumentParser(description="固定 973,728 组合的搜索性能基准（P3-01）")
    parser.add_argument(
        "--modes",
        default=f"{MODE_RUST_FULL},{MODE_RUST_SOA}",
        help="逗号分隔：rust_full,rust_soa,python,all",
    )
    parser.add_argument("--cancel-after", type=int, default=None, help="在 processed 达到该值时取消，并验证续跑")
    parser.add_argument("--out-json", type=Path, default=None, help="JSON 输出路径")
    parser.add_argument("--out-md", type=Path, default=None, help="Markdown 输出路径")
    parser.add_argument("--allow-data-drift", action="store_true", help="数据版本/组合数变化时仍执行")
    parser.add_argument("--internal-mode", choices=ALL_MODES, default=None, help=argparse.SUPPRESS)
    parser.add_argument("--internal-cancel-resume", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    if args.internal_mode is not None or args.internal_cancel_resume:
        return _run_internal(args)

    setup = build_setup()
    drifted = setup.data_version != EXPECTED_DATA_VERSION or setup.total_combinations != EXPECTED_COMBINATIONS
    if drifted and not args.allow_data_drift:
        print(
            f"基准数据已漂移：version={setup.data_version}（期望 {EXPECTED_DATA_VERSION}），"
            f"组合数={setup.total_combinations:,}（期望 {EXPECTED_COMBINATIONS:,}）。"
            "确认要比较新工作负载时加 --allow-data-drift。",
            file=sys.stderr,
        )
        return 2

    modes = _parse_modes(args.modes)
    runs: list[BenchmarkRun] = []
    cancel_resume: CancelResumeReport | None = None
    with tempfile.TemporaryDirectory(prefix="calc-search-bench-") as tmp:
        tmp_dir = Path(tmp)
        for mode in modes:
            print(f"[benchmark] 运行 {mode} ...", file=sys.stderr)
            child_json = tmp_dir / f"{mode}.json"
            _run_child(
                ["--internal-mode", mode, "--out-json", str(child_json), "--allow-data-drift"],
                _child_env(mode),
            )
            run = _run_from_payload(json.loads(child_json.read_text(encoding="utf-8")))
            runs.append(run)
            print(
                f"[benchmark] {mode}: {run.elapsed_seconds:.2f}s "
                f"{run.processed_combinations:,}/{run.total_combinations:,} cancelled={run.cancelled}",
                file=sys.stderr,
            )
        if args.cancel_after is not None:
            print(f"[benchmark] 取消阈值 {args.cancel_after:,} ...", file=sys.stderr)
            child_json = tmp_dir / "cancel_resume.json"
            _run_child(
                [
                    "--internal-cancel-resume",
                    "--cancel-after",
                    str(args.cancel_after),
                    "--out-json",
                    str(child_json),
                    "--allow-data-drift",
                ],
                _child_env(MODE_RUST_SOA),
            )
            cancel_resume = _cancel_report_from_payload(json.loads(child_json.read_text(encoding="utf-8")))

    parity_ok = topn_consistent(runs) if len(runs) > 1 else True
    markdown = summarize_markdown(setup=setup, runs=runs, parity_ok=parity_ok)
    if cancel_resume is not None:
        markdown += "\n" + cancel_resume_markdown(cancel_resume)
    print(markdown)

    if args.out_md is not None:
        args.out_md.write_text(markdown, encoding="utf-8")
    if args.out_json is not None:
        payload = summarize_json(setup=setup, runs=runs, parity_ok=parity_ok, cancel_resume=cancel_resume)
        _write_json(args.out_json, payload)

    complete = all(run.processed_combinations == run.total_combinations for run in runs)
    return 0 if complete and parity_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
