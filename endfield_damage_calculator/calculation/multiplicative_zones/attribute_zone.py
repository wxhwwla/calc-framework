#!/usr/bin/env python3
"""
能力乘区模块

实现力量、敏捷、智识、意志四个属性乘区的计算逻辑。

计算逻辑：
1. 从角色获取四个基础属性值（根据等级）
2. 检查武器是否含有同名属性加成，如有则相加
3. 检查武器是否含有主能力加成/副能力加成，根据角色主/副能力对应加成

参数：
    character: 角色数据字典
    weapon: 武器数据字典
    level: 等级（1-90）
"""

import warnings
from typing import Any

from .base_zone import BaseZone


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
        elif isinstance(bonus_data, (int, float)):
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
        # 计算基础值（角色属性）
        base_value = 0.0
        if character and attr in character and isinstance(character[attr], list):
            attr_list = character[attr]
            if 0 <= level_index < len(attr_list):
                base_value = float(attr_list[level_index])

        # 计算武器加成（仅平值，百分比由 ability_bonus 链处理）
        bonus_value = 0.0
        if weapon:

            def _resolve_level(effect: str) -> int:
                if effect == sa1_name:
                    return sa1_level
                if effect == sa2_name:
                    return sa2_level
                if effect == sa3_name:
                    return sa3_level
                return 1

            def _should_skip(effect: str) -> bool:
                return effect == sa3_name and sa3_level == 0

            # 1. 从 normal_skills 列表中获取平值加成
            for skill in weapon.get("normal_skills", []):
                if not isinstance(skill, dict):
                    continue
                effect = skill.get("effect", "")
                if (
                    effect == f"{attr}+"
                    or (attr == main_attr and effect == "主能力值+")
                    or (attr == sub_attr and effect == "副能力值+")
                ):
                    if _should_skip(effect):
                        continue
                    bonus_value += manager._get_weapon_bonus(skill.get("curve", []), _resolve_level(effect))

            # 2. 从直接属性键中获取加成（向后兼容旧 schema）
            attr_bonus_name = f"{attr}+"
            if attr_bonus_name in weapon:
                bonus_level = _resolve_level(attr_bonus_name)
                if not _should_skip(attr_bonus_name):
                    bonus_value += manager._get_weapon_bonus(weapon[attr_bonus_name], bonus_level)

            if attr == main_attr and "主能力值+" in weapon:
                bonus_level = _resolve_level("主能力值+")
                if not _should_skip("主能力值+"):
                    bonus_value += manager._get_weapon_bonus(weapon["主能力值+"], bonus_level)

            if attr == sub_attr and "副能力值+" in weapon:
                bonus_level = _resolve_level("副能力值+")
                if not _should_skip("副能力值+"):
                    bonus_value += manager._get_weapon_bonus(weapon["副能力值+"], bonus_level)

            from character_weapon_equipment.weapon_data.special_fields import (
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
            if attr == main_attr:
                bonus_value += md
            elif attr == sub_attr:
                bonus_value += sd

            # 如果是主能力，加上信赖加成（累积值）
            if attr == main_attr and trust_level > 0:
                trust_add = [0, 10, 25, 40, 60]
                if 0 <= trust_level < len(trust_add):
                    bonus_value += trust_add[trust_level]

        result[attr] = {"base": base_value, "bonus": bonus_value, "total": base_value + bonus_value}

    return result
