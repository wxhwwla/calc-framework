#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""等级曲线物化 — 从 ``成长参数`` 烘焙运行时数组（加载层双读）。"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from calc_framework.inverse.curve import parse_stored_segments
from calc_framework.inverse.materialize import (
    GROWTH_PARAM_KEY,
    has_segment_storage,
    materialize_entity_from_stored_segments,
)

from games.endfield.calc.core.data_generator import (
    CHARACTER_NORMAL_ATTRS,
    CHARACTER_SKILL_ATTRS,
    generate_character_attributes,
    generate_weapon_attributes,
)

DEFAULT_MAX_LEVEL = 90

CHARACTER_BAKED_ATTRS = tuple(CHARACTER_NORMAL_ATTRS) + tuple(CHARACTER_SKILL_ATTRS)
WEAPON_BAKED_ATTRS = ("基础攻击力",)


def _levels_for_entity(entity: dict[str, Any], *, default: int = DEFAULT_MAX_LEVEL) -> list[int]:
    max_level = int(entity.get("最大等级", default))
    return list(range(1, max(max_level, 1) + 1))


def materialize_character_entity(char: dict[str, Any]) -> dict[str, Any]:
    """若含 ``成长参数`` 则烘焙曲线字段，否则原样返回。

    支持 legacy 顶层属性 dict 与 ``segments[]`` 多段形态（ADR-0026）。
    """
    params = char.get(GROWTH_PARAM_KEY)
    if isinstance(params, dict) and params and has_segment_storage(params):
        out = materialize_entity_from_stored_segments(char, growth_key=GROWTH_PARAM_KEY)
        seg_lens = [int(e.get("length", 0)) for e in parse_stored_segments(params)]
        max_len = max(seg_lens) if seg_lens else DEFAULT_MAX_LEVEL
        out["等级"] = list(range(1, max(max_len, 1) + 1))
        return out
    if not isinstance(params, dict) or not params:
        return char
    baked = generate_character_attributes(params)
    out = deepcopy(char)
    for key, value in baked.items():
        out[key] = value
    if "等级" not in out or not isinstance(out.get("等级"), list):
        out["等级"] = _levels_for_entity(out)
    return out


def materialize_weapon_entity(weapon: dict[str, Any]) -> dict[str, Any]:
    """若含 ``成长参数`` 则烘焙武器曲线，否则原样返回。"""
    params = weapon.get(GROWTH_PARAM_KEY)
    if isinstance(params, dict) and params and has_segment_storage(params):
        out = materialize_entity_from_stored_segments(weapon, growth_key=GROWTH_PARAM_KEY)
        seg_lens = [int(e.get("length", 0)) for e in parse_stored_segments(params)]
        max_len = max(seg_lens) if seg_lens else DEFAULT_MAX_LEVEL
        out["等级"] = list(range(1, max(max_len, 1) + 1))
        return out
    if not isinstance(params, dict) or not params:
        return weapon
    baked = generate_weapon_attributes(params)
    out = deepcopy(weapon)
    for key, value in baked.items():
        out[key] = value
    if "等级" not in out or not isinstance(out.get("等级"), list):
        out["等级"] = _levels_for_entity(out)
    return out


def materialize_character_list(characters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """批量物化角色列表（loader 调用）。"""
    return [materialize_character_entity(c) for c in characters]


def materialize_weapon_list(weapons: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """批量物化武器列表（loader 调用）。"""
    return [materialize_weapon_entity(w) for w in weapons]


def strip_baked_curve_arrays(entity: dict[str, Any], *, kind: str) -> dict[str, Any]:
    """移除可由 ``成长参数`` 再生的数组字段（compact 工具用）。"""
    out = deepcopy(entity)
    keys = CHARACTER_BAKED_ATTRS if kind == "character" else WEAPON_BAKED_ATTRS
    for key in keys:
        out.pop(key, None)
    if kind == "weapon":
        for bonus_key in list(out.keys()):
            if isinstance(bonus_key, str) and bonus_key.endswith("+") and bonus_key != "攻击力+":
                if isinstance(out.get(bonus_key), list):
                    out.pop(bonus_key, None)
    out.pop("等级", None)
    return out
