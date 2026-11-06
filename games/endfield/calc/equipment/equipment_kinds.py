#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""装备种类常量与部位推断（P2-07 从 ``system.py`` 拆出）。"""

from __future__ import annotations

from typing import Any

__all__ = [
    "EQUIPMENT_KIND_ACCESSORY",
    "EQUIPMENT_KIND_ARMOR",
    "EQUIPMENT_KIND_GLOVES",
    "equipment_kind",
    "infer_equipment_slot",
]

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


def _normalize_slot(slot_raw: str) -> str:
    """规范化装备部位名（支持别名映射）。"""
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
