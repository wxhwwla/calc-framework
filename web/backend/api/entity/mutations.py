# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""游戏 JSON 数据 CURD 操作 — 角色/武器/装备增删改 + 公式反推（FastAPI 与 WSGI 共用）。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from api.entity.inverse_payloads import (
    inverse_formula_payload,
    inverse_milestones_payload,
    inverse_segment_payload,
)
from api.internal.json_utils import ENDFIELD_DATA_ROOT

DATA_ROOT = ENDFIELD_DATA_ROOT
CHARACTERS_PATH = DATA_ROOT / "characters.json"
WEAPONS_PATH = DATA_ROOT / "weapons.json"
EQUIPMENTS_PATH = DATA_ROOT / "equipments.json"


def _save_json(path: Path, data: list[dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _find_by_name(data: list[dict[str, Any]], name: str) -> int | None:
    for i, item in enumerate(data):
        if item.get("名称") == name:
            return i
    return None


def create_character(data: dict[str, Any]) -> dict[str, str]:
    from api.entity.profiles import create_entity_row

    return create_entity_row("endfield", "characters", data)


def update_character(name: str, data: dict[str, Any]) -> dict[str, str]:
    """更新指定角色数据。"""
    from api.entity.profiles import update_entity_row

    return update_entity_row("endfield", "characters", name, data)


def delete_character(name: str) -> dict[str, str]:
    """删除指定角色数据。"""
    from api.entity.profiles import delete_entity_row

    return delete_entity_row("endfield", "characters", name)


def create_weapon(data: dict[str, Any]) -> dict[str, str]:
    from api.entity.profiles import create_entity_row

    return create_entity_row("endfield", "weapons", data)


def update_weapon(name: str, data: dict[str, Any]) -> dict[str, str]:
    from api.entity.profiles import update_entity_row

    return update_entity_row("endfield", "weapons", name, data)


def delete_weapon(name: str) -> dict[str, str]:
    from api.entity.profiles import delete_entity_row

    return delete_entity_row("endfield", "weapons", name)


def create_equipment(data: dict[str, Any]) -> dict[str, str]:
    """新增装备数据记录。"""
    from api.entity.profiles import create_entity_row

    return create_entity_row("endfield", "equipments", data)


def update_equipment(name: str, data: dict[str, Any]) -> dict[str, str]:
    """更新指定装备数据。"""
    from api.entity.profiles import update_entity_row

    return update_entity_row("endfield", "equipments", name, data)


def delete_equipment(name: str) -> dict[str, str]:
    from api.entity.profiles import delete_entity_row

    return delete_entity_row("endfield", "equipments", name)


__all__ = [
    "create_character",
    "create_equipment",
    "create_weapon",
    "delete_character",
    "delete_equipment",
    "delete_weapon",
    "inverse_formula_payload",
    "inverse_milestones_payload",
    "inverse_segment_payload",
    "update_character",
    "update_equipment",
    "update_weapon",
]
