# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""ADR 索引生成与校验的回归测试。"""

from __future__ import annotations

from pathlib import Path

from tools.quality.contracts import check_adr


def _write_adr(directory: Path, filename: str, title: str, status: str = "已采纳") -> None:
    (directory / filename).write_text(
        f"# {title}\n\n**状态**：{status}  \n**日期**：2026-11-07\n",
        encoding="utf-8",
    )


def test_collect_adrs_sorts_and_extracts_titles(tmp_path: Path) -> None:
    """按编号排序，标题去掉 ADR-XXXX 前缀。"""
    _write_adr(tmp_path, "0002-second.md", "ADR-0002：第二个决策")
    _write_adr(tmp_path, "0001-first.md", "ADR-0001：第一个决策", status="已批准")

    adrs = check_adr.collect_adrs(tmp_path)

    assert [adr.number for adr in adrs] == ["0001", "0002"]
    assert adrs[0].title == "第一个决策"
    assert adrs[0].accepted is True
    assert adrs[1].title == "第二个决策"


def test_duplicate_number_is_an_error(tmp_path: Path) -> None:
    """同编号文件必须登记到豁免表，否则报错。"""
    _write_adr(tmp_path, "0002-a.md", "ADR-0002：A")
    _write_adr(tmp_path, "0002-b.md", "ADR-0002：B")

    errors = check_adr.validate(tmp_path)

    assert any("重复" in error for error in errors)


def test_superseded_duplicate_is_allowed(tmp_path: Path) -> None:
    """历史重复文件在豁免表中时不报错。"""
    _write_adr(tmp_path, "0002-a.md", "ADR-0002：A")
    _write_adr(tmp_path, "0002-b.md", "ADR-0002：B")

    errors = check_adr.validate(tmp_path, superseded={"0002-b.md": "0014"})

    assert errors == []


def test_render_index_contains_all_adrs_and_gap_note(tmp_path: Path) -> None:
    """生成的索引应包含每个 ADR 的链接，并注明空缺编号。"""
    _write_adr(tmp_path, "0001-first.md", "ADR-0001：第一个决策")
    _write_adr(tmp_path, "0003-third.md", "ADR-0003：第三个决策")

    adrs = check_adr.collect_adrs(tmp_path)
    block = check_adr.render_index(adrs)

    assert "| 0001 |" in block
    assert "| 0003 |" in block
    assert "0001-first.md" in block
    assert "0002" in block and "空缺" in block


def test_check_readme_reports_missing_block(tmp_path: Path) -> None:
    """README 缺少生成标记时给出可操作错误。"""
    _write_adr(tmp_path, "0001-first.md", "ADR-0001：第一个决策")
    readme = tmp_path / "README.md"
    readme.write_text("# ADR\n\n手写表格\n", encoding="utf-8")

    errors = check_adr.check_readme(tmp_path, readme)

    assert any("标记" in error for error in errors)


def test_check_readme_detects_stale_index(tmp_path: Path) -> None:
    """索引与文件不一致时失败。"""
    _write_adr(tmp_path, "0001-first.md", "ADR-0001：第一个决策")
    readme = tmp_path / "README.md"
    adrs = check_adr.collect_adrs(tmp_path)
    block = check_adr.render_index(adrs)
    readme.write_text(f"# ADR\n\n{check_adr.START_MARKER}\n{block}{check_adr.END_MARKER}\n", encoding="utf-8")

    assert check_adr.check_readme(tmp_path, readme) == []

    _write_adr(tmp_path, "0002-second.md", "ADR-0002：第二个决策")
    errors = check_adr.check_readme(tmp_path, readme)

    assert any("过期" in error for error in errors)


def test_real_repository_index_is_current() -> None:
    """仓库自身的 ADR README 必须与文件一致。"""
    assert check_adr.check_readme(check_adr.ADR_DIR, check_adr.README_PATH) == []
