#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""能力乘区：带明细的快捷计算。

从 ``attribute_zone.py`` 拆出（P2-07），保留原始计算逻辑。
"""

import warnings
from typing import Any

from ._attribute_zone_bonus import compute_attr_weapon_bonus as _compute_attr_weapon_bonus
from .attribute_zone_base import AttributeZoneManager

__all__ = ["calculate_attribute_zones_with_details"]


def calculate_attribute_zones_with_details(
    character: dict[str, Any] | None,
    weapon: dict[str, Any] | None,
    level: int = 1,
    sa1_name: str = "",
    sa1_level: int = 1,
    sa2_name: str = "",
    sa2_level: int = 1,
    sa3_name: str = "",
    sa3_level: int = 0,
    ws_name: str = "",
    ws_level: int = 1,
    ws_stack: int = 1,
    ws2_name: str = "",
    ws2_level: int = 1,
    ws2_stack: int = 1,
    trust_level: int = 0,
    normal_skill_1_name: str = "",
    normal_skill_1_level: int = 1,
    normal_skill_2_name: str = "",
    normal_skill_2_level: int = 1,
    normal_skill_3_name: str = "",
    normal_skill_3_level: int = 0,
    special_skill_1_name: str = "",
    special_skill_1_level: int = 1,
    special_skill_1_stack: int = 1,
    special_skill_2_name: str = "",
    special_skill_2_level: int = 1,
    special_skill_2_stack: int = 1,
) -> dict[str, dict[str, float]]:
    """

    快捷函数：计算能力乘区，返回详细信息



    参数：

        character: 角色数据字典

        weapon: 武器数据字典

        level: 等级（1-90）

        sa1_name: 第一个特殊能力名称（如敏捷+）

        sa1_level: 第一个特殊能力等级（1-9）

        sa2_name: 第二个特殊能力名称（如物理伤害+）

        sa2_level: 第二个特殊能力等级（1-9）

        sa3_name: 第三条附加属性名称

        sa3_level: 第三条附加属性等级（无第三条时为 0）

        ws_name: 武器「特殊能力」字段名称

        ws_level: 武器「特殊能力」等级（0 表示关闭）

        trust_level: 信赖等级（0-4），信赖加成会加到角色主能力上



    返回：

        包含详细计算信息的字典：

        {

            '力量': {'base': 基础值, 'bonus': 武器加成, 'total': 总值},

            '敏捷': {'base': 基础值, 'bonus': 武器加成, 'total': 总值},

            ...

        }

    """

    legacy_used = bool(sa1_name or sa2_name or sa3_name or ws_name or ws2_name)

    new_used = bool(
        normal_skill_1_name
        or normal_skill_2_name
        or normal_skill_3_name
        or special_skill_1_name
        or special_skill_2_name
    )

    if legacy_used and not new_used:
        warnings.warn(
            "参数 sa*/ws* 已弃用，请改用 normal_skill_* / special_skill_*。",
            DeprecationWarning,
            stacklevel=2,
        )

    manager = AttributeZoneManager()

    sa1_name = normal_skill_1_name or sa1_name

    sa1_level = normal_skill_1_level if normal_skill_1_name else sa1_level

    sa2_name = normal_skill_2_name or sa2_name

    sa2_level = normal_skill_2_level if normal_skill_2_name else sa2_level

    sa3_name = normal_skill_3_name or sa3_name

    sa3_level = normal_skill_3_level if normal_skill_3_name else sa3_level

    ws_name = special_skill_1_name or ws_name

    ws_level = special_skill_1_level if special_skill_1_name else ws_level

    ws_stack = special_skill_1_stack if special_skill_1_name else ws_stack

    ws2_name = special_skill_2_name or ws2_name

    ws2_level = special_skill_2_level if special_skill_2_name else ws2_level

    ws2_stack = special_skill_2_stack if special_skill_2_name else ws2_stack

    level_index = level - 1

    main_attr = character.get("主能力", "") if character else ""

    sub_attr = character.get("副能力", "") if character else ""

    result = {}

    for attr in manager.ATTRIBUTES:
        base_value = 0.0

        if character and attr in character and isinstance(character[attr], list):
            attr_list = character[attr]

            if 0 <= level_index < len(attr_list):
                base_value = float(attr_list[level_index])

        is_main = attr == main_attr

        is_sub = attr == sub_attr

        flat_bonus, pct_bonus = _compute_attr_weapon_bonus(
            attr=attr,
            attr_is_main=is_main,
            attr_is_sub=is_sub,
            weapon=weapon,
            manager=manager,
            sa1_name=sa1_name,
            sa1_level=int(sa1_level),
            sa2_name=sa2_name,
            sa2_level=int(sa2_level),
            sa3_name=sa3_name,
            sa3_level=int(sa3_level),
            ws_name=ws_name,
            ws_level=int(ws_level),
            ws_stack=int(ws_stack),
            ws2_name=ws2_name,
            ws2_level=int(ws2_level),
            ws2_stack=int(ws2_stack),
            main_attr=main_attr,
            sub_attr=sub_attr,
            trust_level=int(trust_level),
        )

        if is_main or is_sub:
            total = (base_value + flat_bonus) * (1.0 + pct_bonus / 100.0)

        else:
            total = base_value + flat_bonus

        result[attr] = {
            "base": base_value,
            "bonus": flat_bonus,
            "pct_bonus": pct_bonus,
            "total": total,
        }

    return result
