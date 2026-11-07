# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""Git 历史对象扫描：解析、可疑判定与只读报告的回归测试。"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from tools.quality.supply_chain import scan_git_history


def test_parse_rev_list_keeps_paths_with_spaces() -> None:
    """rev-list 输出按首个空格切分，路径中的空格必须保留。"""
    text = "abc123\ndef456 build/output/超大 文件.pyz\n"

    assert scan_git_history.parse_rev_list(text) == {
        "abc123": "",
        "def456": "build/output/超大 文件.pyz",
    }


def test_parse_batch_check_reads_type_and_size() -> None:
    """batch-check 输出应解析对象类型、大小，并跳过 missing。"""
    text = "abc123 blob 12523837\ndef456 missing\nghi789 tree 123\n"

    assert scan_git_history.parse_batch_check(text) == {
        "abc123": {"type": "blob", "size": 12523837},
        "ghi789": {"type": "tree", "size": 123},
    }


def test_find_suspicious_flags_large_build_artifacts() -> None:
    """超过阈值的构建产物应同时标注 large 与 pattern 原因。"""
    entries = [
        {
            "sha": "abc123",
            "path": "build_local-backend/终末地本地搜索服务器/PYZ-00.pyz",
            "type": "blob",
            "size": 12_523_837,
        },
        {
            "sha": "def456",
            "path": "games/endfield/data/characters.json",
            "type": "blob",
            "size": 1_000_000,
        },
    ]

    suspicious = scan_git_history.find_suspicious(entries, threshold_bytes=4_194_304)

    assert len(suspicious) == 1
    assert suspicious[0]["sha"] == "abc123"
    assert "large" in suspicious[0]["reasons"]
    assert "build-artifact" in suspicious[0]["reasons"]


def test_find_suspicious_flags_small_artifacts_by_pattern() -> None:
    """小体积的明确构建产物也应列为可疑，便于人工复核。"""
    entries = [
        {"sha": "x", "path": "dist/app.exe", "type": "blob", "size": 1024},
        {"sha": "y", "path": "docs/readme.md", "type": "blob", "size": 1024},
    ]

    suspicious = scan_git_history.find_suspicious(entries, threshold_bytes=4_194_304)

    assert [item["sha"] for item in suspicious] == ["x"]


def test_main_writes_read_only_report(tmp_path: Path) -> None:
    """--json-out 报告必须声明不重写历史，并记录对象清单。"""
    rev_list = tmp_path / "rev-list.txt"
    rev_list.write_text("abc123 heavy.zip\n", encoding="utf-8")
    batch_check = tmp_path / "batch-check.txt"
    batch_check.write_text("abc123 blob 9000000\n", encoding="utf-8")
    report_path = tmp_path / "history-report.json"

    exit_code = scan_git_history.main(
        [
            "--rev-list-file",
            str(rev_list),
            "--batch-check-file",
            str(batch_check),
            "--json-out",
            str(report_path),
        ]
    )

    assert exit_code == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["history_rewrite"] is False
    assert report["suspicious_count"] == 1
    assert report["large_objects"][0]["path"] == "heavy.zip"


def _is_shallow_clone(repo: Path) -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--is-shallow-repository"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() == "true"


def test_repository_scan_reports_known_large_object() -> None:
    """真实仓库扫描应能发现审查清单记录的 12 MB 构建产物（只读）。"""
    if _is_shallow_clone(scan_git_history.REPO):
        pytest.skip("浅克隆不含完整历史；完整扫描由 security-audit supply-chain job 覆盖")
    report = scan_git_history.scan_repository(scan_git_history.REPO, threshold_bytes=4_194_304)

    assert report["history_rewrite"] is False
    assert report["object_count"] > 0
    assert any(item["path"].endswith("PYZ-00.pyz") for item in report["large_objects"])
