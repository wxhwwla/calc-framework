# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""布局门禁根目录解析与文件行数检查的回归测试。"""

from __future__ import annotations

from pathlib import Path

from tools.quality import check_layout


def test_repo_root_resolves_to_repository_root() -> None:
    """门禁必须扫描真实仓库，而不是 tools/ 下的不存在目录。"""
    repo_root = Path(__file__).resolve().parents[2]

    assert repo_root == check_layout.REPO
    assert repo_root / "games" / "endfield" == check_layout.PKG
    assert check_layout.PKG.is_dir()


def test_check_file_length_flags_hard_cap(tmp_path: Path, monkeypatch) -> None:
    """超过硬上限的 Python 文件必须报错。"""
    monkeypatch.setattr(check_layout, "REPO", tmp_path)
    monkeypatch.setattr(check_layout, "PKG", tmp_path)
    (tmp_path / "too_long.py").write_text("\n".join(["x = 1"] * 501), encoding="utf-8")

    issues = check_layout.check_file_length(max_lines=400)

    assert any("硬上限 500" in issue for issue in issues)


def test_documented_exempt_paths_are_skipped(tmp_path: Path, monkeypatch) -> None:
    """§5 豁免表列出的核心算法文件不受硬顶约束。"""
    monkeypatch.setattr(check_layout, "REPO", tmp_path)
    monkeypatch.setattr(check_layout, "PKG", tmp_path)
    target = tmp_path / "calc" / "multiplicative_zones" / "final_attack_zone.py"
    target.parent.mkdir(parents=True)
    target.write_text("\n".join(["x = 1"] * 501), encoding="utf-8")

    assert check_layout.check_file_length(max_lines=400) == []


def test_exempt_paths_only_cover_files_over_hard_cap() -> None:
    """豁免表只应保留仍超过硬顶的文件，避免长期跳过门禁。"""
    for relative in check_layout.EXEMPT_RELATIVE_PATHS:
        target = check_layout.PKG / relative
        assert target.is_file(), f"豁免路径不存在: {relative}"
        line_count = len(target.read_text(encoding="utf-8").splitlines())
        assert line_count > 500, f"豁免路径已低于硬顶，应移出豁免表: {relative} ({line_count} 行)"


def test_check_file_length_ignores_seed_scripts(tmp_path: Path, monkeypatch) -> None:
    """scripts/ 下的 seed_*.py 属于数据脚本，不受行数门禁约束。"""
    monkeypatch.setattr(check_layout, "REPO", tmp_path)
    monkeypatch.setattr(check_layout, "PKG", tmp_path)
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "seed_demo.py").write_text("\n".join(["x = 1"] * 1600), encoding="utf-8")

    assert check_layout.check_file_length(max_lines=400) == []
