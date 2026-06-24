#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""

构建 Calc Hub 适配器目录 (catalog.json)。



从 framework/adapters/ 扫描所有适配包的 meta.json，

生成为 hub 可消费的 JSON 目录。

"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _find_adapters_dir() -> Path:
    repo = Path(__file__).resolve().parents[2]

    candidates = [
        repo / "framework" / "adapters",
    ]

    for c in candidates:
        if c.is_dir():
            return c

    raise FileNotFoundError("找不到 adapters 目录")


def build_catalog(adapters_dir: Path | None = None) -> dict:
    if adapters_dir is None:
        adapters_dir = _find_adapters_dir()

    catalog = {
        "schema_version": "hub-v1",
        "name": "Game Calc Hub Catalog",
        "updated": "",
        "adapters": [],
    }

    for entry in sorted(adapters_dir.iterdir()):
        meta_path = entry / "meta.json"

        if not meta_path.is_file():
            continue

        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))

            sources = meta.get("sources", {})

            adapter_entry = {
                "name": meta.get("name", entry.name),
                "id": entry.name,
                "type": meta.get("type", "game"),
                "genre": meta.get("genre", ""),
                "description": meta.get("description", ""),
                "version": meta.get("version", "0.1.0"),
                "updated": meta.get("updated", ""),
                "stars": 0,
                "download_url": sources.get("download", ""),
                "source_url": sources.get("source", ""),
                "dependencies": meta.get("dependencies", []),
                "schema_version": meta.get("schema_version", ""),
            }

            catalog["adapters"].append(adapter_entry)

        except (json.JSONDecodeError, KeyError) as e:
            print(f"跳过 {entry.name}: {e}", file=sys.stderr)

    catalog["updated"] = __import__("datetime").datetime.now().strftime("%Y-%m-%d")

    return catalog


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="构建 Calc Hub 适配器目录")

    parser.add_argument("-o", "--output", default=None, help="输出路径 (默认 stdout)")

    parser.add_argument("--adapters-dir", default=None, help="适配器目录路径")

    args = parser.parse_args()

    try:
        catalog = build_catalog(Path(args.adapters_dir) if args.adapters_dir else None)

    except FileNotFoundError as e:
        print(e, file=sys.stderr)

        return 1

    text = json.dumps(catalog, ensure_ascii=False, indent=2)

    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")

        print(f"目录已写入: {args.output}")

    else:
        print(text)

    return 0


if __name__ == "__main__":
    sys.exit(main())
