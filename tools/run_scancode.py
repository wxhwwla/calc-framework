#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""运行 ScanCode Toolkit 许可证/版权扫描。

逐个目录扫描以避免内存溢出。最终输出合并报告。

用法（仓库根目录）::

    python tools/run_scancode.py

输出文件: ``scan_report.json``（在仓库根目录）。

依赖::

    pip install scancode-toolkit
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path


# 要扫描的源代码目录（按文件数排序，大的先扫以便观察进度）
SOURCE_DIRS = [
    "games/endfield",
    "framework",
    "tools/endfield_designer",
    "tools/endfield_scripts",
    "tools/ocr",
    "tools/data_pipeline",
    "tools/designer",
    "tools/audit",
    "tools/tests",
    "scripts",
    "utils",
    "docs",
]


def scan_directory(repo_root: Path, src_dir: str, out_path: Path) -> dict:
    """扫描单个目录，返回 JSON 结果。"""
    target = repo_root / src_dir
    if not target.is_dir():
        print(f"  跳过（目录不存在）: {src_dir}")
        return {}

    cmd = [
        "scancode",
        "--license", "--copyright", "--info",
        "--processes", "16",
        "--json-pp", str(out_path),
        str(target),
    ]

    print(f"  扫描: {src_dir} ({target.name})...", end=" ", flush=True)
    t0 = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.time() - t0

    if result.returncode != 0:
        print(f"失败 (rc={result.returncode})")
        print(f"    stderr: {result.stderr[:300]}")
        return {}

    if not out_path.is_file():
        print("无输出")
        return {}

    with open(out_path, encoding="utf-8") as f:
        data = json.load(f)

    files = data.get("files", [])
    errors = data.get("headers", [{}])[0].get("errors", []) if data.get("headers") else []
    print(f"完成 ({elapsed:.0f}s, {len(files)} 个文件, {len(errors)} 个错误)")
    return data


def merge_results(results: list[dict], output_path: Path) -> dict:
    """合并多个扫描结果为一个 JSON 报告。"""
    all_files = []
    all_errors = []
    total_duration = 0.0
    first_header = None

    for data in results:
        if not data:
            continue
        if first_header is None and data.get("headers"):
            first_header = data["headers"][0]
        for f in data.get("files", []):
            all_files.append(f)
        header = data.get("headers", [{}])[0] if data.get("headers") else {}
        for e in header.get("errors") or []:
            all_errors.append(e)
        total_duration += header.get("duration", 0)

    if first_header:
        first_header["files_count"] = len(all_files)
        first_header["directories_count"] = 0
        first_header["duration"] = total_duration
        first_header["errors"] = all_errors

    merged = {
        "headers": [first_header] if first_header else [],
        "files": all_files,
        "license_detections": {},
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)

    return merged


def analyze_report(data: dict) -> None:
    """打印报告摘要。"""
    files = data.get("files", [])
    if not files:
        return

    license_counts: dict[str, int] = {}
    copyright_files = 0

    for f in files:
        for lic in f.get("licenses") or []:
            key = lic.get("key", "unknown")
            license_counts[key] = license_counts.get(key, 0) + 1
        if f.get("copyrights"):
            copyright_files += 1

    errors = data.get("headers", [{}])[0].get("errors", []) if data.get("headers") else []

    print()
    print(f"  ├─ 扫描文件总数: {len(files)}")
    print(f"  ├─ 有版权声明的文件: {copyright_files}")
    print(f"  ├─ 检测到的许可证种类: {len(license_counts)}")
    if errors:
        print(f"  └─ 错误数: {len(errors)}")
        for e in errors[:5]:
            print(f"       {str(e)[:150]}")

    if license_counts:
        print()
        print("  许可证分布:")
        for key, count in sorted(license_counts.items(), key=lambda x: -x[1]):
            print(f"    {key}: {count}")


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    report_path = repo_root / "scan_report.json"

    print(f"ScanCode 许可证/版权扫描")
    print(f"{'='*50}")
    print(f"源目录数: {len(SOURCE_DIRS)}")
    print()

    # 逐个目录扫描，每个目录独立输出到临时文件
    temp_dir = Path(tempfile.mkdtemp(prefix="scancode_"))
    results: list[dict] = []

    try:
        for src_dir in SOURCE_DIRS:
            out_path = temp_dir / f"{src_dir.replace('/', '_').replace('\\\\', '_')}.json"
            data = scan_directory(repo_root, src_dir, out_path)
            results.append(data)

        # 合并结果
        print()
        print("合并结果...", end=" ", flush=True)
        merged = merge_results(results, report_path)
        print(f"完成 -> {report_path}")
        print()

        # 打印摘要
        print(f"{'='*50}")
        print(f"扫描报告摘要")
        print(f"{'='*50}")
        analyze_report(merged)

    finally:
        # 清理临时文件
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    print()
    print(f"完整报告: {report_path}")
    print(f"分析工具: python tools/check_code_origin.py")


if __name__ == "__main__":
    main()
