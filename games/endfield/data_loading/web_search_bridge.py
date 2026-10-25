# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""Web 搜索请求归一化（与桌面 GUI SearchJobInputs 对齐）。"""

from __future__ import annotations

from typing import Any

from games.endfield.calc.loadout.slot_search import FixedLoadoutSelection
from games.endfield.data_loading.web_loadout_bridge import (
    resolve_fixed_loadout_selection,
    resolve_search_skill_fields,
    weapon_preset_from_web_values,
)


def resolve_search_fixed_loadout(req: Any) -> FixedLoadoutSelection:
    """从 SearchRequest / dict 解析固定配装（名称 → 装备 dict）。"""
    catalog = getattr(req, "equipment_catalog", None) or {}
    names = getattr(req, "fixed_equipment_names", None) or {}
    raw = getattr(req, "fixed_loadout", None)
    return resolve_fixed_loadout_selection(
        fixed_equipment_names=names if isinstance(names, dict) else {},
        equipment_catalog=catalog if isinstance(catalog, dict) else {},
        fixed_loadout_raw=raw if isinstance(raw, dict) else None,
    )


def enrich_search_request_fields(req: Any) -> dict[str, Any]:
    """补全 skill_* / weapon 技能字段，返回 model_copy(update=...) 用的 dict。"""
    s1 = int(getattr(req, "skill_1_level", 0) or 0)
    s2 = int(getattr(req, "skill_2_level", 0) or 0)
    s3 = int(getattr(req, "skill_3_level", 0) or 0)
    skill_name, skill_type, skill_multiplier, damage_type = resolve_search_skill_fields(
        req.char_data,
        skill_1_level=s1,
        skill_2_level=s2,
        skill_3_level=s3,
    )
    wsv = getattr(req, "weapon_skill_values", None) or {}
    normal, special = weapon_preset_from_web_values(wsv if isinstance(wsv, dict) else {})
    updates: dict[str, Any] = {
        "skill_name": skill_name,
        "skill_type": skill_type,
        "skill_multiplier": skill_multiplier,
        "damage_type": damage_type,
        "weapon_normal_levels": normal,
        "weapon_special_states": special,
    }
    if not s1 and not s2 and not s3:
        updates.update({"skill_1_level": 8, "skill_2_level": 8, "skill_3_level": 8})
    return updates
