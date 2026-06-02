"""分析 scan_report.json 的内容"""
from __future__ import annotations

import json
from pathlib import Path

report = Path("scan_report.json")
data = json.loads(report.read_text(encoding="utf-8"))

header = data.get("headers", [{}])[0] if data.get("headers") else {}

print("=== 扫描概要 ===")
print(f"  工具: {header.get('tool_name', '?')} {header.get('tool_version', '?')}")
print(f"  开始: {header.get('start_timestamp', '?')}")
print(f"  结束: {header.get('end_timestamp', '?')}")
print(f"  耗时: {header.get('duration', 0):.0f} 秒")
print()

errors = header.get("errors") or []
if errors:
    print(f"=== 错误（{len(errors)} 条） ===")
    for e in errors:
        print(f"  {str(e)[:300]}")
    print()

files = data.get("files", [])

# === License detections ===
license_in_files: dict[str, int] = {}
copyright_found = 0
no_findings = 0

for f in files:
    file_licenses = f.get("licenses") or []
    file_copyrights = f.get("copyrights") or []
    has_license = False
    has_copyright = False

    for l in file_licenses:
        key = l.get("key", l.get("spdx_license_key", "unknown"))
        license_in_files[key] = license_in_files.get(key, 0) + 1
        has_license = True

    if file_copyrights:
        has_copyright = True

    if not has_license and not has_copyright:
        no_findings += 1

print(f"=== 文件统计 ===")
print(f"  总文件数: {len(files)}")
print(f"  license_detections 键: {list(data.get('license_detections', {}).keys())[:10]}")
print()

print(f"=== 文件中检测到的许可证（按频率排序）===")
if license_in_files:
    for key, count in sorted(license_in_files.items(), key=lambda x: -x[1]):
        print(f"  {key}: {count} 个文件")
else:
    print("  （无）")
print()

print(f"=== 版权声明 ===")
copyrights: dict[str, int] = {}
for f in files:
    for c in f.get("copyrights") or []:
        for stmt in (c.get("statements") or []):
            copyrights[stmt] = copyrights.get(stmt, 0) + 1

if copyrights:
    for stmt, count in sorted(copyrights.items(), key=lambda x: -x[1])[:20]:
        print(f"  [{count}] {stmt[:150]}")
else:
    print("  （无）")
print()

# === 列出有许可证检测结果的文件（可能是第三方代码）===
print(f"=== 有许可证检测的文件（可能含有第三方代码）===")
sample_files = []
for f in files:
    lic = f.get("licenses") or []
    cr = f.get("copyrights") or []
    if lic or cr:
        sample_files.append(f.get("path", "?"))
        if len(sample_files) >= 20:
            break

for fp in sample_files:
    print(f"  - {fp}")

if not sample_files:
    print("  （无语，所有文件都没有许可证/版权检测结果）")
print()

print(f"=== 无任何检测结果的文件: {no_findings} ===")
