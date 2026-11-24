#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""ADR 索引生成与校验。

索引块位于 ``docs/adr/README.md`` 的生成标记之间，内容完全由 ADR 文件推导：
编号、标题、状态与空缺编号。重复编号必须登记到 ``SUPERSEDED`` 豁免表，
否则检查失败。

用法（仓库根目录）::

    python tools/quality/contracts/check_adr.py
    python tools/quality/contracts/check_adr.py --write
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
ADR_DIR = REPO / "docs" / "adr"
README_PATH = ADR_DIR / "README.md"
START_MARKER = "<!-- ADR-INDEX:START -->"
END_MARKER = "<!-- ADR-INDEX:END -->"

# 历史重复编号：文件名 → 取代它的 ADR 编号
SUPERSEDED: dict[str, str] = {"0002-migrate-to-pyside6.md": "0014"}

_TITLE_RE = re.compile(r"^#\s*ADR-(\d{4})\s*[：:]\s*(.+?)\s*$")
_STATUS_RE = re.compile(r"(?:\*\*)?状态(?:\*\*)?\s*[：:]\s*(.+)")
_STATUS_HEADING_RE = re.compile(r"^##\s*状态\s*$", re.MULTILINE)
_ACCEPTED_MARKERS = ("已采纳", "已批准", "已实现", "已接受", "生效")


@dataclass(frozen=True)
class Adr:
    """一个 ADR 文件的元数据。"""

    number: str
    title: str
    accepted: bool
    filename: str
    status: str


def _parse_title(path: Path, text: str) -> tuple[str, str]:
    first_line = text.splitlines()[0] if text else ""
    match = _TITLE_RE.match(first_line)
    if match:
        return match.group(1), match.group(2)
    number = path.stem.split("-", 1)[0]
    if not (len(number) == 4 and number.isdigit()):
        return "", first_line.lstrip("# ").strip()
    return number, first_line.lstrip("# ").strip()


def _parse_status(text: str) -> str:
    match = _STATUS_RE.search(text)
    if match:
        return match.group(1).strip()
    heading = _STATUS_HEADING_RE.search(text)
    if heading:
        for line in text[heading.end() :].splitlines():
            stripped = line.strip()
            if stripped:
                return stripped
    return ""


def collect_adrs(directory: Path = ADR_DIR, *, superseded: dict[str, str] | None = None) -> list[Adr]:
    """收集目录下的 ADR，按编号排序并排除豁免表中的历史文件。

    Args:
        directory: ADR 目录
        superseded: 历史重复文件豁免表（文件名 → 取代编号）

    Returns:
        按编号、文件名排序的 :class:`Adr` 列表
    """
    mapping = superseded or {}
    adrs: list[Adr] = []
    if not directory.is_dir():
        return adrs
    for path in sorted(directory.glob("*.md")):
        if path.name.lower() == "readme.md" or path.name in mapping:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        number, title = _parse_title(path, text)
        status = _parse_status(text)
        accepted = any(marker in status for marker in _ACCEPTED_MARKERS)
        adrs.append(
            Adr(
                number=number,
                title=title,
                accepted=accepted,
                filename=path.name,
                status=status,
            )
        )
    adrs.sort(key=lambda adr: (adr.number, adr.filename))
    return adrs


def validate(directory: Path = ADR_DIR, *, superseded: dict[str, str] | None = None) -> list[str]:
    """校验 ADR 文件：编号可解析且不重复。

    Args:
        directory: ADR 目录
        superseded: 历史重复文件豁免表；为 ``None`` 时使用 :data:`SUPERSEDED`

    Returns:
        错误信息列表（空列表表示通过）
    """
    mapping = SUPERSEDED if superseded is None else superseded
    errors: list[str] = []
    seen: dict[str, str] = {}
    for adr in collect_adrs(directory, superseded=mapping):
        if not adr.number:
            errors.append(f"{adr.filename} 无法解析 ADR 编号")
            continue
        if adr.number in seen:
            errors.append(
                f"ADR 编号重复：{seen[adr.number]} 与 {adr.filename} 都是 {adr.number}；请重编号或在 SUPERSEDED 中登记"
            )
        else:
            seen[adr.number] = adr.filename
    return errors


def render_index(adrs: list[Adr], *, superseded: dict[str, str] | None = None) -> str:
    """把 ADR 列表渲染为 Markdown 索引表。

    Args:
        adrs: ADR 列表（通常来自 :func:`collect_adrs`）
        superseded: 历史重复文件豁免表，用于生成底部说明

    Returns:
        以换行结尾的 Markdown 文本
    """
    lines = ["| 编号 | 状态 | 说明 |", "|------|:----:|------|"]
    rows: list[tuple[int, str]] = []
    for adr in adrs:
        symbol = "✅" if adr.accepted else "—"
        order = int(adr.number) if adr.number.isdigit() else 10**9
        rows.append((order, f"| {adr.number} | {symbol} | [{adr.title}]({adr.filename}) |"))

    numbers = sorted(int(adr.number) for adr in adrs if adr.number.isdigit())
    if numbers:
        present = set(numbers)
        for missing in range(numbers[0], numbers[-1] + 1):
            if missing not in present:
                rows.append((missing, f"| {missing:04d} | — | **空缺**（编号预留，未使用） |"))
    lines.extend(row for _, row in sorted(rows, key=lambda item: item[0]))

    if superseded:
        lines.append("")
        for filename, replacement in sorted(superseded.items()):
            lines.append(f"**注意**：`{filename}` 为历史重复编号文件，已被 ADR-{replacement} 取代，不列入索引。")
    return "\n".join(lines) + "\n"


def _existing_superseded(directory: Path, mapping: dict[str, str]) -> dict[str, str]:
    """只保留目录中真实存在的豁免文件，便于在临时目录中复用同一套检查。"""
    return {filename: replacement for filename, replacement in mapping.items() if (directory / filename).is_file()}


def check_readme(
    directory: Path = ADR_DIR,
    readme: Path = README_PATH,
    *,
    superseded: dict[str, str] | None = None,
) -> list[str]:
    """校验 README 中的生成索引是否与 ADR 文件一致。

    Args:
        directory: ADR 目录
        readme: 索引 README 路径
        superseded: 历史重复文件豁免表；为 ``None`` 时使用 :data:`SUPERSEDED`

    Returns:
        错误信息列表（空列表表示通过）
    """
    mapping = _existing_superseded(directory, SUPERSEDED if superseded is None else superseded)
    errors = validate(directory, superseded=mapping)
    if not readme.is_file():
        return [*errors, f"缺少 ADR 索引文件：{readme}"]
    text = readme.read_text(encoding="utf-8", errors="replace")
    if START_MARKER not in text or END_MARKER not in text:
        return [*errors, f"{readme} 缺少生成标记 {START_MARKER} / {END_MARKER}，请运行 --write"]
    actual = text.split(START_MARKER, 1)[1].split(END_MARKER, 1)[0].strip("\n")
    expected = render_index(collect_adrs(directory, superseded=mapping), superseded=mapping).strip("\n")
    if actual != expected:
        errors.append(f"{readme} 的 ADR 索引已过期，请运行 python tools/quality/contracts/check_adr.py --write")
    return errors


def write_readme(
    directory: Path = ADR_DIR,
    readme: Path = README_PATH,
    *,
    superseded: dict[str, str] | None = None,
) -> None:
    """重新生成 README 中的索引块；缺少标记时追加到文末。"""
    mapping = _existing_superseded(directory, SUPERSEDED if superseded is None else superseded)
    block = render_index(collect_adrs(directory, superseded=mapping), superseded=mapping)
    text = readme.read_text(encoding="utf-8") if readme.is_file() else "# 架构决策记录（ADR）\n"
    if START_MARKER in text and END_MARKER in text:
        head, rest = text.split(START_MARKER, 1)
        _, tail = rest.split(END_MARKER, 1)
        text = f"{head}{START_MARKER}\n{block}{END_MARKER}{tail}"
    else:
        text = f"{text.rstrip()}\n\n## ADR 索引\n\n{START_MARKER}\n{block}{END_MARKER}\n"
    readme.write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    """CLI 入口：校验或重写 ADR 索引。

    Returns:
        退出码（0 通过，1 失败）
    """
    parser = argparse.ArgumentParser(description="校验 ADR 编号与索引")
    parser.add_argument("--adr-dir", type=Path, default=ADR_DIR)
    parser.add_argument("--readme", type=Path, default=README_PATH)
    parser.add_argument("--write", action="store_true", help="重写 README 中的索引块")
    args = parser.parse_args(argv)

    if args.write:
        write_readme(args.adr_dir, args.readme)
        print(f"已更新 ADR 索引：{args.readme}")
        return 0

    errors = check_readme(args.adr_dir, args.readme)
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        print(f"ADR 检查失败：{len(errors)} 个错误。")
        return 1
    print("ADR 检查通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
