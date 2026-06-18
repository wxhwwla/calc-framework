#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""等级曲线烘焙：录入与 BWIKI 同步共用的唯一接缝。"""

from __future__ import annotations

from typing import Any

from games.endfield.calc.core.data_generator import (
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
    sk1_dt: list[str] | None = None,
    sk2_dt: list[str] | None = None,
    sk3_dt: list[str] | None = None,
    base_hp: dict[str, Any] | None = None,
    base_defense: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """由 seed / 反推参数生成角色四维、攻击、生命、防御与技能曲线字段。"""
    params: dict[str, Any] = {
        "力量": strength,
        "敏捷": agility,
        "智识": intellect,
        "意志": will,
        "基础攻击力": base_atk,
        "战技倍率": sk1,
        "连携技倍率": sk2,
        "终结技倍率": sk3,
    }
    if base_hp is not None:
        params["基础生命值"] = base_hp
    if base_defense is not None:
        params["基础防御力"] = base_defense
    attrs = generate_character_attributes(params)

    if sk1_dt:
        attrs["战技段伤害类型"] = list(sk1_dt)  # type: ignore[assignment]

    if sk2_dt:
        attrs["连携技段伤害类型"] = list(sk2_dt)  # type: ignore[assignment]

    if sk3_dt:
        attrs["终结技段伤害类型"] = list(sk3_dt)  # type: ignore[assignment]

    return attrs


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
