#!/usr/bin/env python3
"""搜索导出路径工具。"""

from __future__ import annotations

from pathlib import Path


def format_export_paths(top_json: Path | None, top_csv: Path | None) -> str:
    lines: list[str] = []
    if top_json is not None:
        lines.append(f"JSON: {top_json}")
    if top_csv is not None:
        lines.append(f"CSV: {top_csv}")
    return "\n".join(lines) if lines else "无导出"
