# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""MCP 项目作用域 — 路径安全测试。"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from tools.calc_mcp.safety import ProjectScope, ScopeError


@pytest.fixture
def scope(tmp_path: Path) -> ProjectScope:
    (tmp_path / "framework" / "adapters").mkdir(parents=True)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "guide.md").write_text("指南", encoding="utf-8")
    return ProjectScope(tmp_path)


def test_resolve_relative_path(scope: ProjectScope, tmp_path: Path) -> None:
    assert scope.resolve("docs/guide.md") == (tmp_path / "docs" / "guide.md").resolve()


@pytest.mark.parametrize("bad", ["../outside.txt", "..\\outside.txt", "E:\\outside.txt", "docs/\x00bad"])
def test_resolve_rejects_escape(scope: ProjectScope, bad: str) -> None:
    with pytest.raises(ScopeError):
        scope.resolve(bad)


def test_resolve_must_exist(scope: ProjectScope) -> None:
    with pytest.raises(ScopeError, match="不存在"):
        scope.resolve("docs/missing.md", must_exist=True)


def test_adapter_dir_accepts_valid_id(scope: ProjectScope, tmp_path: Path) -> None:
    adapter = tmp_path / "framework" / "adapters" / "demo"
    adapter.mkdir()

    assert scope.adapter_dir("demo") == adapter.resolve()


@pytest.mark.parametrize("bad", ["", "../demo", "a/b", "_template", "-bad", "a" * 65])
def test_adapter_dir_rejects_invalid_id(scope: ProjectScope, bad: str) -> None:
    with pytest.raises(ScopeError):
        scope.adapter_dir(bad)


def test_adapters_dir_must_stay_inside_root(tmp_path: Path) -> None:
    with pytest.raises(ScopeError):
        ProjectScope(tmp_path, adapters_dir=tmp_path.parent / "adapters")


def test_write_text_creates_parents_and_refuses_overwrite(scope: ProjectScope, tmp_path: Path) -> None:
    target = scope.resolve("framework/adapters/demo/ui/layout.json")

    written = scope.write_text(target, "{}", overwrite=False)
    assert written == 2
    assert target.read_text(encoding="utf-8") == "{}"

    with pytest.raises(ScopeError, match="已存在"):
        scope.write_text(target, "[]", overwrite=False)

    scope.write_text(target, "[]", overwrite=True)
    assert target.read_text(encoding="utf-8") == "[]"


def test_write_text_rejects_extension_and_oversize(scope: ProjectScope) -> None:
    target = scope.resolve("framework/adapters/demo/run.exe")
    with pytest.raises(ScopeError, match="扩展名"):
        scope.write_text(target, "x", overwrite=True)

    json_target = scope.resolve("framework/adapters/demo/big.json")
    with pytest.raises(ScopeError, match="过大"):
        scope.write_text(json_target, "x" * 100, overwrite=True, max_bytes=10)


def test_read_text_truncates(scope: ProjectScope) -> None:
    target = scope.resolve("docs/guide.md")
    content, truncated = scope.read_text(target, max_bytes=3)
    assert content == "指"
    assert truncated is True

    content, truncated = scope.read_text(target)
    assert content == "指南"
    assert truncated is False


def test_read_text_range_pages_without_splitting_utf8(scope: ProjectScope) -> None:
    """分页读取必须在 UTF-8 字符边界停下，拼接后与原文一致。"""
    target = scope.resolve("docs/guide.md")  # “指南” = 6 字节

    first = scope.read_text_range(target, offset=0, max_bytes=2)
    text, next_offset, truncated, total = first
    assert text == "指"
    assert next_offset == 3
    assert truncated is True
    assert total == 6

    text, next_offset, truncated, total = scope.read_text_range(target, offset=3, max_bytes=2)
    assert text == "南"
    assert next_offset is None
    assert truncated is False
    assert total == 6


def test_read_text_range_offset_past_eof(scope: ProjectScope) -> None:
    target = scope.resolve("docs/guide.md")

    assert scope.read_text_range(target, offset=999, max_bytes=10) == ("", None, False, 6)


def test_read_text_range_rejects_bad_arguments(scope: ProjectScope) -> None:
    target = scope.resolve("docs/guide.md")

    with pytest.raises(ScopeError, match="offset"):
        scope.read_text_range(target, offset=-1, max_bytes=10)
    with pytest.raises(ScopeError, match="max_bytes"):
        scope.read_text_range(target, offset=0, max_bytes=0)


def test_symlink_escape_is_rejected(scope: ProjectScope, tmp_path: Path) -> None:
    outside = tmp_path.parent / "mcp-outside-target"
    outside.write_text("secret", encoding="utf-8")
    link = tmp_path / "docs" / "link.txt"
    try:
        os.symlink(outside, link)
    except (OSError, NotImplementedError):
        pytest.skip("当前环境不允许创建符号链接")

    with pytest.raises(ScopeError):
        scope.resolve("docs/link.txt")
