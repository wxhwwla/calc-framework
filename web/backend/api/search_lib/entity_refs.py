# SPDX-License-Identifier: AGPL-3.0
"""Web 实体引用 — 名称 + 可选 ``成长参数``，服务端可补全 catalog。"""

from __future__ import annotations

from typing import Any

from calc_framework.inverse.materialize import GROWTH_PARAM_KEY
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field


class WebEntityRef(BaseModel):
    """传输用实体引用（可仅含 ``名称`` 与 ``成长参数``）。"""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    name: str = Field(alias="名称", description="实体名称")
    growth_params: dict[str, Any] | None = Field(default=None, alias="成长参数")
    level: int | None = Field(default=None, alias="等级")
    trust_level: int | None = Field(default=None, description="信赖等级（角色）")


def entity_needs_catalog_load(data: dict[str, Any], *, kind: str) -> bool:
    """判断是否需从磁盘 catalog 补全实体字段。"""
    if kind == "character":
        return not data.get("武器") and not data.get("类型")
    return not data.get("类型")


def _load_entity_by_name(name: str, *, kind: str) -> dict[str, Any] | None:
    from games.endfield.data_loading.loader import get_characters, get_weapons

    rows = get_characters() if kind == "character" else get_weapons()
    for row in rows:
        if str(row.get("名称", "")) == name:
            return dict(row)
    return None


def merge_entity_ref(data: dict[str, Any], *, kind: str) -> dict[str, Any]:
    """将引用 dict 与磁盘 catalog 合并（引用字段优先）。"""
    name = str(data.get("名称") or data.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail=f"缺少{'角色' if kind == 'character' else '武器'}名称")
    if not entity_needs_catalog_load(data, kind=kind):
        return dict(data)
    base = _load_entity_by_name(name, kind=kind)
    if base is None:
        raise HTTPException(status_code=404, detail=f"未找到{'角色' if kind == 'character' else '武器'}: {name}")
    merged = dict(base)
    for key, value in data.items():
        if key in ("名称", "name"):
            continue
        if value is None:
            continue
        if key == GROWTH_PARAM_KEY or key == "成长参数":
            if isinstance(value, dict) and value:
                merged[GROWTH_PARAM_KEY] = value
            continue
        merged[key] = value
    merged["名称"] = name
    return merged


def resolve_character_ref(
    data: dict[str, Any],
    *,
    char_level: int,
    trust_level: int,
) -> dict[str, Any]:
    """解析角色引用并物化曲线。"""
    from web.backend.data_materialize import prepare_character_for_compute

    merged = merge_entity_ref(data, kind="character")
    out = prepare_character_for_compute(merged)
    if char_level > 0:
        out["当前等级"] = int(char_level)
    if trust_level >= 0:
        out["信赖等级"] = int(trust_level)
    return out


def resolve_weapon_ref(data: dict[str, Any], *, weapon_level: int) -> dict[str, Any]:
    """解析武器引用并物化曲线。"""
    from web.backend.data_materialize import prepare_weapon_for_compute

    merged = merge_entity_ref(data, kind="weapon")
    out = prepare_weapon_for_compute(merged)
    if weapon_level > 0:
        out["当前等级"] = int(weapon_level)
    return out


__all__ = [
    "WebEntityRef",
    "entity_needs_catalog_load",
    "merge_entity_ref",
    "resolve_character_ref",
    "resolve_weapon_ref",
]
