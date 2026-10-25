#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""武器属性平值/百分比加成计算辅助函数（提取自 attribute_zone.py）。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .attribute_zone import AttributeZoneManager


def compute_attr_weapon_bonus(
    *,
    attr: str,
    attr_is_main: bool,
    attr_is_sub: bool,
    weapon: dict[str, Any] | None,
    manager: AttributeZoneManager,
    sa1_name: str,
    sa1_level: int,
    sa2_name: str,
    sa2_level: int,
    sa3_name: str,
    sa3_level: int,
    ws_name: str,
    ws_level: int,
    ws_stack: int,
    ws2_name: str,
    ws2_level: int,
    ws2_stack: int,
    main_attr: str,
    sub_attr: str,
    trust_level: int,
) -> tuple[float, float]:
    flat_bonus = 0.0

    pct_bonus = 0.0

    if not weapon:
        return 0.0, 0.0

    def _resolve_level(effect: str) -> int:
        """根据效果名查找对应特殊技能等级。"""
        if effect == sa1_name:
            return sa1_level

        if effect == sa2_name:
            return sa2_level

        if effect == sa3_name:
            return sa3_level

        return 1

    def _should_skip(effect: str) -> bool:
        """should skip。"""
        return effect == sa3_name and sa3_level == 0

    def _classify(effect: str) -> str:
        """将效果名分类为内部类型（main_flat/sub_flat/main_pct/sub_pct/both_pct）。"""
        if effect == "主能力值+":
            return "main_flat"

        if effect == "副能力值+":
            return "sub_flat"

        if effect == f"{attr}+":
            return "attr_flat"

        if attr_is_main and effect == "主能力+":
            return "main_pct"

        if attr_is_sub and effect == "副能力+":
            return "sub_pct"

        if (attr_is_main or attr_is_sub) and effect == "全能力+":
            return "both_pct"

        return ""

    def _classify_and_add(effect: str, value: float) -> None:
        nonlocal flat_bonus, pct_bonus

        category = _classify(effect)

        if (
            (category == "main_flat" and attr_is_main)
            or (category == "sub_flat" and attr_is_sub)
            or category == "attr_flat"
        ):
            flat_bonus += value

        elif category == "main_pct" or category == "sub_pct" or category == "both_pct":
            pct_bonus += value
        """classify and add。"""

    for skill in weapon.get("normal_skills", []):
        if not isinstance(skill, dict):
            continue

        effect = skill.get("effect", "")

        if _should_skip(effect):
            continue

        value = manager._get_weapon_bonus(skill.get("curve", []), _resolve_level(effect))

        _classify_and_add(effect, value)

    for bonus_key in [key for key in weapon if key.endswith("+")]:
        if _should_skip(bonus_key):
            continue

        value = manager._get_weapon_bonus(weapon[bonus_key], _resolve_level(bonus_key))

        _classify_and_add(bonus_key, value)

    from games.endfield.calc.skills.special_fields import (
        add_special_picks_to_ability_pct,
        add_special_picks_to_main_sub_bonus,
    )

    md, sd = add_special_picks_to_main_sub_bonus(
        weapon,
        ws_name=ws_name,
        ws_level=ws_level,
        ws_stack=ws_stack,
        ws2_name=ws2_name,
        ws2_level=ws2_level,
        ws2_stack=ws2_stack,
        main_attr=main_attr,
        sub_attr=sub_attr,
    )

    mp, sp = add_special_picks_to_ability_pct(
        weapon,
        ws_name=ws_name,
        ws_level=ws_level,
        ws_stack=ws_stack,
        ws2_name=ws2_name,
        ws2_level=ws2_level,
        ws2_stack=ws2_stack,
        main_attr=main_attr,
        sub_attr=sub_attr,
    )

    if attr_is_main:
        flat_bonus += md

        pct_bonus += mp

    elif attr_is_sub:
        flat_bonus += sd

        pct_bonus += sp

    if attr_is_main and trust_level > 0:
        trust_add = [0, 10, 25, 40, 60]

        if 0 <= trust_level < len(trust_add):
            flat_bonus += trust_add[trust_level]

    """compute attr weapon bonus。"""
    return flat_bonus, pct_bonus
