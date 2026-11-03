#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""能力乘区模块。

实现力量、敏捷、智识、意志四个属性乘区的计算逻辑。

P2-07 拆分：乘区类迁至 ``attribute_zone_base.py``，带明细的快捷函数迁至
``attribute_zone_details.py``；本模块继续再导出，既有导入路径不变。
"""

from typing import Any

from .attribute_zone_base import AttributeMultiplierZone, AttributeZoneManager
from .attribute_zone_details import calculate_attribute_zones_with_details

__all__ = [
    "AttributeMultiplierZone",
    "AttributeZoneManager",
    "calculate_attribute_zones",
    "calculate_attribute_zones_with_details",
]


def calculate_attribute_zones(
    character: dict[str, Any] | None, weapon: dict[str, Any] | None, level: int = 1
) -> dict[str, float]:
    """

    快捷函数：计算能力乘区



    参数：

        character: 角色数据字典

        weapon: 武器数据字典

        level: 等级（1-90）



    返回：

        包含四个属性乘区值的字典

    """

    manager = AttributeZoneManager()

    manager.setup_from_data(character, weapon, level)

    return manager.calculate_all()
