#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""活跃文档本地链接检查。

只校验仓库内相对路径链接：外部 URL、纯锚点、``mailto:`` 等跳过。
代码块与行内代码中的示例链接不参与检查。

用法（仓库根目录）::

    python tools/quality/contracts/check_links.py
    python tools/quality/contracts/check_links.py docs/操作指令集.md README.md
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote

REPO = Path(__file__).resolve().parents[3]

_INLINE_LINK_RE = re.compile(r"!?\[[^\]]*\]\(\s*(<[^>\n]*>|[^)\s]+)(?:\s+(?:\"[^\"]*\"|'[^']*'))?\s*\)")
_INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
_EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "tel:", "data:", "ftp://", "file:", "//")
_FENCE_PREFIXES = ("```", "~~~")
_HISTORICAL_DOC_RE = re.compile(r"^会话接续手册-\d{4}-\d{2}\.md$")


@dataclass(frozen=True)
class Link:
    """文档中的一条本地链接。"""

    line: int
    target: str


@dataclass(frozen=True)
class Issue:
    """一条链接问题。"""

    line: int
    message: str


def extract_links(text: str) -> list[Link]:
    """提取文本中的本地链接（跳过代码块、行内代码与外部目标）。

    Args:
        text: Markdown 文本

    Returns:
        带行号的 :class:`Link` 列表
    """
    links: list[Link] = []
    in_fence = False
    for lineno, raw_line in enumerate(text.splitlines(), 1):
        stripped = raw_line.lstrip()
        if stripped.startswith(_FENCE_PREFIXES):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        line = _INLINE_CODE_RE.sub("", raw_line)
        for match in _INLINE_LINK_RE.finditer(line):
            target = match.group(1)
            if target.startswith("<") and target.endswith(">"):
                target = target[1:-1]
            if _is_external(target):
                continue
            links.append(Link(line=lineno, target=target))
    return links


def _is_external(target: str) -> bool:
    normalized = target.strip().lower()
    return not normalized or normalized.startswith("#") or normalized.startswith(_EXTERNAL_PREFIXES)


def check_file(path: Path, *, repo: Path = REPO) -> list[Issue]:
    """检查单个 Markdown 文件的本地链接是否都能解析。

    Args:
        path: Markdown 文件路径
        repo: 仓库根目录（用于解析以 ``/`` 开头的链接）

    Returns:
        :class:`Issue` 列表（空列表表示通过）
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    issues: list[Issue] = []
    for link in extract_links(text):
        target = link.target.split("#", 1)[0].split("?", 1)[0]
        if not target:
            continue
        target = unquote(target)
        candidate = Path(target)
        if candidate.is_absolute():
            resolved = candidate
        elif target.startswith("/"):
            resolved = repo / target.lstrip("/")
        else:
            resolved = path.parent / target
        if not resolved.exists():
            issues.append(Issue(line=link.line, message=f"链接目标不存在：{link.target}"))
    return issues


def default_documents() -> list[Path]:
    """返回默认扫描的活跃文档清单。

    Returns:
        去重后的 Markdown 文件列表
    """
    candidates: list[Path] = [
        REPO / "README.md",
        REPO / "README_zh.md",
        REPO / "tools" / "README.md",
        REPO / "framework" / "README.md",
    ]
    for directory in (REPO / "docs", REPO / "docs" / "adr", REPO / "docs" / "agents"):
        if directory.is_dir():
            candidates.extend(
                path for path in sorted(directory.glob("*.md")) if not _HISTORICAL_DOC_RE.match(path.name)
            )
    return [path for path in dict.fromkeys(candidates) if path.is_file()]


def _display(path: Path) -> str:
    try:
        return path.relative_to(REPO).as_posix()
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    """CLI 入口：检查指定或默认文档的本地链接。

    Returns:
        退出码（0 通过，1 失败）
    """
    parser = argparse.ArgumentParser(description="检查 Markdown 本地链接")
    parser.add_argument("documents", nargs="*", type=Path, help="待检查的 Markdown 文件（默认扫描活跃文档）")
    args = parser.parse_args(argv)

    documents = [path.resolve() for path in args.documents] if args.documents else default_documents()
    total = 0
    for document in documents:
        for issue in check_file(document):
            total += 1
            print(f"ERROR: {_display(document)}:{issue.line}: {issue.message}")
    if total:
        print(f"链接检查失败：{total} 个失效链接（扫描 {len(documents)} 个文件）。")
        return 1
    print(f"链接检查通过（扫描 {len(documents)} 个文件）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
