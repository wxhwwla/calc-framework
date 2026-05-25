#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""装备数据链路与四格装配。"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from calculation.damage_engine import DamageEffect
from calculation.damage_types import infer_equipment_damage_types

_PERCENT_RE = re.compile(r"([+-]?\d+(?:\.\d+)?)\s*%")

# 与 BWIKI「装备种类」一致：护甲 / 护手 / 配件
EQUIPMENT_KIND_ARMOR = "护甲"
EQUIPMENT_KIND_GLOVES = "护手"
EQUIPMENT_KIND_ACCESSORY = "配件"

_SLOT_ALIASES = {
    EQUIPMENT_KIND_ARMOR: EQUIPMENT_KIND_ARMOR,
    EQUIPMENT_KIND_GLOVES: EQUIPMENT_KIND_GLOVES,
    EQUIPMENT_KIND_ACCESSORY: EQUIPMENT_KIND_ACCESSORY,
    "胸甲": EQUIPMENT_KIND_ARMOR,
}

# BWIKI 同步失败或旧数据：按名称关键词回退推断装备种类
_NAME_SLOT_KEYWORDS: tuple[tuple[str, str], ...] = (
    ("轻甲", EQUIPMENT_KIND_ARMOR),
    ("重甲", EQUIPMENT_KIND_ARMOR),
    ("护甲", EQUIPMENT_KIND_ARMOR),
    ("罩衣", EQUIPMENT_KIND_ARMOR),
    ("夹克", EQUIPMENT_KIND_ARMOR),
    ("背心", EQUIPMENT_KIND_ARMOR),
    ("甲片", EQUIPMENT_KIND_ARMOR),
    ("外骨骼", EQUIPMENT_KIND_ARMOR),
    ("胸甲", EQUIPMENT_KIND_ARMOR),
    ("护手", EQUIPMENT_KIND_GLOVES),
    ("手套", EQUIPMENT_KIND_GLOVES),
    ("护腕", EQUIPMENT_KIND_GLOVES),
    ("手甲", EQUIPMENT_KIND_GLOVES),
    ("雷达", EQUIPMENT_KIND_ACCESSORY),
    ("短刃", EQUIPMENT_KIND_ACCESSORY),
    ("刺刃", EQUIPMENT_KIND_ACCESSORY),
    ("芯片", EQUIPMENT_KIND_ACCESSORY),
    ("戒指", EQUIPMENT_KIND_ACCESSORY),
    ("项链", EQUIPMENT_KIND_ACCESSORY),
    ("胸针", EQUIPMENT_KIND_ACCESSORY),
    ("徽章", EQUIPMENT_KIND_ACCESSORY),
    ("手环", EQUIPMENT_KIND_ACCESSORY),
    ("臂环", EQUIPMENT_KIND_ACCESSORY),
    ("瞄具", EQUIPMENT_KIND_ACCESSORY),
    ("工具组", EQUIPMENT_KIND_ACCESSORY),
    ("储能", EQUIPMENT_KIND_ACCESSORY),
    ("测温镜", EQUIPMENT_KIND_ACCESSORY),
    ("电力匣", EQUIPMENT_KIND_ACCESSORY),
    ("净芯", EQUIPMENT_KIND_ACCESSORY),
    ("滤芯", EQUIPMENT_KIND_ACCESSORY),
    ("图鉴", EQUIPMENT_KIND_ACCESSORY),
)


def equipment_kind(record: dict[str, Any]) -> str:
    """读取装备种类（优先 Wiki 字段「装备种类」，兼容旧字段「部位」）。"""
    raw = str(record.get("装备种类") or record.get("部位") or "").strip()
    if raw in _SLOT_ALIASES:
        return _SLOT_ALIASES[raw]
    return raw

@dataclass(frozen=True)
class FourSlotLoadout:
    """四格装备。"""

    chest: dict[str, Any]
    gloves: dict[str, Any]
    accessory_a: dict[str, Any]
    accessory_b: dict[str, Any]


def _parse_percent_value(text: str) -> float:
    m = _PERCENT_RE.search(text)
    if not m:
        return 0.0
    return float(m.group(1)) / 100.0


def _infer_damage_types(text: str) -> tuple[str, ...]:
    return infer_equipment_damage_types(text)


def _parse_effect_text(text: str, *, source: str) -> DamageEffect:
    from calculation.equipment_affix import parse_equipment_affix_line

    affix_effects, _ = parse_equipment_affix_line(text, source=source)
    if affix_effects:
        return affix_effects[0]

    value = _parse_percent_value(text)
    if "易伤" in text:
        return DamageEffect("易伤", value=value, source=source, raw_text=text, damage_types=_infer_damage_types(text))
    if "脆弱" in text:
        return DamageEffect("脆弱", value=value, source=source, raw_text=text, damage_types=_infer_damage_types(text))
    if "虚弱" in text:
        return DamageEffect("虚弱", value=value, source=source, raw_text=text)
    if "庇护" in text:
        return DamageEffect("庇护", value=value, source=source, raw_text=text)
    if "伤害减免" in text:
        return DamageEffect("伤害减免", value=value, source=source, raw_text=text, damage_types=_infer_damage_types(text))
    if "连击增伤" in text:
        return DamageEffect("连击增伤", value=value, source=source, raw_text=text)
    if "增幅" in text:
        return DamageEffect("增幅", value=value, source=source, raw_text=text, damage_types=_infer_damage_types(text))
    if "伤害+" in text or "伤害加成" in text:
        damage_types = _infer_damage_types(text)
        effect_type = "伤害类型伤害加成" if damage_types else "其他伤害加成"
        return DamageEffect(
            effect_type,
            value=value,
            source=source,
            raw_text=text,
            damage_types=damage_types,
        )
    return DamageEffect(text.strip(), value=value, source=source, raw_text=text)


def _normalize_slot(slot_raw: str) -> str:
    slot = (slot_raw or "").strip()
    if slot in _SLOT_ALIASES:
        return _SLOT_ALIASES[slot]
    raise ValueError(f"不支持的装备部位：{slot_raw}")


def infer_equipment_slot(record: dict[str, Any]) -> str:
    """从记录推断装备种类；优先显式字段，否则按名称关键词。"""
    slot_raw = equipment_kind(record)
    if slot_raw in _SLOT_ALIASES:
        return _SLOT_ALIASES[slot_raw]
    type_raw = str(record.get("类型") or "").strip()
    if type_raw in _SLOT_ALIASES:
        return _SLOT_ALIASES[type_raw]
    name = str(record.get("名称") or "").strip()
    for keyword, slot in _NAME_SLOT_KEYWORDS:
        if keyword in name:
            return slot
    return ""


def _parse_effect_keys(params: dict[str, Any], prefix: str, source: str) -> list[DamageEffect]:
    effects: list[DamageEffect] = []
    for idx in range(1, 10):
        key = f"{prefix}{idx}"
        text = str(params.get(key, "")).strip()
        if not text:
            continue
        effects.append(_parse_effect_text(text, source=source))
    return effects


def build_runtime_equipment_from_wiki_draft(record: dict[str, Any]) -> dict[str, Any]:
    """将 BWIKI 草案记录转为可计算装备。"""
    params = record.get("_wiki_params") or {}
    name = str(record.get("名称") or params.get("名称") or "").strip()
    slot_raw = str(
        params.get("装备种类") or params.get("部位") or params.get("类型") or ""
    ).strip()
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
    from calculation.equipment_affix import (
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
    for text in (record.get("效果") or []):
        if not str(text).strip():
            continue
        effs, flats = parse_equipment_effect_block(str(text), source=source)
        direct_effects.extend(effs)
        for key, val in flats.items():
            flat_stats[key] = flat_stats.get(key, 0.0) + val
    for text in (record.get("属性词条") or []):
        if not str(text).strip():
            continue
        effs, flats = parse_equipment_affix_line(str(text), source=source)
        direct_effects.extend(effs)
        for key, val in flats.items():
            flat_stats[key] = flat_stats.get(key, 0.0) + val
    set_effects: list[DamageEffect] = []
    for text in (record.get("三件套效果") or []):
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
