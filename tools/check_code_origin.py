#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 生成代码来源/版权检测工具。

运行在仓库根目录：
    python tools/check_code_origin.py

运行在 devtool 子命令：
    python devtool.py check-origin

四种检测器：
1. LicenseHeaderChecker  — 缺失许可证头部
2. InternalDupChecker   — 内部代码重复（跨文件完全相同的行块）
3. SuspiciousPatternChecker — 可疑复制痕迹（外部项目版权声明、搬运注释、未改写的 import）
4. GitDiffChecker       — Git 变更分析（新增文件缺头部、超大 diff）

CI 用法：--ci 输出 JSON Lines（每行一个 Issue），0 = 通过，非 0 = 有警告/错误。
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]

# ── 跳过规则 ──────────────────────────────────────────

SKIP_DIRS = frozenset({
    ".git", "__pycache__", ".pytest_cache", ".venv", "build",
    "dist", ".egg-info", "node_modules", "venv", ".trae",
})
SKIP_FILE_SUFFIXES = (".pyc", ".pyo", ".so", ".pyd", ".gitkeep")
SKIP_FILE_NAMES = frozenset({"__init__.py", "conftest.py", "setup.py"})

# 已知的外部项目版权声明关键词
SUSPICIOUS_COPYRIGHT_KEYWORDS = [
    "Copyright (c)", "Copyright (C)", "All rights reserved",
    "This file is part of", "This program is free software",
    "General Public License", "GNU General Public License",
    "from the authors of", "Code originally from",
    "Copied from", "Adapted from",
    # 非本项目声明的具体许可证
    "Apache License, Version 2.0",
    "Licensed under the Apache License",
    "MIT License", "BSD License",
    "SPDX-License-Identifier",
]

# 已知外部项目的 import 指纹（当这些 import 出现在非 `adapters/` 时可能可疑）
KNOWN_EXTERNAL_IMPORTS = [
    "torch", "tensorflow", "transformers", "openai",
    "fastapi", "flask", "django", "numpy",
    "pandas", "scipy", "matplotlib", "selenium",
    "requests", "httpx", "aiohttp",
]

# 本项目的许可证头部模板
ACCEPTED_LICENSE_HEADERS = [
    # SPDX 标准头部
    re.compile(r"# SPDX-License-Identifier:\s*MIT"),
    re.compile(r"# SPDX-License-Identifier:\s*Apache-2\.0"),
    re.compile(r"# SPDX-License-Identifier:\s*GPL-3\.0-or-later"),
    re.compile(r"# SPDX-License-Identifier:\s*BSD-3-Clause"),
    # 常规版权头部
    re.compile(r"# Copyright\s+\d{4}[\s,\d]*\s+.*"),
    re.compile(r"# All rights reserved"),
]

# ── Issue 数据模型 ─────────────────────────────────────


@dataclass
class Issue:
    severity: str  # "error" | "warning" | "info"
    checker: str
    file: str
    line: int
    message: str
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity,
            "checker": self.checker,
            "file": self.file,
            "line": self.line,
            "message": self.message,
            "detail": self.detail,
        }

    def __str__(self) -> str:
        level = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(self.severity, "?")
        return f"{level} [{self.checker}] {self.file}:{self.line} — {self.message}"


# ── 工具 ──────────────────────────────────────────────


def _iter_py_files(root: Path | None = None) -> list[Path]:
    """递归收集所有 .py 文件（跳过 SKIP_DIRS）。"""
    if root is None:
        root = REPO
    files: list[Path] = []
    for path in root.rglob("*.py"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name in SKIP_FILE_NAMES:
            continue
        files.append(path)
    return files


def _read_lines(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8").splitlines(keepends=True)
    except (OSError, UnicodeDecodeError):
        return []


# ── 检测器 1: LicenseHeaderChecker ───────────────────


class LicenseHeaderChecker:
    """检查 .py 文件是否包含有效的许可证头部。"""

    def __init__(self, root: Path | None = None):
        self.root = root or REPO

    def run(self) -> list[Issue]:
        issues: list[Issue] = []
        for path in _iter_py_files(self.root):
            if self._is_generated(path):
                continue
            lines = _read_lines(path)
            if not lines:
                continue
            if not self._has_license_header(lines):
                rel = path.relative_to(self.root)
                issues.append(Issue(
                    severity="warning",
                    checker="license-header",
                    file=str(rel),
                    line=1,
                    message="文件缺少许可证头部声明",
                    detail="建议添加 SPDX-License-Identifier 或版权声明（例如 '# SPDX-License-Identifier: MIT'）",
                ))
        return issues

    @staticmethod
    def _is_generated(path: Path) -> bool:
        """判断是否为自动生成的文件。"""
        name = path.name
        if name.startswith("_version") or name == "version.py":
            return True
        return False

    @staticmethod
    def _has_license_header(lines: list[str]) -> bool:
        """检查文件开头 15 行内是否有许可证头部。"""
        for line in lines[:15]:
            stripped = line.strip()
            for pattern in ACCEPTED_LICENSE_HEADERS:
                if pattern.search(stripped):
                    return True
        return False


# ── 检测器 2: InternalDupChecker ─────────────────────


class InternalDupChecker:
    """检测内部代码重复：跨文件完全相同的行块。"""

    MIN_DUP_LINES = 6  # ≥6 行连续完全相同才报告
    MAX_DUP_REPORT = 3  # 每个重复块最多报 3 个位置

    def __init__(self, root: Path | None = None):
        self.root = root or REPO

    def run(self) -> list[Issue]:
        issues: list[Issue] = []
        files = _iter_py_files(self.root)

        # 构建行指纹索引：指纹 → [(file, lineno, line_text)]
        index: dict[int, list[tuple[Path, int, str]]] = defaultdict(list)
        for path in files:
            rel = path.relative_to(self.root)
            lines = _read_lines(path)
            for lineno, raw in enumerate(lines, 1):
                fingerprint = self._line_fingerprint(raw)
                if fingerprint:
                    index[fingerprint].append((path, lineno, raw.strip()))

        # 找出跨文件的行指纹匹配（同一指纹出现在 ≥2 个文件中）
        dup_candidates: defaultdict[int, list[tuple[Path, int, str]]] = defaultdict(list)
        for fp, locations in index.items():
            seen_files: set[Path] = {loc[0] for loc in locations}
            if len(seen_files) >= 2:
                dup_candidates[fp] = locations

        # 查找连续重复块
        visited: set[tuple[Path, int]] = set()
        for path in files:
            lines = _read_lines(path)
            lineno = 1
            while lineno <= len(lines):
                if (path, lineno) in visited:
                    lineno += 1
                    continue
                # 尝试扩展匹配块
                block: list[str] = []
                match_locations: list[tuple[Path, int, str]] = []
                jump = lineno
                while jump <= len(lines):
                    fp = self._line_fingerprint(lines[jump - 1])
                    if not fp:
                        break
                    if fp in dup_candidates:
                        locs = [loc for loc in dup_candidates[fp]
                                if loc[0] != path]
                        if locs:
                            block.append(lines[jump - 1].strip())
                            for loc in locs:
                                if loc not in match_locations:
                                    match_locations.append(loc)
                            visited.add((path, jump))
                            jump += 1
                            continue
                    break

                if len(block) >= self.MIN_DUP_LINES:
                    # 去重匹配位置
                    seen_files_for_block: set[Path] = set()
                    for loc in match_locations:
                        seen_files_for_block.add(loc[0])
                    other_files = [str(loc[0].relative_to(self.root))
                                   for loc in match_locations[:self.MAX_DUP_REPORT]
                                   if loc[0].relative_to(self.root)]
                    other_files = list(dict.fromkeys(other_files))  # 去重保持顺序

                    rel = path.relative_to(self.root)
                    issues.append(Issue(
                        severity="warning" if len(block) >= 10 else "info",
                        checker="internal-dup",
                        file=str(rel),
                        line=lineno,
                        message=f"内部代码重复：{len(block)} 行连续相同代码",
                        detail=f"同时出现在: {', '.join(other_files[:5])}",
                    ))

                lineno = jump

        return issues

    @staticmethod
    def _line_fingerprint(line: str) -> int:
        """计算行指纹（忽略缩进空白）。"""
        stripped = line.strip()
        # 跳过注释/空行/import/from
        if not stripped or stripped.startswith("#") or stripped.startswith("import "):
            return 0
        if stripped.startswith("from ") and "import" in stripped:
            return 0
        # 跳过只有装饰器和 def 的行
        if stripped.startswith("@") or stripped.startswith("def ") or stripped.startswith("class "):
            return 0
        if stripped in ("'''", '"""', "pass", "..."):
            return 0
        return hash(stripped)


# ── 检测器 3: SuspiciousPatternChecker ──────────────


class SuspiciousPatternChecker:
    """检测外部版权痕迹、搬运注释、未改写的 import。"""

    def __init__(self, root: Path | None = None):
        self.root = root or REPO

    def run(self) -> list[Issue]:
        issues: list[Issue] = []
        for path in _iter_py_files(self.root):
            rel = path.relative_to(self.root)
            lines = _read_lines(path)
            if not lines:
                continue
            issues.extend(self._check_copyright(rel, lines))
            issues.extend(self._check_external_imports(rel, lines))
            issues.extend(self._check_suspicious_comments(rel, lines))
        return issues

    @staticmethod
    def _check_copyright(rel: Path, lines: list[str]) -> list[Issue]:
        """检查是否有本项目之外的版权声明。"""
        issues: list[Issue] = []
        for lineno, raw in enumerate(lines, 1):
            stripped = raw.strip()
            for keyword in SUSPICIOUS_COPYRIGHT_KEYWORDS:
                if keyword.lower() in stripped.lower():
                    # 判断是否为本项目声明的版权
                    if "endfield_damage_calculator" in stripped.lower():
                        continue
                    if "solo" in stripped.lower():
                        continue
                    if keyword == "Copyright (c)" and "2026" in stripped:
                        continue  # 本项目年份
                    issues.append(Issue(
                        severity="warning",
                        checker="suspicious-copyright",
                        file=str(rel),
                        line=lineno,
                        message=f"发现可能的外部版权声明：{stripped[:80]}",
                        detail=f"匹配关键词: {keyword}",
                    ))
                    break  # 一行只报一次
        return issues

    @staticmethod
    def _check_external_imports(rel: Path, lines: list[str]) -> list[Issue]:
        """检查非标准库的 import 是否可疑。"""
        issues: list[Issue] = []
        for lineno, raw in enumerate(lines, 1):
            stripped = raw.strip()
            for known_pkg in KNOWN_EXTERNAL_IMPORTS:
                if known_pkg in stripped and (
                    stripped.startswith("import ") or stripped.startswith("from ")
                ):
                    issues.append(Issue(
                        severity="info",
                        checker="external-import",
                        file=str(rel),
                        line=lineno,
                        message=f"引入外部包：{stripped[:80]}",
                        detail=f"来源: {known_pkg}",
                    ))
                    break
        return issues

    @staticmethod
    def _check_suspicious_comments(rel: Path, lines: list[str]) -> list[Issue]:
        """检查搬运/改编标记注释。"""
        issues: list[Issue] = []
        patterns = [
            r"(?:Copied|Copied?)\s+(?:from|off)",
            r"Adapted\s+(?:from|off)",
            r"Taken\s+(?:from|off)",
            r"Originally\s+(?:written|created|from)",
            r"Port(?:ed)?\s+(?:from|to)",
            r"Translate(?:d)?\s+from",
            r"Source:\s*https?://",
            r"See\s+https?://",
            r"Reference:\s*https?://",
        ]
        compiled = [re.compile(p, re.IGNORECASE) for p in patterns]

        for lineno, raw in enumerate(lines, 1):
            stripped = raw.strip()
            if not stripped.startswith("#"):
                continue
            for pat in compiled:
                if pat.search(stripped):
                    issues.append(Issue(
                        severity="info",
                        checker="suspicious-comment",
                        file=str(rel),
                        line=lineno,
                        message=f"发现搬运/改编标记：{stripped[:80]}",
                    ))
                    break
        return issues


# ── 检测器 4: GitDiffChecker ─────────────────────────


class GitDiffChecker:
    """分析 Git 变更中的版权风险。"""

    def __init__(self, root: Path | None = None, *, since: str | None = None):
        self.root = root or REPO
        self.since = since  # git diff 基准，例如 "HEAD~1" 或 "origin/main"

    def run(self) -> list[Issue]:
        issues: list[Issue] = []
        diff_stat = self._get_diff_stat()
        if not diff_stat:
            return [Issue(
                severity="info",
                checker="git-diff",
                file="(root)",
                line=0,
                message="未检测到 Git 变更（不是 Git 仓库或无历史提交）",
            )]

        issues.extend(self._check_new_files())
        issues.extend(self._check_large_diffs(diff_stat))
        return issues

    def _get_diff_stat(self) -> dict[str, dict[str, int]]:
        """返回 {filepath: {'added': N, 'deleted': M}}。"""
        since = self.since or self._default_since()
        try:
            result = subprocess.run(
                ["git", "diff", "--numstat", since],
                capture_output=True, text=True, cwd=self.root,
                timeout=30,
            )
        except (subprocess.SubprocessError, FileNotFoundError):
            return {}

        stats: dict[str, dict[str, int]] = {}
        for line in result.stdout.splitlines():
            parts = line.split("\t")
            if len(parts) >= 3:
                added_str, deleted_str, path = parts[0], parts[1], parts[2]
                try:
                    added = int(added_str) if added_str != "-" else 0
                    deleted = int(deleted_str) if deleted_str != "-" else 0
                except ValueError:
                    continue
                stats[path] = {"added": added, "deleted": deleted}
        return stats

    def _default_since(self) -> str:
        """默认基准：HEAD~1 或初始提交。"""
        try:
            subprocess.run(
                ["git", "rev-parse", "HEAD~1"],
                capture_output=True, cwd=self.root, timeout=10,
                check=True,
            )
            return "HEAD~1"
        except subprocess.SubprocessError:
            return "--root"

    def _check_new_files(self) -> list[Issue]:
        """检查文件是否缺少必要的版权头部。"""
        issues: list[Issue] = []
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "--diff-filter=A",
                 self.since or self._default_since()],
                capture_output=True, text=True, cwd=self.root, timeout=30,
            )
        except subprocess.SubprocessError:
            return issues

        checker = LicenseHeaderChecker(self.root)
        for filename in result.stdout.splitlines():
            if not filename.endswith(".py"):
                continue
            path = self.root / filename
            if not path.exists():
                continue
            rel = Path(filename)
            lines = _read_lines(path)
            if lines and not checker._has_license_header(lines):
                issues.append(Issue(
                    severity="error",
                    checker="git-new-file",
                    file=filename,
                    line=1,
                    message="新增 .py 文件缺少许可证头部",
                    detail="所有新增源文件应包含 SPDX 许可证标识符或版权声明",
                ))
        return issues

    def _check_large_diffs(self, stats: dict[str, dict[str, int]]) -> list[Issue]:
        """报告超大 diff（可能为批量搬运）。"""
        issues: list[Issue] = []
        for path, stat in stats.items():
            if stat["added"] > 500:
                issues.append(Issue(
                    severity="warning",
                    checker="git-large-diff",
                    file=path,
                    line=0,
                    message=f"单次变更新增 {stat['added']} 行（>500），请确认代码来源合规",
                    detail="大块新增代码应附有来源声明和许可证标识",
                ))
            elif stat["added"] > 200:
                issues.append(Issue(
                    severity="info",
                    checker="git-large-diff",
                    file=path,
                    line=0,
                    message=f"单次变更新增 {stat['added']} 行（>200），建议检查代码来源",
                ))
        return issues


# ── 运行器 ─────────────────────────────────────────────


def run_all(
    root: Path | None = None,
    *,
    ci: bool = False,
    since: str | None = None,
    skip_checks: list[str] | None = None,
) -> list[Issue]:
    all_issues: list[Issue] = []

    checkers: dict[str, Any] = {
        "license-header": LicenseHeaderChecker(root),
        "internal-dup": InternalDupChecker(root),
        "suspicious": SuspiciousPatternChecker(root),
        "git-diff": GitDiffChecker(root, since=since),
    }

    skip = set(skip_checks or [])

    for name, checker in checkers.items():
        if name in skip:
            continue
        try:
            all_issues.extend(checker.run())
        except Exception as exc:
            all_issues.append(Issue(
                severity="error",
                checker=name,
                file="(internal)",
                line=0,
                message=f"检测器异常: {exc}",
            ))

    return all_issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="AI 生成代码来源/版权检测工具",
    )
    parser.add_argument(
        "--ci", action="store_true",
        help="CI 模式：输出 JSON Lines, 仅 exit code 区分通过/不通过",
    )
    parser.add_argument(
        "--since", default=None,
        help="Git diff 基准（默认 HEAD~1）",
    )
    parser.add_argument(
        "--skip", nargs="*", default=[],
        help="跳过的检测器（license-header / internal-dup / suspicious / git-diff）",
    )
    parser.add_argument(
        "--root", default=None,
        help="仓库根目录（默认自动检测）",
    )

    args = parser.parse_args(argv)
    root = Path(args.root).resolve() if args.root else REPO

    issues = run_all(
        root=root,
        ci=args.ci,
        since=args.since,
        skip_checks=args.skip or None,
    )

    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]
    infos = [i for i in issues if i.severity == "info"]

    if args.ci:
        for issue in issues:
            print(json.dumps(issue.to_dict(), ensure_ascii=False))
        return 1 if errors or warnings else 0

    # 非 CI 模式：人类友好输出
    for issue in issues:
        print(issue)

    print()
    print(f"总计: {len(issues)} 项")
    print(f"  ❌ Error:   {len(errors)}")
    print(f"  ⚠️ Warning: {len(warnings)}")
    print(f"  ℹ️ Info:    {len(infos)}")

    return 1 if errors or warnings else 0


if __name__ == "__main__":
    sys.exit(main())
