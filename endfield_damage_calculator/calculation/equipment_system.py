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

_PERCENT_RE = re.compile(r"([+-]?\d+(?:\.\d+)?)\s*%")

_SLOT_ALIASES = {
    "胸甲": "胸甲",
    "护手": "护手",
    "配件": "配件",
}

_DAMAGE_TYPE_TAGS = {
    "物理": ("物理",),
    "灼热": ("法术-灼热",),
    "电磁": ("法术-电磁",),
    "寒冷": ("法术-寒冷",),
    "自然": ("法术-自然",),
    "法术": ("法术-灼热", "法术-电磁", "法术-寒冷", "法术-自然"),
    "超域": ("超域",),
}


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
    for tag, mapped in _DAMAGE_TYPE_TAGS.items():
        if tag in text:
            return mapped
    return ()


def _parse_effect_text(text: str, *, source: str) -> DamageEffect:
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
    slot = _normalize_slot(str(params.get("部位") or params.get("类型") or ""))
    set_id = str(params.get("套装") or "").strip()
    source = f"{name or '未命名装备'}"
    direct_effects = _parse_effect_keys(params, "效果", source)
    set_effects = _parse_effect_keys(params, "三件套效果", source)
    return {
        "名称": name,
        "部位": slot,
        "套装": set_id,
        "效果": direct_effects,
        "三件套效果": set_effects,
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
    if chest.get("部位") != "胸甲":
        raise ValueError("胸甲槽位必须放置胸甲")
    if gloves.get("部位") != "护手":
        raise ValueError("护手槽位必须放置护手")
    if accessory_a.get("部位") != "配件":
        raise ValueError("配件A槽位必须放置配件")
    if accessory_b.get("部位") != "配件":
        raise ValueError("配件B槽位必须放置配件")
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
        slot = str(item.get("部位") or "").strip()
        if slot == "胸甲":
            catalog["chest"].append(item)
        elif slot == "护手":
            catalog["gloves"].append(item)
        elif slot == "配件":
            catalog["accessories"].append(item)
    return catalog


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
