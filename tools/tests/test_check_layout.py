# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""布局门禁全仓扫描、历史基线豁免与过期复审的回归测试。"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from tools.quality import check_layout


def test_repo_root_resolves_to_repository_root() -> None:
    """门禁必须扫描真实仓库，而不是 tools/ 下的不存在目录。"""
    repo_root = Path(__file__).resolve().parents[2]

    assert repo_root == check_layout.REPO
    assert repo_root / "games" / "endfield" == check_layout.ENDFIELD_PKG
    assert check_layout.ENDFIELD_PKG.is_dir()


def test_check_file_length_flags_hard_cap(tmp_path: Path) -> None:
    """超过硬上限的 Python 文件必须报错。"""
    (tmp_path / "too_long.py").write_text("\n".join(["x = 1"] * 501), encoding="utf-8")

    issues = check_layout.check_file_length(max_lines=400, roots=[tmp_path])

    assert any(issue.hard and "硬上限 500" in issue.message for issue in issues)


def test_documented_exempt_paths_are_skipped(tmp_path: Path, monkeypatch) -> None:
    """§5 豁免表列出的核心算法文件不受硬顶约束。"""
    monkeypatch.setattr(check_layout, "ENDFIELD_PKG", tmp_path)
    target = tmp_path / "calc" / "multiplicative_zones" / "final_attack_zone.py"
    target.parent.mkdir(parents=True)
    target.write_text("\n".join(["x = 1"] * 501), encoding="utf-8")

    assert check_layout.check_file_length(max_lines=400, roots=[tmp_path]) == []


def test_exempt_paths_only_cover_files_over_hard_cap() -> None:
    """豁免表只应保留仍超过硬顶的文件，避免长期跳过门禁。"""
    for relative in check_layout.EXEMPT_RELATIVE_PATHS:
        target = check_layout.ENDFIELD_PKG / relative
        assert target.is_file(), f"豁免路径不存在: {relative}"
        line_count = len(target.read_text(encoding="utf-8").splitlines())
        assert line_count > 500, f"豁免路径已低于硬顶，应移出豁免表: {relative} ({line_count} 行)"


def test_check_file_length_ignores_seed_scripts(tmp_path: Path) -> None:
    """scripts/ 下的 seed_*.py 属于数据脚本，不受行数门禁约束。"""
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "seed_demo.py").write_text("\n".join(["x = 1"] * 1600), encoding="utf-8")

    assert check_layout.check_file_length(max_lines=400, roots=[tmp_path]) == []


def test_directory_width_violation_is_reported(tmp_path: Path) -> None:
    """目录子项超过上限时报告目录违规。"""
    build = tmp_path / "build"
    build.mkdir()
    for index in range(21):
        (build / f"f{index}.py").write_text("x = 1\n", encoding="utf-8")

    issues = check_layout.check_directory_width(max_items=20, roots=[tmp_path / "build"])

    assert any(issue.kind == "directory" and issue.actual == 21 for issue in issues)


def _file_violation(path: Path, lines: int = 450) -> check_layout.Violation:
    return check_layout.Violation(kind="file", path=path, actual=lines, limit=400)


def test_baseline_allows_known_violation_until_review_date(tmp_path: Path) -> None:
    """基线内的历史超限在复审日期前只告警，不失败。"""
    violation = _file_violation(tmp_path / "legacy.py")
    baseline = {
        "files": {
            "legacy.py": {"lines": 450, "review_by": "2027-01-31"},
        }
    }

    errors, warnings = check_layout.evaluate_baseline(
        [violation],
        baseline,
        today=date(2026, 11, 6),
        repo_root=tmp_path,
    )

    assert errors == []
    assert any("基线豁免" in warning for warning in warnings)


def test_baseline_entry_expired_is_error(tmp_path: Path) -> None:
    """复审日期已过的豁免必须失败，要求重新评估。"""
    violation = _file_violation(tmp_path / "legacy.py")
    baseline = {
        "files": {
            "legacy.py": {"lines": 450, "review_by": "2026-01-31"},
        }
    }

    errors, _ = check_layout.evaluate_baseline(
        [violation],
        baseline,
        today=date(2026, 11, 6),
        repo_root=tmp_path,
    )

    assert any("豁免已过期" in error for error in errors)


def test_new_violation_not_in_baseline_fails(tmp_path: Path) -> None:
    """基线之外的新超限必须失败。"""
    violation = _file_violation(tmp_path / "new_file.py")

    errors, _ = check_layout.evaluate_baseline(
        [violation],
        {"files": {}},
        today=date(2026, 11, 6),
        repo_root=tmp_path,
    )

    assert any("未登记" in error for error in errors)


def test_regression_beyond_baseline_lines_is_error(tmp_path: Path) -> None:
    """历史文件继续变长时，即使有基线也必须失败。"""
    violation = _file_violation(tmp_path / "legacy.py", lines=520)
    baseline = {
        "files": {
            "legacy.py": {"lines": 500, "review_by": "2027-01-31"},
        }
    }

    errors, _ = check_layout.evaluate_baseline(
        [violation],
        baseline,
        today=date(2026, 11, 6),
        repo_root=tmp_path,
    )

    assert any("超过基线" in error for error in errors)


def test_repository_passes_with_committed_baseline() -> None:
    """提交的基线必须覆盖当前仓库的全部历史超限，门禁应通过。"""
    assert check_layout.main(["--max-lines", "400"]) == 0


def test_write_baseline_round_trip(tmp_path: Path) -> None:
    """--write-baseline 生成的基线可被再次读取并通过评估。"""
    (tmp_path / "legacy.py").write_text("\n".join(["x = 1"] * 450), encoding="utf-8")
    baseline_path = tmp_path / "baseline.json"

    assert (
        check_layout.main(
            [
                "--roots",
                str(tmp_path),
                "--max-lines",
                "400",
                "--write-baseline",
                "--baseline",
                str(baseline_path),
                "--today",
                "2026-11-06",
            ]
        )
        == 0
    )

    baseline = check_layout.load_baseline(baseline_path)
    assert baseline["files"]["legacy.py"]["lines"] == 450

    assert (
        check_layout.main(
            [
                "--roots",
                str(tmp_path),
                "--max-lines",
                "400",
                "--baseline",
                str(baseline_path),
                "--today",
                "2026-11-06",
            ]
        )
        == 0
    )


@pytest.mark.parametrize("flag", ["--scope", "--roots"])
def test_scope_and_roots_are_mutually_exclusive(flag: str) -> None:
    """--scope 与 --roots 不能同时使用。"""
    with pytest.raises(SystemExit):
        check_layout.main(["--scope", "repo", "--roots", ".", "--max-lines", "400"])
