# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""Web 层实体格式化 — compact / runtime / raw 与计算前物化。"""

from __future__ import annotations

from typing import Any, Literal

from calc_framework.inverse.materialize import GROWTH_PARAM_KEY

from games.endfield.data_loading.curve_materialize import (
    CHARACTER_BAKED_ATTRS,
    materialize_character_entity,
    materialize_weapon_entity,
    strip_baked_curve_arrays,
)

EntityFormat = Literal["compact", "runtime", "raw"]
DEFAULT_ENTITY_FORMAT: EntityFormat = "compact"
VALID_ENTITY_FORMATS: frozenset[str] = frozenset({"compact", "runtime", "raw"})


def parse_entity_format(value: str | None, *, default: EntityFormat = DEFAULT_ENTITY_FORMAT) -> EntityFormat:
    """解析 ``format`` 查询参数。"""
    if not value:
        return default
    fmt = value.strip().lower()
    if fmt in VALID_ENTITY_FORMATS:
        return fmt  # type: ignore[return-value]
    return default


def has_growth_params(entity: dict[str, Any]) -> bool:
    """实体是否含非空 ``成长参数``。"""
    params = entity.get(GROWTH_PARAM_KEY)
    return isinstance(params, dict) and bool(params)


def _has_baked_curve_arrays(entity: dict[str, Any], *, kind: str) -> bool:
    if kind == "character":
        keys = CHARACTER_BAKED_ATTRS
    else:
        keys = ("基础攻击力",)
    for key in keys:
        val = entity.get(key)
        if isinstance(val, list) and val:
            return True
    if kind == "weapon":
        for key, val in entity.items():
            if isinstance(key, str) and key.endswith("+") and key != "攻击力+" and isinstance(val, list) and val:
                return True
    return False


def format_character_entity(char: dict[str, Any], fmt: EntityFormat) -> dict[str, Any]:
    """按 ``compact`` / ``runtime`` / ``raw`` 返回角色 dict。"""
    if fmt == "raw":
        return char
    if fmt == "runtime":
        return materialize_character_entity(char)
    if has_growth_params(char):
        return strip_baked_curve_arrays(char, kind="character")
    return char


def format_weapon_entity(weapon: dict[str, Any], fmt: EntityFormat) -> dict[str, Any]:
    """按 ``compact`` / ``runtime`` / ``raw`` 返回武器 dict。"""
    if fmt == "raw":
        return weapon
    if fmt == "runtime":
        return materialize_weapon_entity(weapon)
    if has_growth_params(weapon):
        return strip_baked_curve_arrays(weapon, kind="weapon")
    return weapon


def format_entity_list(
    entities: list[dict[str, Any]],
    fmt: EntityFormat,
    *,
    kind: str,
) -> list[dict[str, Any]]:
    """批量格式化实体列表。"""
    formatter = format_character_entity if kind == "character" else format_weapon_entity
    return [formatter(item, fmt) for item in entities]


def prepare_character_for_compute(char: dict[str, Any]) -> dict[str, Any]:
    """计算/搜索前物化：含 ``成长参数`` 且无烘焙数组时展开曲线。"""
    if has_growth_params(char):
        return materialize_character_entity(char)
    return char


def prepare_weapon_for_compute(weapon: dict[str, Any]) -> dict[str, Any]:
    """计算/搜索前物化武器曲线。"""
    if has_growth_params(weapon):
        return materialize_weapon_entity(weapon)
    return weapon


def compact_entity_for_transport(entity: dict[str, Any], *, kind: str) -> dict[str, Any]:
    """传输用 compact（有 ``成长参数`` 时去掉可再生的数组字段）。"""
    if kind == "character":
        return format_character_entity(entity, "compact")
    return format_weapon_entity(entity, "compact")
