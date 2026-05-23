#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""统一装备目录接缝：范围过滤 + 三部位 catalog。"""

from __future__ import annotations

from typing import Any

from calculation.equipment_system import build_equipment_catalog_from_local_rows
from data.loader import DataLoadError, get_equipments

# 与 GUI 下拉文案一致
EQUIPMENT_SCOPE_ALL = "all"
EQUIPMENT_SCOPE_SET = "set_only"
EQUIPMENT_SCOPE_LOOSE = "loose_only"

_SCOPE_LABEL_MAP = {
    "全部装备": EQUIPMENT_SCOPE_ALL,
    "仅套装装备": EQUIPMENT_SCOPE_SET,
    "仅散件装备": EQUIPMENT_SCOPE_LOOSE,
}

_EMPTY_CATALOG: dict[str, list[dict[str, Any]]] = {
    "chest": [],
    "gloves": [],
    "accessories": [],
}


def equipment_scope_from_label(scope_label: str) -> str:
    """将 GUI 装备范围文案解析为内部 scope。"""
    return _SCOPE_LABEL_MAP.get((scope_label or "").strip(), EQUIPMENT_SCOPE_ALL)


def filter_equipment_rows_by_scope(
    rows: list[dict[str, Any]],
    scope: str,
) -> list[dict[str, Any]]:
    """按套装/散件范围过滤装备行。"""
    if scope == EQUIPMENT_SCOPE_ALL:
        return list(rows)
    filtered: list[dict[str, Any]] = []
    for row in rows:
        set_name = str(row.get("套装") or "").strip()
        if scope == EQUIPMENT_SCOPE_SET and not set_name:
            continue
        if scope == EQUIPMENT_SCOPE_LOOSE and set_name:
            continue
        filtered.append(row)
    return filtered


def get_equipment_catalog(
    *,
    scope_label: str = "全部装备",
    equipment_rows: list[dict[str, Any]] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """
    返回全量遍历/预览用的三部位 catalog。

    equipment_rows 为 None 时从统一加载层读取；加载失败时返回空 catalog。
    """
    if equipment_rows is None:
        try:
            equipment_rows = get_equipments()
        except DataLoadError:
            return {key: [] for key in _EMPTY_CATALOG}
    scope = equipment_scope_from_label(scope_label)
    filtered = filter_equipment_rows_by_scope(equipment_rows, scope)
    return build_equipment_catalog_from_local_rows(filtered)


def is_equipment_catalog_complete(catalog: dict[str, list[dict[str, Any]]]) -> bool:
    """三部位均非空时视为可用于全量遍历。"""
    return bool(catalog.get("chest") and catalog.get("gloves") and catalog.get("accessories"))
