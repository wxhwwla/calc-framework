#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""能力乘区基类与管理器。

从 ``attribute_zone.py`` 拆出（P2-07），保留原始计算逻辑。
"""

from typing import Any

from .base_zone import BaseZone

__all__ = ["AttributeMultiplierZone", "AttributeZoneManager"]


class AttributeMultiplierZone(BaseZone):
    """

    能力乘区基类



    力量、敏捷、智识、意志四个乘区的基类。

    """

    def __init__(self, attribute_name: str, base_value: float = 0.0):
        super().__init__(name=f"{attribute_name}乘区", description=f"{attribute_name}属性乘区")

        self.attribute_name = attribute_name

        self.set_params(**{attribute_name: base_value})

    def calculate(self) -> float:
        """执行计算。
                返回:
        计算结果。
        """
        return self._params.get(self.attribute_name, 0.0)


class AttributeZoneManager:
    """

    能力乘区管理器



    统一管理力量、敏捷、智识、意志四个乘区。



    使用方式：

        manager = AttributeZoneManager()

        manager.setup_from_data(character_data, weapon_data, level=90)

        results = manager.calculate_all()

    """

    ATTRIBUTES = ["力量", "敏捷", "智识", "意志"]

    def __init__(self):
        self._zones: dict[str, AttributeMultiplierZone] = {
            attr: AttributeMultiplierZone(attr) for attr in self.ATTRIBUTES
        }

    def setup_from_data(self, character: dict[str, Any] | None, weapon: dict[str, Any] | None, level: int = 1) -> None:
        """

        从角色和武器数据设置乘区



        参数：

            character: 角色数据字典

            weapon: 武器数据字典

            level: 等级（1-90）

        """

        if character is None:
            return

        self._setup_from_character(character, level)

        if weapon is not None:
            self._setup_from_weapon(character, weapon)

    def _setup_from_character(self, character: dict[str, Any], level: int) -> None:
        """从角色数据设置基础属性"""

        level_index = level - 1

        for attr in self.ATTRIBUTES:
            if attr in character and isinstance(character[attr], list):
                attr_list = character[attr]

                if 0 <= level_index < len(attr_list):
                    value = float(attr_list[level_index])

                else:
                    value = 0.0

            else:
                value = 0.0

            self._zones[attr].set_params(**{attr: value})

    def _setup_from_weapon(self, character: dict[str, Any], weapon: dict[str, Any]) -> None:
        """从武器数据添加属性加成（仅平值，百分比由 ability_bonus 链处理）"""

        main_attr = character.get("主能力", "")

        sub_attr = character.get("副能力", "")

        for attr in self.ATTRIBUTES:
            current_value = self._zones[attr]._params.get(attr, 0.0)

            # 从 normal_skills 列表中获取平值加成

            for skill in weapon.get("normal_skills", []):
                if not isinstance(skill, dict):
                    continue

                effect = skill.get("effect", "")

                if (
                    effect == f"{attr}+"
                    or (attr == main_attr and effect == "主能力值+")
                    or (attr == sub_attr and effect == "副能力值+")
                ):
                    current_value += self._get_weapon_bonus(skill.get("curve", []))

            # 从直接属性键中获取加成（向后兼容旧 schema）

            if f"{attr}+" in weapon:
                current_value += self._get_weapon_bonus(weapon[f"{attr}+"])

            if attr == main_attr and "主能力值+" in weapon:
                current_value += self._get_weapon_bonus(weapon["主能力值+"])

            if attr == sub_attr and "副能力值+" in weapon:
                current_value += self._get_weapon_bonus(weapon["副能力值+"])

            self._zones[attr].set_params(**{attr: current_value})

    def _get_weapon_bonus(self, bonus_data, level: int = 1) -> float:
        """

        从武器加成数据中提取加成值（支持等级选择）



        参数：

            bonus_data: 武器加成数据（可以是列表或数值）

            level: 特殊能力等级（1-9），用于从列表中获取对应等级的加成值



        返回：

            加成值（float）



        说明：

            - 如果 bonus_data 是列表，根据 level 参数获取对应等级的值

            - 如果 bonus_data 是单个数值，直接返回该值

            - 如果数据无效，返回 0.0

        """

        if isinstance(bonus_data, list) and len(bonus_data) > 0:
            level_index = level - 1

            if 0 <= level_index < len(bonus_data):
                return float(bonus_data[level_index])

            return float(bonus_data[0])

        elif isinstance(bonus_data, int | float):
            return float(bonus_data)

        return 0.0

    def get_zone(self, attribute: str) -> AttributeMultiplierZone:
        """获取指定属性的乘区"""

        return self._zones[attribute]

    def calculate_all(self) -> dict[str, float]:
        """计算所有属性乘区的值"""

        return {attr: zone.calculate() for attr, zone in self._zones.items()}

    def calculate_total(self) -> float:
        """计算所有属性乘区的总和"""

        return sum(zone.calculate() for zone in self._zones.values())

    def get_main_sub_info(self, character: dict[str, Any] | None) -> dict[str, str]:
        """获取角色的主能力和副能力信息"""

        if character is None:
            return {"主能力": "", "副能力": ""}

        return {"主能力": character.get("主能力", ""), "副能力": character.get("副能力", "")}
