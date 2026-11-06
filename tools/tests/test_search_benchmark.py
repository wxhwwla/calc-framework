# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""搜索性能基准工具（P3-01）回归测试。

基准本身不在此处跑全量（973,728 组合需约 30s），测试只覆盖：
- 固定基线的组合数/装备目录规模（数据版本漂移守卫）
- 模式环境变量的设置与恢复
- 结果摘要与 TopN 一致性比较
- 取消阈值回调
"""

from __future__ import annotations

import dataclasses
import json
import os
from unittest.mock import Mock, patch

import pytest

from games.endfield.calc.loadout.optimizer import LoadoutScore
from games.endfield.calc.search.run.cancel import SearchCancelToken
from games.endfield.calc.search.run.session import SearchSessionResult
from tools.quality import search_benchmark as sb


def test_build_setup_matches_fixed_baseline() -> None:
    setup = sb.build_setup()

    assert setup.data_version == sb.EXPECTED_DATA_VERSION
    assert setup.total_combinations == sb.EXPECTED_COMBINATIONS == 973_728
    assert setup.catalog_sizes == {"chest": 24, "gloves": 23, "accessories": 42}
    assert len(setup.job.weapon_candidates) == 1


def test_mode_env_sets_and_restores(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CALC_RUST_FULL_BATCH", raising=False)
    monkeypatch.delenv("RUST_SEARCH_FALLBACK", raising=False)

    with sb._mode_env(sb.MODE_RUST_SOA):
        assert os.environ["CALC_RUST_FULL_BATCH"] == "0"
        assert "RUST_SEARCH_FALLBACK" not in os.environ

    assert "CALC_RUST_FULL_BATCH" not in os.environ

    with sb._mode_env(sb.MODE_PYTHON):
        assert os.environ["RUST_SEARCH_FALLBACK"] == "1"

    assert "RUST_SEARCH_FALLBACK" not in os.environ


def test_child_env_isolated_per_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CALC_RUST_FULL_BATCH", "1")
    monkeypatch.setenv("RUST_SEARCH_FALLBACK", "1")

    full = sb._child_env(sb.MODE_RUST_FULL)
    assert "CALC_RUST_FULL_BATCH" not in full
    assert "RUST_SEARCH_FALLBACK" not in full

    soa = sb._child_env(sb.MODE_RUST_SOA)
    assert soa["CALC_RUST_FULL_BATCH"] == "0"
    assert "RUST_SEARCH_FALLBACK" not in soa

    python_env = sb._child_env(sb.MODE_PYTHON)
    assert python_env["RUST_SEARCH_FALLBACK"] == "1"
    assert "CALC_RUST_FULL_BATCH" not in python_env


def test_run_from_payload_round_trips_dataclass() -> None:
    run = sb.BenchmarkRun(
        mode=sb.MODE_RUST_FULL,
        elapsed_seconds=1.5,
        total_combinations=3,
        processed_combinations=2,
        cancelled=True,
        peak_rss_mb=10.0,
        top_results=(sb.TopResult("W", 1.0, (("chest", "C"),)),),
        skipped_preprocessed=1,
    )

    restored = sb._run_from_payload(json.loads(json.dumps(dataclasses.asdict(run))))

    assert restored == run


def test_progress_with_cancel_triggers_once() -> None:
    token = SearchCancelToken()
    callback = sb.make_cancel_after_callback(100, token)

    callback({"processed": 50})
    assert not token.is_cancelled

    callback({"processed": 100})
    assert token.is_cancelled


def test_run_benchmark_records_session_result() -> None:
    setup = Mock()
    setup.job = Mock()
    setup.job.run_signature = "sig"
    setup.job.weapon_candidates = ()
    setup.job.equipment_catalog = {}
    setup.job.base_context = Mock()
    setup.search_eval = Mock()
    setup.config = Mock()

    scores = (LoadoutScore(weapon_name="W", final_damage=123.456, loadout_names={"chest": "C"}),)
    fake_result = SearchSessionResult(
        top_results=scores,
        total_combinations=973_728,
        processed_combinations=973_728,
        cancelled=False,
        warnings=(),
    )

    with (
        patch.object(sb.SearchRunner, "run", return_value=fake_result) as run,
        patch.object(sb, "_current_rss_mb", return_value=321.5),
    ):
        result = sb.run_benchmark(setup, mode=sb.MODE_RUST_FULL)

    assert result.mode == sb.MODE_RUST_FULL
    assert result.processed_combinations == 973_728
    assert result.total_combinations == 973_728
    assert result.elapsed_seconds >= 0
    assert result.peak_rss_mb == 321.5
    assert result.top_results[0].weapon_name == "W"
    assert result.top_results[0].loadout == (("chest", "C"),)
    assert run.call_args.kwargs["search_job"] is setup.job
    assert run.call_args.kwargs["db_path"] is None


def test_topn_consistency_within_tolerance() -> None:
    a = sb.BenchmarkRun(
        mode="rust_full",
        elapsed_seconds=30.0,
        total_combinations=10,
        processed_combinations=10,
        cancelled=False,
        peak_rss_mb=100.0,
        top_results=(sb.TopResult("W", 100.0, (("chest", "C"),)),),
    )
    b = sb.BenchmarkRun(
        mode="rust_soa",
        elapsed_seconds=31.0,
        total_combinations=10,
        processed_combinations=10,
        cancelled=False,
        peak_rss_mb=100.0,
        top_results=(sb.TopResult("W", 100.0 + 1e-9, (("chest", "C"),)),),
    )
    c = sb.BenchmarkRun(
        mode="python",
        elapsed_seconds=80.0,
        total_combinations=10,
        processed_combinations=10,
        cancelled=False,
        peak_rss_mb=100.0,
        top_results=(sb.TopResult("W", 101.0, (("chest", "C"),)),),
    )

    assert sb.topn_consistent([a, b])
    assert not sb.topn_consistent([a, c])


def test_topn_consistency_treats_accessory_slots_as_interchangeable() -> None:
    base = (("chest", "C"), ("gloves", "G"))
    a = sb.BenchmarkRun(
        mode="rust_full",
        elapsed_seconds=30.0,
        total_combinations=10,
        processed_combinations=10,
        cancelled=False,
        peak_rss_mb=100.0,
        top_results=(sb.TopResult("W", 100.0, (*base, ("accessory_a", "X"), ("accessory_b", "Y"))),),
    )
    b = sb.BenchmarkRun(
        mode="rust_soa",
        elapsed_seconds=31.0,
        total_combinations=10,
        processed_combinations=10,
        cancelled=False,
        peak_rss_mb=100.0,
        top_results=(sb.TopResult("W", 100.0, (*base, ("accessory_a", "Y"), ("accessory_b", "X"))),),
    )

    assert sb.topn_consistent([a, b])


def test_topn_consistency_ignores_tie_order() -> None:
    first = (sb.TopResult("W", 100.0, (("chest", "A"),)), sb.TopResult("W", 100.0, (("chest", "B"),)))
    second = (sb.TopResult("W", 100.0, (("chest", "B"),)), sb.TopResult("W", 100.0, (("chest", "A"),)))

    def _run(mode: str, results: tuple[sb.TopResult, ...]) -> sb.BenchmarkRun:
        return sb.BenchmarkRun(
            mode=mode,
            elapsed_seconds=1.0,
            total_combinations=2,
            processed_combinations=2,
            cancelled=False,
            peak_rss_mb=None,
            top_results=results,
        )

    assert sb.topn_consistent([_run("rust_full", first), _run("rust_soa", second)])


def test_summarize_markdown_contains_measurements() -> None:
    run = sb.BenchmarkRun(
        mode=sb.MODE_RUST_FULL,
        elapsed_seconds=30.0,
        total_combinations=973_728,
        processed_combinations=973_728,
        cancelled=False,
        peak_rss_mb=512.0,
        top_results=(sb.TopResult("W", 100.0, (("chest", "C"),)),),
    )
    markdown = sb.summarize_markdown(
        setup=Mock(
            data_version="1.1.0",
            total_combinations=973_728,
            catalog_sizes={"chest": 24, "gloves": 23, "accessories": 42},
        ),
        runs=[run],
        parity_ok=True,
    )

    assert "973,728" in markdown
    assert "rust_full" in markdown
    assert "30.00" in markdown
    assert "512" in markdown
