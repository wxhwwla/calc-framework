#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""
仓库布局门禁：目录宽度 ≤10、业务 .py ≤500 行。

用法（仓库根）：
    python tools/check_layout.py
    python tools/check_layout.py --max-lines 400
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PKG = REPO / "games" / "endfield"
SKIP_DIR_NAMES = frozenset({"__pycache__", ".pytest_cache", "dist", ".venv", "build"})
SKIP_FILE_SUFFIXES = (".pyc",)


def _iter_check_dirs(root: Path) -> list[Path]:
    out: list[Path] = []
    for path in [root, *root.rglob("*")]:
        if not path.is_dir():
            continue
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        out.append(path)
    return out


def check_directory_width(*, max_items: int = 10) -> list[str]:
    errors: list[str] = []
    scan_roots = [
        PKG / "gui_design",
        PKG / "calculation",
        PKG / "tests",
        PKG / "calc_engine/endfield/data",
        PKG / "data",
        PKG / "scripts",
    ]
    for scan_root in scan_roots:
        if not scan_root.is_dir():
            continue
        for directory in [scan_root, *scan_root.rglob("*")]:
            if not directory.is_dir():
                continue
            if any(part in SKIP_DIR_NAMES for part in directory.parts):
                continue
            children = [
                p
                for p in directory.iterdir()
                if p.name not in SKIP_DIR_NAMES and not p.name.endswith(SKIP_FILE_SUFFIXES)
            ]
            if len(children) > max_items:
                rel = directory.relative_to(REPO)
                errors.append(f"目录 {rel} 有 {len(children)} 个子项（上限 {max_items}）")
    return errors


def check_file_length(*, max_lines: int, hard_max: int = 500) -> list[str]:
    errors: list[str] = []
    for path in PKG.rglob("*.py"):
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        if path.parts[-2:] == ("scripts", path.name) and path.name.startswith("seed_"):
            continue
        try:
            count = sum(1 for _ in path.open(encoding="utf-8"))
        except OSError:
            continue
        limit = hard_max if "scripts" not in path.parts else hard_max * 3
        if count > limit:
            rel = path.relative_to(REPO)
            errors.append(f"文件 {rel} 有 {count} 行（硬上限 {limit}）")
        elif count > max_lines and "tests" not in path.parts:
            rel = path.relative_to(REPO)
            errors.append(f"文件 {rel} 有 {count} 行（建议 ≤{max_lines}）")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="检查代码布局约束")
    parser.add_argument("--max-items", type=int, default=10)
    parser.add_argument("--max-lines", type=int, default=400)
    parser.add_argument("--warn-only-lines", action="store_true", help="超长文件仅警告，不失败")
    args = parser.parse_args()

    width_errors = check_directory_width(max_items=args.max_items)
    line_issues = check_file_length(max_lines=args.max_lines)

    hard_line_errors = [e for e in line_issues if "硬上限" in e]
    soft_line_warnings = [e for e in line_issues if "建议" in e]

    for msg in width_errors:
        print(f"ERROR: {msg}")
    for msg in hard_line_errors:
        print(f"ERROR: {msg}")
    for msg in soft_line_warnings:
        print(f"WARN: {msg}")

    if width_errors or hard_line_errors:
        return 1
    if soft_line_warnings and not args.warn_only_lines:
        return 1
    print("布局检查通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
