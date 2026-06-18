#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""生成或校验 .secrets.baseline（供 CI / 本地维护使用）。"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BASELINE = REPO_ROOT / ".secrets.baseline"
EXCLUDE = (
    r"package-lock\.json|poetry\.lock|.*\.calcpack|.*\.zip|"
    r"\.tmp-audit-venv.*|\.secrets\.baseline|\.admin_data|"
    r"tools/tests/test_secrets_baseline\.py|"
    r"i18n/locales/.*\.ts$|"
    r"searchResumeDb\.ts$"
)


def _run_scan(*, update: bool) -> str:
    cmd = [
        "detect-secrets",
        "scan",
        "--all-files",
        "--exclude-files",
        EXCLUDE,
    ]
    if update and BASELINE.is_file():
        cmd.extend(["--baseline", str(BASELINE)])
    proc = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        raise SystemExit(proc.returncode)
    return proc.stdout


def generate() -> None:
    """全量扫描并写入 baseline。"""
    output = _run_scan(update=False)
    BASELINE.write_text(output, encoding="utf-8")
    data = json.loads(output)
    count = sum(len(v) for v in data.get("results", {}).values())
    print(f"已写入 {BASELINE}（{count} 条记录）")


def _secret_fingerprints(data: dict) -> set[tuple[str, str, int]]:
    """提取 (文件, 哈希, 行号) 集合，用于判断是否有新增密钥。"""
    fps: set[tuple[str, str, int]] = set()
    for path, entries in data.get("results", {}).items():
        for entry in entries:
            fps.add(
                (
                    path,
                    str(entry.get("hashed_secret", "")),
                    int(entry.get("line_number", 0)),
                )
            )
    return fps


def verify_no_new_secrets() -> None:
    """CI 用：相对 baseline 不得出现新密钥。"""
    if not BASELINE.is_file():
        print("缺少 .secrets.baseline，请先运行 tools/generate_secrets_baseline.py generate", file=sys.stderr)
        raise SystemExit(1)

    before_data = json.loads(BASELINE.read_text(encoding="utf-8"))
    before_fps = _secret_fingerprints(before_data)

    output = _run_scan(update=False)
    after_data = json.loads(output)
    after_fps = _secret_fingerprints(after_data)

    new_entries = after_fps - before_fps
    if new_entries:
        print(
            f"detect-secrets：发现 {len(new_entries)} 条 baseline 未记录的新密钥，"
            "请审查后运行 python tools/generate_secrets_baseline.py generate",
            file=sys.stderr,
        )
        for path, hashed, line in sorted(new_entries)[:10]:
            print(f"  - {path}:{line} ({hashed[:12]}…)", file=sys.stderr)
        raise SystemExit(1)

    print("detect-secrets baseline 校验通过（无新增密钥）")


def main() -> None:
    parser = argparse.ArgumentParser(description="管理 detect-secrets baseline")
    parser.add_argument(
        "action",
        choices=("generate", "verify"),
        help="generate=重建 baseline；verify=CI 校验无新增",
    )
    args = parser.parse_args()
    if args.action == "generate":
        generate()
    else:
        verify_no_new_secrets()


if __name__ == "__main__":
    main()
