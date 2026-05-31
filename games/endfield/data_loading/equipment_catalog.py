#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""统一装备目录接缝：范围过滤 + 三部位 catalog。"""

from __future__ import annotations

from typing import Any

from games.endfield.calc.equipment.system import build_equipment_catalog_from_local_rows
from games.endfield.data_loading.loader import DataLoadError, get_equipments

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


def catalog_has_any_rows(catalog: dict[str, list[dict[str, Any]]]) -> bool:
    """任一部位有条目（可能仍不完整）。"""
    return bool(catalog.get("chest") or catalog.get("gloves") or catalog.get("accessories"))


def is_equipment_catalog_complete(catalog: dict[str, list[dict[str, Any]]]) -> bool:
    """三部位均非空时视为可用于全量遍历。"""
    return bool(catalog.get("chest") and catalog.get("gloves") and catalog.get("accessories"))


def catalog_status_message(catalog: dict[str, list[dict[str, Any]]]) -> str | None:
    """
    返回装备 catalog 不可用时的用户可读说明；可用时返回 None。

    missing_data：完全未加载；incomplete：有数据但三部位不齐。
    """
    if not catalog_has_any_rows(catalog):
        return "未加载到本地装备数据，请先执行 sync_equipments.py --apply。"
    if not is_equipment_catalog_complete(catalog):
        return "装备数据不完整（缺护甲/护手/配件），请先执行 sync_equipments.py --apply 同步 Wiki 装备。"
    return None


def catalog_full_search_error(catalog: dict[str, list[dict[str, Any]]]) -> str | None:
    """全量遍历/搜索作业不可用时的错误文案；可用时返回 None。"""
    status = catalog_status_message(catalog)
    if status is None:
        return None
    if is_equipment_catalog_complete(catalog):
        return None
    if not catalog_has_any_rows(catalog):
        return status
    return "装备数据不完整（缺护甲/护手/配件）。请先执行 sync_equipments.py --apply 同步 Wiki 装备。"


def catalog_preview_status_lines(
    catalog: dict[str, list[dict[str, Any]]],
    *,
    mode_label: str,
) -> list[str] | None:
    """快速预览不可用时的说明行；可用时返回 None。"""
    if not catalog_has_any_rows(catalog):
        return [
            f"计算模式: {mode_label}",
            "未加载到本地装备数据，请先执行 sync_equipments.py --apply。",
        ]
    if not is_equipment_catalog_complete(catalog):
        return [
            f"计算模式: {mode_label}",
            "装备数据不完整（缺护甲/护手/配件），无法进行预览。",
        ]
    return None


def sample_equipment_catalog(
    catalog: dict[str, list[dict[str, Any]]],
    *,
    per_slot: int = 2,
) -> dict[str, list[dict[str, Any]]]:
    """快速预览用：每部位取前 per_slot 件。"""
    limit = max(0, int(per_slot))
    return {
        "chest": list(catalog.get("chest") or [])[:limit],
        "gloves": list(catalog.get("gloves") or [])[:limit],
        "accessories": list(catalog.get("accessories") or [])[:limit],
    }
