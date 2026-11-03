#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""装备数据链路与四格装配。

P2-07 拆分：种类常量/部位推断迁至 ``equipment_kinds.py``，效果文本解析迁至
``equipment_effects.py``；本模块继续再导出这些符号，既有导入路径不变。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from games.endfield.calc.damage.engine import DamageEffect

from .equipment_effects import (
    _infer_damage_types,
    _parse_effect_keys,
    _parse_effect_text,
    _parse_percent_value,
)
from .equipment_kinds import (
    EQUIPMENT_KIND_ACCESSORY,
    EQUIPMENT_KIND_ARMOR,
    EQUIPMENT_KIND_GLOVES,
    _normalize_slot,
    equipment_kind,
    infer_equipment_slot,
)

__all__ = [
    "EQUIPMENT_KIND_ACCESSORY",
    "EQUIPMENT_KIND_ARMOR",
    "EQUIPMENT_KIND_GLOVES",
    "FourSlotLoadout",
    "_infer_damage_types",
    "_normalize_slot",
    "_parse_effect_keys",
    "_parse_effect_text",
    "_parse_percent_value",
    "build_equipment_catalog_from_local_rows",
    "build_equipment_catalog_from_runtime",
    "build_four_slot_loadout",
    "build_runtime_equipment_from_local_record",
    "build_runtime_equipment_from_wiki_draft",
    "collect_loadout_effects",
    "equipment_kind",
    "infer_equipment_slot",
    "load_equipment_catalog_from_wiki_draft",
]


@dataclass(frozen=True)
class FourSlotLoadout:
    """四格装备。"""

    chest: dict[str, Any]

    gloves: dict[str, Any]

    accessory_a: dict[str, Any]

    accessory_b: dict[str, Any]


def build_runtime_equipment_from_wiki_draft(record: dict[str, Any]) -> dict[str, Any]:
    """将 BWIKI 草案记录转为可计算装备。"""

    params = record.get("_wiki_params") or {}

    name = str(record.get("名称") or params.get("名称") or "").strip()

    slot_raw = str(params.get("装备种类") or params.get("部位") or params.get("类型") or "").strip()

    slot = infer_equipment_slot({"装备种类": slot_raw, "部位": slot_raw, "名称": name})

    if not slot:
        raise ValueError(f"无法推断装备种类：{name or '未命名装备'}")

    slot = _normalize_slot(slot)

    set_id = str(params.get("所属套组") or params.get("套装") or "").strip()

    source = f"{name or '未命名装备'}"

    direct_effects = _parse_effect_keys(params, "效果", source)

    set_effects = _parse_effect_keys(params, "三件套效果", source)

    if not set_effects:
        set_text = str(params.get("装备套组效果") or "").strip()

        if set_text:
            set_effects = [_parse_effect_text(set_text, source=source)]

    return {
        "名称": name,
        "装备种类": slot,
        "部位": slot,
        "套装": set_id,
        "效果": direct_effects,
        "三件套效果": set_effects,
    }


def build_runtime_equipment_from_local_record(record: dict[str, Any]) -> dict[str, Any]:
    """将本地 equipments.json 记录转为可计算装备。"""

    from games.endfield.calc.equipment.affix import (
        parse_equipment_affix_line,
        parse_equipment_effect_block,
    )

    name = str(record.get("名称") or "").strip()

    slot = infer_equipment_slot(record)

    if not slot:
        raise ValueError(f"无法推断装备种类：{name or '未命名装备'}")

    slot = _normalize_slot(slot)

    set_id = str(record.get("套装") or "").strip()

    source = f"{name or '未命名装备'}"

    flat_stats: dict[str, float] = {}

    direct_effects: list[DamageEffect] = []

    for text in record.get("效果") or []:
        if not str(text).strip():
            continue

        effs, flats = parse_equipment_effect_block(str(text), source=source)

        direct_effects.extend(effs)

        for key, val in flats.items():
            flat_stats[key] = flat_stats.get(key, 0.0) + val

    for text in record.get("属性词条") or []:
        if not str(text).strip():
            continue

        effs, flats = parse_equipment_affix_line(str(text), source=source)

        direct_effects.extend(effs)

        for key, val in flats.items():
            flat_stats[key] = flat_stats.get(key, 0.0) + val

    set_effects: list[DamageEffect] = []

    for text in record.get("三件套效果") or []:
        if not str(text).strip():
            continue

        effs, flats = parse_equipment_effect_block(str(text), source=source)

        set_effects.extend(effs)

        for key, val in flats.items():
            flat_stats[key] = flat_stats.get(key, 0.0) + val

    return {
        "名称": name,
        "装备种类": slot,
        "部位": slot,
        "套装": set_id,
        "效果": direct_effects,
        "三件套效果": set_effects,
        "flat_stats": flat_stats,
    }


def build_four_slot_loadout(
    *,
    chest: dict[str, Any],
    gloves: dict[str, Any],
    accessory_a: dict[str, Any],
    accessory_b: dict[str, Any],
    allow_duplicate_accessory: bool = True,
) -> FourSlotLoadout:
    """构建四格装备并校验部位规则。"""

    if equipment_kind(chest) != EQUIPMENT_KIND_ARMOR:
        raise ValueError("护甲槽位必须放置护甲类装备")

    if equipment_kind(gloves) != EQUIPMENT_KIND_GLOVES:
        raise ValueError("护手槽位必须放置护手类装备")

    if equipment_kind(accessory_a) != EQUIPMENT_KIND_ACCESSORY:
        raise ValueError("配件A槽位必须放置配件类装备")

    if equipment_kind(accessory_b) != EQUIPMENT_KIND_ACCESSORY:
        raise ValueError("配件B槽位必须放置配件类装备")

    if not allow_duplicate_accessory and accessory_a.get("名称") == accessory_b.get("名称"):
        raise ValueError("当前配置不允许重复配件")

    return FourSlotLoadout(
        chest=chest,
        gloves=gloves,
        accessory_a=accessory_a,
        accessory_b=accessory_b,
    )


def collect_loadout_effects(loadout: FourSlotLoadout) -> list[DamageEffect]:
    """收集四格效果并在三件同套时追加套装效果。"""

    all_items = [
        loadout.chest,
        loadout.gloves,
        loadout.accessory_a,
        loadout.accessory_b,
    ]

    effects: list[DamageEffect] = []

    for item in all_items:
        effects.extend(item.get("效果") or [])

    set_counts: dict[str, int] = {}

    for item in all_items:
        set_id = str(item.get("套装") or "").strip()

        if not set_id:
            continue

        set_counts[set_id] = set_counts.get(set_id, 0) + 1

    activated_sets = {sid for sid, cnt in set_counts.items() if cnt >= 3}

    for set_id in activated_sets:
        for item in all_items:
            if str(item.get("套装") or "").strip() == set_id:
                effects.extend(item.get("三件套效果") or [])

                break

    return effects


def build_equipment_catalog_from_runtime(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """将运行时装备记录归并为搜索目录。"""

    catalog = {"chest": [], "gloves": [], "accessories": []}

    for item in records:
        slot = equipment_kind(item)

        if slot == EQUIPMENT_KIND_ARMOR:
            catalog["chest"].append(item)

        elif slot == EQUIPMENT_KIND_GLOVES:
            catalog["gloves"].append(item)

        elif slot == EQUIPMENT_KIND_ACCESSORY:
            catalog["accessories"].append(item)

    return catalog


def build_equipment_catalog_from_local_rows(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """从本地装备 JSON 行构建可搜索目录。"""

    runtime_records = []

    for record in records:
        try:
            runtime_records.append(build_runtime_equipment_from_local_record(record))

        except ValueError:
            continue

    return build_equipment_catalog_from_runtime(runtime_records)


def load_equipment_catalog_from_wiki_draft(path: Path) -> dict[str, list[dict[str, Any]]]:
    """从 BWIKI 解析草案加载装备目录。"""

    data = json.loads(Path(path).read_text(encoding="utf-8"))

    runtime_records = []

    for record in data:
        try:
            runtime_records.append(build_runtime_equipment_from_wiki_draft(record))

        except ValueError:
            continue

    return build_equipment_catalog_from_runtime(runtime_records)
