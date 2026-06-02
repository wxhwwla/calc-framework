#!/usr/bin/env python3
"""检查项目源代码中是否包含第三方许可证/版权声明。

用于快速判断 AI 生成的代码是否含有来自其他开源项目的版权内容。

用法（仓库根目录）::

    python tools/check_code_origin.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


# 常见开源许可证的标识符和关键词
LICENSE_PATTERNS: list[tuple[str, str, list[str]]] = [
    ("MIT", "MIT License", [
        r"MIT License",
        r"Permission is hereby granted, free of charge, to any person",
        r"THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY",
    ]),
    ("Apache-2.0", "Apache License 2.0", [
        r"Apache License[,\s]+Version 2\.0",
        r"Licensed under the Apache License, Version 2\.0",
        r'http://www\.apache\.org/licenses/LICENSE-2\.0',
    ]),
    ("GPL-2.0", "GNU General Public License v2.0", [
        r"GNU General Public License[,\s]+version 2",
        r"GNU GENERAL PUBLIC LICENSE[,\s]+Version 2",
    ]),
    ("GPL-3.0", "GNU General Public License v3.0", [
        r"GNU General Public License[,\s]+version 3",
        r"GNU GENERAL PUBLIC LICENSE[,\s]+Version 3",
    ]),
    ("LGPL", "GNU Lesser General Public License", [
        r"GNU Lesser General Public License",
        r"GNU LIBRARY GENERAL PUBLIC LICENSE",
    ]),
    ("BSD", "BSD License", [
        r"Redistributions of source code must retain the above copyright",
        r"Redistributions in binary form must reproduce",
        r"BSD [23]-Clause",
        r"BSD 2-Clause",
        r"BSD 3-Clause",
    ]),
    ("MPL-2.0", "Mozilla Public License 2.0", [
        r"Mozilla Public License[,\s]+Version 2\.0",
        r"Mozilla Public License[,\s]version 2\.0",
    ]),
    ("Unlicense", "The Unlicense", [
        r"This is free and unencumbered software released into the public domain",
        r"Unlicense",
    ]),
    ("CC0", "CC0 1.0 Universal", [
        r"CC0 1\.0 Universal",
        r"Creative Commons Zero",
    ]),
    ("CC-BY", "Creative Commons Attribution", [
        r"Creative Commons Attribution",
        r"CC BY",
    ]),
    ("ISC", "ISC License", [
        r"ISC License",
        r"Permission to use, copy, modify, and/or distribute this software",
    ]),
    ("Zlib", "zlib/libpng License", [
        r"zlib License",
        r"This software is provided 'as-is', without any express or implied",
    ]),
    ("Python-2.0", "Python Software Foundation License", [
        r"Python Software Foundation License",
        r"PSF LICENSE AGREEMENT FOR PYTHON",
    ]),
    ("JetBrains", "JetBrains License", [
        r"JetBrains",
    ]),
]

SPDX_PATTERN = re.compile(r"SPDX-License-Identifier:\s*(\S+)", re.IGNORECASE)
COPYRIGHT_PATTERN = re.compile(
    r"(?i)"
    r"(?:copyright\s+(?:©\s*)?(?:\d{4}[-\d{,4}]*(?:,\s*\d{4})*)?\s*(?:by\s+)?"
    r"(.{1,120}?))"
    r"|(?:©\s*(?:\d{4}[-\d{,4}]*(?:,\s*\d{4})*)?\s*(.{1,120}?))"
    r"|(?:All rights reserved)"
)

# 文件扩展名白名单（只检查源代码）
SOURCE_EXTENSIONS = {
    ".py", ".pyx",
    ".js", ".mjs", ".cjs",
    ".ts", ".tsx",
    ".json",
    ".yaml", ".yml",
    ".toml",
    ".cfg", ".ini", ".conf",
    ".md", ".rst",
    ".txt",
    ".css", ".scss",
    ".html", ".htm",
    ".xml", ".xsl",
    ".svg",
    ".cmake",
    ".bat", ".cmd",
    ".ps1",
    ".sh",
    ".desktop",
    ".editorconfig",
    ".gitattributes",
    ".dockerfile",
}

# 排除的目录
EXCLUDE_DIRS = {
    "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache",
    ".git", ".venv", "venv", "env", "node_modules",
    ".idea", ".vscode", ".trae", ".cursor", ".agents",
    "dist", "build", "build_*", "spec_*",
    "__pycache__", "egg-info",
}


def find_source_files(root: Path) -> list[Path]:
    """递归查找所有源代码文件。"""
    files = []
    for path in root.rglob("*"):
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in SOURCE_EXTENSIONS:
            files.append(path)
    return files


def check_license_in_file(filepath: Path) -> list[dict]:
    """检查单个文件中是否包含许可证或版权声明。"""
    findings: list[dict] = []
    try:
        text = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception:
        try:
            text = filepath.read_text(encoding="latin-1", errors="replace")
        except Exception:
            return [{"type": "error", "detail": "无法读取文件"}]

    lines = text.splitlines()

    # 检查 SPDX 标识符
    for match in SPDX_PATTERN.finditer(text):
        line_num = text[:match.start()].count("\n") + 1
        findings.append({
            "type": "spdx",
            "value": match.group(1),
            "line": line_num,
        })

    # 检查版权声明
    for match in COPYRIGHT_PATTERN.finditer(text):
        line_num = text[:match.start()].count("\n") + 1
        groups = [g for g in match.groups() if g]
        copyright_text = groups[0] if groups else match.group(0)
        findings.append({
            "type": "copyright",
            "value": copyright_text.strip()[:120],
            "line": line_num,
        })

    # 检查已知许可证文本
    for lic_id, lic_name, patterns in LICENSE_PATTERNS:
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                line_num = text[:match.start()].count("\n") + 1
                findings.append({
                    "type": "license",
                    "license_id": lic_id,
                    "license_name": lic_name,
                    "value": match.group(0)[:120],
                    "line": line_num,
                })
                break  # 每个许可证只报告一次

    return findings


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent

    source_dirs = [
        repo_root / "framework",
        repo_root / "games" / "endfield",
        repo_root / "tools" / "endfield_designer",
        repo_root / "tools" / "endfield_scripts",
        repo_root / "tools" / "ocr",
        repo_root / "tools" / "data_pipeline",
        repo_root / "tools" / "designer",
        repo_root / "tools" / "audit",
        repo_root / "tools" / "tests",
        repo_root / "scripts",
        repo_root / "utils",
        repo_root / "docs",
    ]

    all_files: list[Path] = []
    for d in source_dirs:
        if d.is_dir():
            all_files.extend(find_source_files(d))

    all_files.sort()
    print(f"共找到 {len(all_files)} 个源代码文件\n")

    report: list[dict] = []
    files_with_findings = 0

    for f in all_files:
        findings = check_license_in_file(f)
        if findings:
            files_with_findings += 1
            report.append({
                "file": str(f.relative_to(repo_root)),
                "findings": findings,
            })

    # === 输出报告 ===
    print(f"{'='*60}")
    print(f"  代码来源检查报告")
    print(f"{'='*60}")
    print()

    if not report:
        print("[OK] 未发现任何第三方许可证或版权声明")
        print("(所有代码看起来都是原创的)")
        return

    print(f"[!] 在 {files_with_findings}/{len(all_files)} 个文件中发现许可证/版权声明\n")

    # SPDX 标识符汇总
    spdx_findings = [r for r in report if any(f["type"] == "spdx" for f in r["findings"])]
    if spdx_findings:
        print(f"--- SPDX License Identifier 发现（{len(spdx_findings)} 个文件）---")
        for r in spdx_findings:
            spdx_tags = [f for f in r["findings"] if f["type"] == "spdx"]
            for tag in spdx_tags:
                print(f"  {r['file']}:{tag['line']}  {tag['value']}")
        print()

    # 许可证文本发现
    lic_findings = [
        (r["file"], f) for r in report
        for f in r["findings"] if f["type"] == "license"
    ]
    if lic_findings:
        print(f"--- 许可证文本发现（{len(lic_findings)} 处）---")
        for filepath, lic in lic_findings:
            print(f"  {filepath}:{lic['line']}")
            print(f"    [{lic['license_id']}] {lic['value']}")
        print()

    # 版权声明发现
    cr_findings = [
        (r["file"], f) for r in report
        for f in r["findings"] if f["type"] == "copyright"
    ]
    if cr_findings:
        print(f"--- 版权声明发现（{len(cr_findings)} 处）---")
        for filepath, cr in cr_findings:
            print(f"  {filepath}:{cr['line']}")
            print(f"    {cr['value']}")
        print()

    # 有发现的所有文件列表，方便手动审查
    print(f"--- 需要审查的文件列表 ---")
    for r in report:
        has_spdx = any(f["type"] == "spdx" for f in r["findings"])
        has_lic = any(f["type"] == "license" for f in r["findings"])
        labels = []
        if has_spdx:
            labels.append("SPDX")
        if has_lic:
            labels.append("LIC")
        if any(f["type"] == "copyright" for f in r["findings"]):
            labels.append("CR")
        print(f"  [{','.join(labels)}] {r['file']}")


if __name__ == "__main__":
    main()
