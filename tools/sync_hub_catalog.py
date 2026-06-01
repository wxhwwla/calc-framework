#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""从 framework/adapters 同步 web/hub/catalog.json 适配器条目（保留 samples 下载链）。"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ADAPTER_ROOT = REPO / "framework" / "adapters"
CATALOG_PATH = REPO / "web" / "hub" / "catalog.json"
REPO_URL = "https://github.com/wxhwwla/calc-framework"
SAMPLE_IDS = frozenset({"fps", "moba", "card_rpg"})


def build_adapter_entry(adapter_id: str, meta: dict) -> dict:
    entry = {
        "name": meta.get("name", adapter_id),
        "id": adapter_id,
        "type": "game",
        "genre": adapter_id,
        "description": meta.get("description", ""),
        "version": meta.get("version", "1.0.0"),
        "updated": date.today().isoformat(),
        "stars": 0,
        "download_url": "",
        "source_url": f"{REPO_URL}/tree/main/framework/adapters/{adapter_id}",
        "dependencies": [],
        "schema_version": meta.get("schema_version", "dag-v1"),
    }
    if adapter_id in SAMPLE_IDS:
        entry["download_url"] = f"./samples/{adapter_id}_sample.calcpack"
    return entry


def sync_catalog() -> dict:
    adapters: list[dict] = []
    for path in sorted(ADAPTER_ROOT.iterdir()):
        if not path.is_dir():
            continue
        meta_file = path / "meta.json"
        if not meta_file.is_file():
            continue
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        adapters.append(build_adapter_entry(path.name, meta))

    catalog = {
        "schema_version": "hub-v1",
        "name": "Game Calc Hub Catalog",
        "updated": date.today().isoformat(),
        "adapters": adapters,
    }
    CATALOG_PATH.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return catalog


def main() -> int:
    catalog = sync_catalog()
    print(f"Wrote {len(catalog['adapters'])} adapters to {CATALOG_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
