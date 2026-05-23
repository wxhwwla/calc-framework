#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BWIKI 装备草案 -> 本地 equipments.json 同步。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from bwiki_scout.equipment_wiki import equipment_record_from_draft


def convert_equipment_draft_record(record: dict[str, Any]) -> dict[str, Any]:
    """将 parsed/equipment.json 条目映射为本地装备格式（字段与 Wiki 对齐）。"""
    return equipment_record_from_draft(record)


def sync_equipments_from_parsed(
    *,
    parsed_equipment_json: Path,
    local_equipments_json: Path,
    dry_run: bool = True,
) -> dict[str, Any]:
    """同步装备：parsed 草案 -> 本地标准 JSON。"""
    rows = json.loads(parsed_equipment_json.read_text(encoding="utf-8"))
    converted = [convert_equipment_draft_record(r) for r in rows if r.get("名称")]
    converted.sort(key=lambda x: x.get("名称", ""))
    if not dry_run:
        local_equipments_json.parent.mkdir(parents=True, exist_ok=True)
        local_equipments_json.write_text(
            json.dumps(converted, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    kinds: dict[str, int] = {}
    for row in converted:
        kind = str(row.get("装备种类") or "")
        if kind:
            kinds[kind] = kinds.get(kind, 0) + 1
    return {
        "dry_run": dry_run,
        "count": len(converted),
        "kind_counts": kinds,
        "sample_names": [row["名称"] for row in converted[:10]],
    }
