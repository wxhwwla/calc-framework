#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""仓库布局门禁：目录子项数 ≤20（目标 ≤15）、业务 .py 文件行数 ≤500。

默认扫描全仓 Python 生产目录；历史超限登记在 ``layout_baseline.json``，
基线内只告警，新增超限或超过基线记录必须失败，复审日期过期同样失败。

用法（仓库根目录）::

    python tools/quality/check_layout.py
    python tools/quality/check_layout.py --max-lines 400
    python tools/quality/check_layout.py --scope endfield
    python tools/quality/check_layout.py --write-baseline
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ENDFIELD_PKG = REPO / "games" / "endfield"
PKG = ENDFIELD_PKG  # 向后兼容旧调用
BASELINE_PATH = REPO / "tools" / "quality" / "layout_baseline.json"
DEFAULT_REVIEW_DAYS = 90

SKIP_DIR_NAMES = frozenset(
    {
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "dist",
        "build",
        ".venv",
        "node_modules",
        "htmlcov",
        "output",
        "logs",
        "target",
    }
)
SKIP_FILE_SUFFIXES = (".pyc",)

# 见 docs/代码结构规范.md §5「豁免表」；路径相对 games/endfield/
EXEMPT_RELATIVE_PATHS = frozenset(
    {
        "calc/multiplicative_zones/final_attack_zone.py",
        "tests/calculation/test_multiplicative_zones.py",
        "tests/tools/test_bwiki_scout.py",
    }
)

_REPO_SCAN_ROOTS = (
    "framework/src",
    "games",
    "tools",
    "web/backend",
    "scripts",
    "utils",
    "extensions",
    "release_bundle",
    "installer",
)
_ENDFIELD_SCAN_ROOTS = ("calc", "data", "data_loading", "gui", "tests")


@dataclass(frozen=True)
class Violation:
    """单个目录或文件超限记录。"""

    kind: str
    path: Path
    actual: int
    limit: int
    hard: bool = False

    @property
    def message(self) -> str:
        """生成带仓库相对路径的可读描述。"""
        rel = _display_path(self.path)
        if self.kind == "directory":
            return f"目录 {rel} 有 {self.actual} 个子项（上限 {self.limit}）"
        if self.hard:
            return f"文件 {rel} 有 {self.actual} 行（硬上限 {self.limit}）"
        return f"文件 {rel} 有 {self.actual} 行（建议 ≤{self.limit}）"


def default_roots(scope: str = "repo") -> list[Path]:
    """返回指定范围的默认扫描根目录。"""
    if scope == "endfield":
        return [ENDFIELD_PKG / name for name in _ENDFIELD_SCAN_ROOTS]
    if scope != "repo":
        raise ValueError(f"未知扫描范围: {scope}")
    return [REPO / name for name in _REPO_SCAN_ROOTS]


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(REPO).as_posix()
    except ValueError:
        return str(path)


def _is_skipped(path: Path, root: Path) -> bool:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        parts = path.parts
    return any(part in SKIP_DIR_NAMES or (part.startswith(".") and part not in {".", ".."}) for part in parts)


def _is_exempt(path: Path) -> bool:
    try:
        relative = path.relative_to(ENDFIELD_PKG).as_posix()
    except ValueError:
        return False
    return relative in EXEMPT_RELATIVE_PATHS


def _iter_python_files(roots: list[Path]):
    seen: set[Path] = set()
    for root in roots:
        if not root.is_dir():
            continue
        for path in root.rglob("*.py"):
            if _is_skipped(path, root) or path in seen:
                continue
            seen.add(path)
            yield path


def check_directory_width(*, max_items: int = 20, roots: list[Path] | None = None) -> list[Violation]:
    """检查目录子项数是否超过上限。

    Args:
        max_items: 子项数上限
        roots: 扫描根目录；默认全仓 Python 生产目录

    Returns:
        超限记录列表
    """
    issues: list[Violation] = []
    seen: set[Path] = set()
    for scan_root in roots if roots is not None else default_roots():
        if not scan_root.is_dir():
            continue
        for directory in (scan_root, *scan_root.rglob("*")):
            if not directory.is_dir() or _is_skipped(directory, scan_root):
                continue
            if directory in seen:
                continue
            seen.add(directory)
            children = [
                child
                for child in directory.iterdir()
                if child.name not in SKIP_DIR_NAMES
                and not child.name.startswith(".")
                and not child.name.endswith(SKIP_FILE_SUFFIXES)
            ]
            if len(children) > max_items:
                issues.append(
                    Violation(
                        kind="directory",
                        path=directory,
                        actual=len(children),
                        limit=max_items,
                        hard=True,
                    )
                )
    return issues


def check_file_length(
    *,
    max_lines: int,
    hard_max: int = 500,
    roots: list[Path] | None = None,
) -> list[Violation]:
    """检查 Python 文件行数是否超过上限。

    Args:
        max_lines: 建议行数上限
        hard_max: 硬性行数上限（超出即报错；scripts/ 放宽到 3 倍）
        roots: 扫描根目录；默认全仓 Python 生产目录

    Returns:
        超限记录列表
    """
    issues: list[Violation] = []
    scan_roots = roots if roots is not None else default_roots()
    for path in _iter_python_files(scan_roots):
        if path.name.startswith("seed_") and "scripts" in path.parent.name:
            continue
        if _is_exempt(path):
            continue
        try:
            with path.open(encoding="utf-8", errors="replace") as handle:
                count = sum(1 for _ in handle)
        except OSError:
            continue
        limit = hard_max * 3 if "scripts" in path.parts else hard_max
        if count > limit:
            issues.append(Violation(kind="file", path=path, actual=count, limit=limit, hard=True))
        elif count > max_lines and "tests" not in path.parts:
            issues.append(Violation(kind="file", path=path, actual=count, limit=max_lines))
    return issues


def load_baseline(path: Path = BASELINE_PATH) -> dict:
    """读取布局基线；文件不存在时返回空基线。"""
    if not path.is_file():
        return {"files": {}, "directories": {}}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"布局基线格式错误: {path}")
    data.setdefault("files", {})
    data.setdefault("directories", {})
    return data


def _key(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.name


def _parse_date(value: object) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def evaluate_baseline(
    violations: list[Violation],
    baseline: dict,
    *,
    today: date | None = None,
    repo_root: Path = REPO,
) -> tuple[list[str], list[str]]:
    """按基线评估超限，返回 (错误列表, 告警列表)。"""
    today = today or date.today()
    errors: list[str] = []
    warnings: list[str] = []
    for violation in violations:
        section = "directories" if violation.kind == "directory" else "files"
        entry = baseline.get(section, {}).get(_key(violation.path, repo_root))
        if not isinstance(entry, dict):
            errors.append(f"{violation.message} — 未登记在布局基线中（新超限）")
            continue
        review_by = _parse_date(entry.get("review_by"))
        if review_by is None:
            errors.append(f"{violation.message} — 基线缺少合法 review_by")
        elif review_by < today:
            errors.append(
                f"{violation.message} — 基线豁免已过期（review_by {review_by.isoformat()}），请拆分或更新基线"
            )
        else:
            recorded = entry.get("lines" if violation.kind == "file" else "count")
            if not isinstance(recorded, int) or violation.actual > recorded:
                errors.append(f"{violation.message} — 超过基线记录（{recorded}）")
            else:
                warnings.append(f"{violation.message} — 基线豁免（复审日期 {review_by.isoformat()}）")
    return errors, warnings


def build_baseline(
    violations: list[Violation],
    *,
    today: date,
    review_days: int = DEFAULT_REVIEW_DAYS,
    repo_root: Path = REPO,
) -> dict:
    """把当前全部超限写成基线，供历史债分批复审。"""
    review_by = (today + timedelta(days=review_days)).isoformat()
    files: dict[str, dict] = {}
    directories: dict[str, dict] = {}
    for violation in violations:
        key = _key(violation.path, repo_root)
        if violation.kind == "directory":
            directories[key] = {"count": violation.actual, "review_by": review_by}
        else:
            files[key] = {"lines": violation.actual, "review_by": review_by}
    return {
        "generated": today.isoformat(),
        "review_by": review_by,
        "files": dict(sorted(files.items())),
        "directories": dict(sorted(directories.items())),
    }


def _collect(*, roots: list[Path], max_items: int, max_lines: int, hard_max: int) -> list[Violation]:
    return [
        *check_directory_width(max_items=max_items, roots=roots),
        *check_file_length(max_lines=max_lines, hard_max=hard_max, roots=roots),
    ]


def main(argv: list[str] | None = None) -> int:
    """CLI 入口：解析参数并执行布局检查。

    Returns:
        退出码（0 通过，1 失败）
    """
    parser = argparse.ArgumentParser(description="检查代码布局约束")
    scope_group = parser.add_mutually_exclusive_group()
    scope_group.add_argument("--scope", choices=("repo", "endfield"), default=None)
    scope_group.add_argument("--roots", nargs="+", type=Path, default=None)
    parser.add_argument("--max-items", type=int, default=20)
    parser.add_argument("--max-lines", type=int, default=400)
    parser.add_argument("--hard-max", type=int, default=500)
    parser.add_argument("--baseline", type=Path, default=BASELINE_PATH)
    parser.add_argument("--write-baseline", action="store_true")
    parser.add_argument("--baseline-review-days", type=int, default=DEFAULT_REVIEW_DAYS)
    parser.add_argument("--today", type=str, default=None, help=argparse.SUPPRESS)
    parser.add_argument("--warn-only-lines", action="store_true")
    args = parser.parse_args(argv)

    today = date.fromisoformat(args.today) if args.today else date.today()
    if args.roots:
        roots = [path.resolve() for path in args.roots]
        repo_root = Path(os.path.commonpath([str(p) for p in roots]))
    else:
        roots = default_roots(args.scope or "repo")
        repo_root = REPO

    scope_label = ", ".join(str(root.relative_to(REPO)) if root.is_relative_to(REPO) else str(root) for root in roots)
    print(f"扫描范围: {scope_label}（跳过 __pycache__/.venv/dist/build/target/node_modules/output 等）")

    violations = _collect(
        roots=roots,
        max_items=args.max_items,
        max_lines=args.max_lines,
        hard_max=args.hard_max,
    )

    if args.write_baseline:
        baseline = build_baseline(
            violations,
            today=today,
            review_days=args.baseline_review_days,
            repo_root=repo_root,
        )
        args.baseline.write_text(json.dumps(baseline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"已写入布局基线: {args.baseline}（{len(violations)} 项，复审日期 {baseline['review_by']}）")
        return 0

    baseline = load_baseline(args.baseline)
    errors, warnings = evaluate_baseline(violations, baseline, today=today, repo_root=repo_root)
    if args.warn_only_lines:
        downgraded = [error for error in errors if "建议 ≤" in error]
        errors = [error for error in errors if "建议 ≤" not in error]
        warnings.extend(downgraded)

    for message in errors:
        print(f"ERROR: {message}")
    for message in warnings:
        print(f"WARN: {message}")
    if errors:
        print(f"布局检查失败：{len(errors)} 个错误，{len(warnings)} 个基线内告警。")
        return 1
    print(f"布局检查通过（{len(warnings)} 个基线内告警）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
