#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""只读扫描 Git 历史对象，列出大文件与构建产物，供维护者评估。

本工具**不会**重写历史、删除对象或执行任何写操作；输出用于
``docs/仓库历史清理评估.md`` 的复核记录。

用法（仓库根目录）::

    python tools/quality/supply_chain/scan_git_history.py
    python tools/quality/supply_chain/scan_git_history.py --json-out history-report.json
    python tools/quality/supply_chain/scan_git_history.py --fail-on-suspicious
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DEFAULT_THRESHOLD_BYTES = 4 * 1024 * 1024
_ARTIFACT_PATTERN = re.compile(
    r"(^|/)(dist|build|node_modules|target|__pycache__)/"
    r"|\.(pyz|pyc|exe|dll|so|dylib|whl|7z)$"
    r"|\.(zip|tar\.gz)$",
    re.IGNORECASE,
)


def parse_rev_list(text: str) -> dict[str, str]:
    """解析 ``git rev-list --objects --all`` 输出为 sha → 路径。"""
    entries: dict[str, str] = {}
    for line in text.splitlines():
        line = line.rstrip("\r")
        if not line:
            continue
        sha, _, path = line.partition(" ")
        entries.setdefault(sha, path)
    return entries


def parse_batch_check(text: str) -> dict[str, dict]:
    """解析 ``git cat-file --batch-check`` 输出为 sha → {type, size}。"""
    entries: dict[str, dict] = {}
    for line in text.splitlines():
        parts = line.strip().split()
        if len(parts) < 3 or parts[1] == "missing":
            continue
        try:
            size = int(parts[2])
        except ValueError:
            continue
        entries[parts[0]] = {"type": parts[1], "size": size}
    return entries


def find_suspicious(entries: list[dict], *, threshold_bytes: int) -> list[dict]:
    """筛出大文件或路径命中构建产物模式的 blob。"""
    suspicious: list[dict] = []
    for entry in entries:
        if entry.get("type") != "blob":
            continue
        reasons: list[str] = []
        if entry["size"] > threshold_bytes:
            reasons.append("large")
        if _ARTIFACT_PATTERN.search(entry.get("path", "")):
            reasons.append("build-artifact")
        if reasons:
            suspicious.append({**entry, "reasons": reasons})
    return sorted(suspicious, key=lambda item: item["size"], reverse=True)


def _build_report(entries: list[dict], *, repository: Path, threshold_bytes: int) -> dict:
    suspicious = find_suspicious(entries, threshold_bytes=threshold_bytes)
    return {
        "repository": str(repository),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "history_rewrite": False,
        "threshold_bytes": threshold_bytes,
        "object_count": len(entries),
        "total_object_bytes": sum(entry["size"] for entry in entries),
        "suspicious_count": len(suspicious),
        "large_objects": suspicious,
    }


def _git(repo: Path, args: list[str], *, input_text: str | None = None) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), "-c", "core.quotePath=false", *args],
        input=input_text,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return result.stdout


def scan_repository(repo: Path = REPO, *, threshold_bytes: int = DEFAULT_THRESHOLD_BYTES) -> dict:
    """只读扫描仓库全部历史对象并返回报告。"""
    rev_list = _git(repo, ["rev-list", "--objects", "--all"])
    paths = parse_rev_list(rev_list)
    shas = list(paths)
    batch = _git(
        repo,
        ["cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize)"],
        input_text="\n".join(shas) + "\n",
    )
    metadata = parse_batch_check(batch)
    entries = [
        {
            "sha": sha,
            "path": paths.get(sha, ""),
            "type": metadata[sha]["type"],
            "size": metadata[sha]["size"],
        }
        for sha in shas
        if sha in metadata
    ]
    return _build_report(entries, repository=repo, threshold_bytes=threshold_bytes)


def main(argv: list[str] | None = None) -> int:
    """CLI 入口：扫描历史、打印摘要并可选写出 JSON 报告。"""
    parser = argparse.ArgumentParser(description="只读扫描 Git 历史大文件与构建产物")
    parser.add_argument("--repo", type=Path, default=REPO)
    parser.add_argument("--threshold-bytes", type=int, default=DEFAULT_THRESHOLD_BYTES)
    parser.add_argument("--json-out", type=Path, default=None)
    parser.add_argument("--fail-on-suspicious", action="store_true")
    parser.add_argument("--rev-list-file", type=Path, default=None, help=argparse.SUPPRESS)
    parser.add_argument("--batch-check-file", type=Path, default=None, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    if args.rev_list_file and args.batch_check_file:
        paths = parse_rev_list(args.rev_list_file.read_text(encoding="utf-8"))
        metadata = parse_batch_check(args.batch_check_file.read_text(encoding="utf-8"))
        entries = [
            {
                "sha": sha,
                "path": paths.get(sha, ""),
                "type": metadata[sha]["type"],
                "size": metadata[sha]["size"],
            }
            for sha in paths
            if sha in metadata
        ]
        report = _build_report(entries, repository=args.repo, threshold_bytes=args.threshold_bytes)
    else:
        report = scan_repository(args.repo, threshold_bytes=args.threshold_bytes)

    if args.json_out is not None:
        args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        f"Git 历史只读扫描：{report['object_count']} 个对象、"
        f"{report['suspicious_count']} 个可疑对象、"
        f"阈值 {report['threshold_bytes']} 字节。"
    )
    for item in report["large_objects"][:10]:
        print(f"  {item['size']:>12}  {item['path'] or '(无路径)'}  [{', '.join(item['reasons'])}]")
    if report["history_rewrite"]:
        print("ERROR: 本工具不允许重写历史。")
        return 1
    print("未执行任何写操作；历史处置决定见 docs/仓库历史清理评估.md。")
    return 1 if args.fail_on_suspicious and report["suspicious_count"] else 0


if __name__ == "__main__":
    sys.exit(main())
