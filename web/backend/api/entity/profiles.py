# SPDX-License-Identifier: AGPL-3.0
"""Web 数据设计器 — 多游戏 profile（对齐 tools/designer/data_editor/profiles.py）。"""

from __future__ import annotations

import asyncio
import json as _json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from api.internal.json_utils import REPO_ROOT, load_json, save_json
from fastapi import HTTPException

ENDFIELD_DATA = REPO_ROOT / "games" / "endfield" / "data"
ARKNIGHTS_OPERATORS = REPO_ROOT / "tools" / "arknights_scout" / "output" / "parsed" / "operators.json"


@dataclass(frozen=True)
class EntityDef:
    key: str
    label: str
    path: Path
    columns: tuple[str, ...]


@dataclass(frozen=True)
class ProfileDef:
    id: str
    label: str
    entities: tuple[EntityDef, ...]


PROFILES: dict[str, ProfileDef] = {
    "endfield": ProfileDef(
        id="endfield",
        label="终末地",
        entities=(
            EntityDef(
                "characters", "角色", ENDFIELD_DATA / "characters.json", ("名称", "类型", "星级", "主能力", "副能力")
            ),
            EntityDef("weapons", "武器", ENDFIELD_DATA / "weapons.json", ("名称", "类型", "星级")),
            EntityDef("equipments", "装备", ENDFIELD_DATA / "equipments.json", ("名称", "部位", "稀有度")),
        ),
    ),
    "arknights": ProfileDef(
        id="arknights",
        label="明日方舟",
        entities=(EntityDef("operators", "干员", ARKNIGHTS_OPERATORS, ("名称", "职业", "星级", "分支")),),
    ),
}


def get_profile(profile_id: str) -> ProfileDef:
    profile = PROFILES.get(profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail=f"未知 profile: {profile_id}")
    return profile


def get_entity(profile_id: str, entity_key: str) -> EntityDef:
    profile = get_profile(profile_id)
    for ent in profile.entities:
        if ent.key == entity_key:
            return ent
    raise HTTPException(status_code=404, detail=f"profile {profile_id} 无实体 {entity_key}")


def profiles_metadata() -> list[dict[str, Any]]:
    """供前端渲染 profile / 实体下拉。"""
    out: list[dict[str, Any]] = []
    for profile in PROFILES.values():
        out.append(
            {
                "id": profile.id,
                "label": profile.label,
                "entities": [
                    {
                        "key": ent.key,
                        "label": ent.label,
                        "columns": list(ent.columns),
                        "read_only": False,
                    }
                    for ent in profile.entities
                ],
            }
        )
    return out


def _load_entity_list(ent: EntityDef) -> list[dict[str, Any]]:
    if not ent.path.is_file():
        return []  # 数据文件尚未部署（如 PA 上未解压干员 zip），返回空列表
    try:
        data = load_json(ent.path)
    except _json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"JSON 解析失败: {ent.path.name}: {e}") from e
    if data is None:
        return []
    if not isinstance(data, list):
        raise HTTPException(status_code=500, detail=f"{ent.path.name} 根节点须为数组")
    return data


def _save_entity_list(ent: EntityDef, data: list[dict[str, Any]]) -> None:
    save_json(ent.path, data)


def _find_by_name(data: list[dict[str, Any]], name: str) -> int | None:
    """在数据数组中查找名称为 name 的项，返回索引（未找到时返回 None）。"""
    for i, item in enumerate(data):
        if item.get("名称") == name:
            return i
    return None


def list_entity_rows(profile_id: str, entity_key: str, *, full: bool = False) -> list[dict[str, Any]]:
    """列出指定实体数据（full=True 返回全部字段，否则仅返回 columns）。"""
    ent = get_entity(profile_id, entity_key)
    raw = _load_entity_list(ent)
    if full:
        return raw
    return [{col: row.get(col) for col in ent.columns} for row in raw]


def create_entity_row(profile_id: str, entity_key: str, payload: dict[str, Any]) -> dict[str, str]:
    ent = get_entity(profile_id, entity_key)
    raw = _load_entity_list(ent)
    name = str(payload.get("名称", "")).strip()
    if not name:
        raise HTTPException(status_code=400, detail="缺少字段：名称")
    if _find_by_name(raw, name) is not None:
        raise HTTPException(status_code=409, detail=f"'{name}' 已存在")
    raw.append(payload)
    _save_entity_list(ent, raw)
    return {"message": "ok"}


def update_entity_row(profile_id: str, entity_key: str, name: str, payload: dict[str, Any]) -> dict[str, str]:
    ent = get_entity(profile_id, entity_key)
    raw = _load_entity_list(ent)
    idx = _find_by_name(raw, name)
    if idx is None:
        raise HTTPException(status_code=404, detail=f"'{name}' 未找到")
    merged = dict(raw[idx])
    merged.update(payload)
    if "名称" not in merged:
        merged["名称"] = name
    raw[idx] = merged
    _save_entity_list(ent, raw)
    return {"message": "ok"}


def delete_entity_row(profile_id: str, entity_key: str, name: str) -> dict[str, str]:
    ent = get_entity(profile_id, entity_key)
    raw = _load_entity_list(ent)
    idx = _find_by_name(raw, name)
    if idx is None:
        raise HTTPException(status_code=404, detail=f"'{name}' 未找到")
    raw.pop(idx)
    _save_entity_list(ent, raw)
    return {"message": "ok"}


async def list_entity_rows_async(profile_id: str, entity_key: str, *, full: bool = False) -> list[dict[str, Any]]:
    return await asyncio.to_thread(list_entity_rows, profile_id, entity_key, full=full)


async def create_entity_row_async(profile_id: str, entity_key: str, payload: dict[str, Any]) -> dict[str, str]:
    return await asyncio.to_thread(create_entity_row, profile_id, entity_key, payload)


async def update_entity_row_async(
    profile_id: str, entity_key: str, name: str, payload: dict[str, Any]
) -> dict[str, str]:
    return await asyncio.to_thread(update_entity_row, profile_id, entity_key, name, payload)


async def delete_entity_row_async(profile_id: str, entity_key: str, name: str) -> dict[str, str]:
    return await asyncio.to_thread(delete_entity_row, profile_id, entity_key, name)


__all__: list[str] = []
