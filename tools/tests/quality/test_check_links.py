# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""活跃文档本地链接检查的回归测试。"""

from __future__ import annotations

from pathlib import Path

from tools.quality.contracts import check_links


def test_extract_links_ignores_external_and_pure_anchors(tmp_path: Path) -> None:
    """外部链接、纯锚点、mailto 不参与本地文件检查。"""
    doc = tmp_path / "doc.md"
    doc.write_text(
        "[a](other.md)\n[b](https://example.com/x)\n[c](#section)\n[d](mailto:a@b.c)\n",
        encoding="utf-8",
    )

    links = check_links.extract_links(doc.read_text(encoding="utf-8"))

    assert [link.target for link in links] == ["other.md"]


def test_check_file_reports_missing_relative_target(tmp_path: Path) -> None:
    """相对链接指向不存在文件时报告行号。"""
    doc = tmp_path / "doc.md"
    doc.write_text("# Doc\n\n[missing](nope.md)\n", encoding="utf-8")

    issues = check_links.check_file(doc)

    assert len(issues) == 1
    assert issues[0].line == 3
    assert "nope.md" in issues[0].message


def test_check_file_accepts_images_and_fragments(tmp_path: Path) -> None:
    """图片、带 #fragment 的链接按去掉 fragment 后的路径判定。"""
    (tmp_path / "img.png").write_bytes(b"png")
    (tmp_path / "other.md").write_text("# Other\n", encoding="utf-8")
    doc = tmp_path / "doc.md"
    doc.write_text("![x](img.png)\n[o](other.md#top)\n", encoding="utf-8")

    assert check_links.check_file(doc) == []


def test_check_file_decodes_percent_encoding(tmp_path: Path) -> None:
    """中文/空格路径的 %XX 编码应能解析到真实文件。"""
    (tmp_path / "中文 文档.md").write_text("# X\n", encoding="utf-8")
    doc = tmp_path / "doc.md"
    doc.write_text("[x](%E4%B8%AD%E6%96%87%20%E6%96%87%E6%A1%A3.md)\n", encoding="utf-8")

    assert check_links.check_file(doc) == []


def test_default_documents_exist() -> None:
    """默认扫描清单至少包含 README 与 docs/ 下的活跃文档。"""
    candidates = check_links.default_documents()

    assert check_links.REPO / "README.md" in candidates
    assert any(path.name == "操作指令集.md" for path in candidates)
