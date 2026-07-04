# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""
固定配装槽位映射逻辑（纯 Python）。

从 qt_control_dock.py 提取，不依赖 PySide6，可被 Web/CLI/测试复用。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# 固定配装四槽位定义：(槽位键, 显示标签)
FIXED_SLOT_SPECS: list[tuple[str, str]] = [
    ("chest", "胸甲"),
    ("gloves", "手套"),
    ("accessory_a", "饰品A"),
    ("accessory_b", "饰品B"),
]


def slot_to_catalog_key(slot_key: str) -> str:
    """将槽位键映射到 catalog 键（饰品槽共享 accessories）。

    Args:
        slot_key: 槽位标识（chest/gloves/accessory_a/accessory_b）

    Returns:
        catalog 中对应的键名。
    """
    if slot_key in ("accessory_a", "accessory_b"):
        return "accessories"
    return slot_key


@dataclass
class SlotLookupResult:
    """单个槽位的查找结果。"""

    slot_key: str
    catalog_key: str
    selected_name: str | None
    matched_row: dict[str, Any] | None


def lookup_equipment_in_catalog(
    catalog: dict[str, list[dict[str, Any]]],
    slot_key: str,
    selected_name: str | None,
) -> SlotLookupResult:
    """在 catalog 中查找指定名称的装备行。

    Args:
        catalog: 装备 catalog（按部位分组）
        slot_key: 槽位键
        selected_name: 用户选择的装备名称（None 表示未选择）

    Returns:
        SlotLookupResult 包含匹配的行或 None。
    """
    catalog_key = slot_to_catalog_key(slot_key)
    if selected_name is None:
        return SlotLookupResult(slot_key, catalog_key, None, None)
    for row in catalog.get(catalog_key) or []:
        if str(row.get("名称") or "") == selected_name:
            return SlotLookupResult(slot_key, catalog_key, selected_name, row)
    return SlotLookupResult(slot_key, catalog_key, selected_name, None)


def resolve_fixed_loadout_from_names(
    catalog: dict[str, list[dict[str, Any]]],
    slot_names: dict[str, str | None],
) -> dict[str, dict[str, Any] | None]:
    """从四槽位名称解析为装备行字典。

    Args:
        catalog: 装备 catalog
        slot_names: {槽位键: 选择的装备名称}

    Returns:
        {槽位键: 匹配的装备行或 None}
    """
    result: dict[str, dict[str, Any] | None] = {}
    for slot_key in [s[0] for s in FIXED_SLOT_SPECS]:
        lookup = lookup_equipment_in_catalog(
            catalog,
            slot_key,
            slot_names.get(slot_key),
        )
        result[slot_key] = lookup.matched_row
    return result
