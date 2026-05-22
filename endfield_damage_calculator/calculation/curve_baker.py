#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""等级曲线烘焙：录入与 BWIKI 同步共用的唯一接缝。"""

from __future__ import annotations

from typing import Any

from calculation.data_generator import (
    generate_character_attributes,
    generate_weapon_attributes,
)


def bake_character_curves(
    *,
    strength: dict[str, Any],
    agility: dict[str, Any],
    intellect: dict[str, Any],
    will: dict[str, Any],
    base_atk: dict[str, Any],
    sk1: list[dict[str, Any]],
    sk2: list[dict[str, Any]],
    sk3: list[dict[str, Any]],
) -> dict[str, Any]:
    """由 seed / 反推参数生成角色四维、攻击与技能曲线字段。"""
    return generate_character_attributes(
        {
            "力量": strength,
            "敏捷": agility,
            "智识": intellect,
            "意志": will,
            "基础攻击力": base_atk,
            "战技倍率": sk1,
            "连携技倍率": sk2,
            "终结技倍率": sk3,
        }
    )


def bake_weapon_curves(
    *,
    base_atk: dict[str, Any],
    bonus_attrs: dict[str, dict[str, Any]] | None,
) -> dict[str, Any]:
    """由 seed / 反推参数生成武器基础攻击与 xxx+ 曲线字段。"""
    params: dict[str, Any] = {"基础攻击力": base_atk}
    if bonus_attrs:
        for key, p in bonus_attrs.items():
            attr = key if key.endswith("+") else f"{key}+"
            params[attr] = p
    return generate_weapon_attributes(params)
