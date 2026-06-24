# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""搜索请求 catalog 解析 — 服务端加载武器/装备，替代客户端全量 POST。"""

from __future__ import annotations

from typing import Any

from games.endfield.data_loading.equipment_catalog import get_equipment_catalog
from games.endfield.data_loading.loader import get_weapons


def _catalog_is_empty(catalog: dict[str, list[dict[str, Any]]] | None) -> bool:
    if not catalog:
        return True
    return all(not entries for entries in catalog.values())


def resolve_equipment_catalog(
    catalog: dict[str, list[dict[str, Any]]] | None,
    *,
    equipment_scope_label: str,
) -> dict[str, list[dict[str, Any]]]:
    """空或未传装备目录时从磁盘按 scope 加载。"""
    if not _catalog_is_empty(catalog):
        return dict(catalog or {})
    return get_equipment_catalog(scope_label=equipment_scope_label)


def filter_weapons_by_scope(
    all_weapons: list[dict[str, Any]],
    *,
    char_data: dict[str, Any],
    current_weapon: dict[str, Any],
    weapon_scope_label: str,
    weapon_candidate_names: list[str] | None = None,
) -> list[dict[str, Any]]:
    """按武器范围与可选名称列表过滤武器行。"""
    scope = (weapon_scope_label or "").strip()
    weapon_type = str(char_data.get("武器", ""))
    current_star = current_weapon.get("星级")
    current_name = current_weapon.get("名称")
    name_filter: set[str] | None = None
    if weapon_candidate_names:
        name_filter = {str(n).strip() for n in weapon_candidate_names if str(n).strip()}

    filtered: list[dict[str, Any]] = []
    for weapon in all_weapons:
        name = str(weapon.get("名称", ""))
        if name_filter is not None and name not in name_filter:
            continue
        if weapon.get("类型") != weapon_type:
            continue
        if scope == "同类型同星级" and weapon.get("星级") != current_star:
            continue
        if scope == "当前武器" and name != current_name:
            continue
        filtered.append(weapon)
    return filtered


def resolve_weapon_candidates(
    all_weapons: list[dict[str, Any]] | None,
    *,
    char_data: dict[str, Any],
    current_weapon: dict[str, Any],
    weapon_scope_label: str,
    char_level: int,
    weapon_level: int,
    trust_level: int,
    weapon_candidate_names: list[str] | None = None,
) -> list[dict[str, Any]]:
    """未传 ``all_weapons`` 时从磁盘加载并按 scope 过滤。"""
    weapons = list(all_weapons) if all_weapons else list(get_weapons())
    return filter_weapons_by_scope(
        weapons,
        char_data=char_data,
        current_weapon=current_weapon,
        weapon_scope_label=weapon_scope_label,
        weapon_candidate_names=weapon_candidate_names,
    )


def weapon_rows_for_search(
    all_weapons: list[dict[str, Any]] | None,
    *,
    char_data: dict[str, Any],
    current_weapon: dict[str, Any],
    weapon_scope_label: str,
    char_level: int,
    weapon_level: int,
    trust_level: int,
    weapon_candidate_names: list[str] | None = None,
) -> list[dict[str, Any]]:
    """返回搜索作业所需的武器 dict 列表（含 scope 内全部字段）。"""
    if all_weapons:
        scoped = filter_weapons_by_scope(
            list(all_weapons),
            char_data=char_data,
            current_weapon=current_weapon,
            weapon_scope_label=weapon_scope_label,
            weapon_candidate_names=weapon_candidate_names,
        )
        if scoped:
            return scoped
    return resolve_weapon_candidates(
        None,
        char_data=char_data,
        current_weapon=current_weapon,
        weapon_scope_label=weapon_scope_label,
        char_level=char_level,
        weapon_level=weapon_level,
        trust_level=trust_level,
        weapon_candidate_names=weapon_candidate_names,
    )


__all__ = [
    "resolve_equipment_catalog",
    "resolve_weapon_candidates",
    "weapon_rows_for_search",
]
