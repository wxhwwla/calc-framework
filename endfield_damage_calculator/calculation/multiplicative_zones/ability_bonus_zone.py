#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
能力值加成乘区模块

计算角色主能力和副能力带来的攻击力加成。

计算公式：
    能力值加成 = (主能力值 + 武器主能力加成) × 0.005 + (副能力值 + 武器副能力加成) × 0.002

说明：
    - 主能力：角色属性中定义的主要属性（如力量、敏捷等）
    - 副能力：角色属性中定义的次要属性
    - 能力值：根据角色等级从对应的属性列表中获取，加上武器加成
"""

from typing import Dict, Any, Optional, Union
from .base_zone import BaseZone
from calculation.formula import trust_add


class AbilityBonusZone(BaseZone):
    """
    能力值加成乘区

    根据角色的主能力和副能力计算额外的攻击力加成。
    """

    def __init__(self):
        super().__init__(
            name="能力值加成",
            description="主能力×0.005 + 副能力×0.002"
        )

    def calculate(self) -> float:
        """
        计算能力值加成

        返回：
            能力值加成值（float）
        """
        main_value = self._params.get('main_value', 0.0)
        sub_value = self._params.get('sub_value', 0.0)
        return main_value * 0.005 + sub_value * 0.002


def _get_weapon_bonus(bonus_data, level: int = 1) -> float:
    """从武器加成数据中提取加成值（支持等级选择）"""
    if isinstance(bonus_data, list):
        level_index = level - 1
        if 0 <= level_index < len(bonus_data) and isinstance(bonus_data[level_index], (int, float)):
            return float(bonus_data[level_index])
    elif isinstance(bonus_data, (int, float)):
        return float(bonus_data)
    return 0.0


def calculate_ability_bonus(
    character: Optional[Dict[str, Any]],
    weapon: Optional[Dict[str, Any]] = None,
    level: int = 1,
    sa1_name: str = "",
    sa1_level: int = 1,
    sa2_name: str = "",
    sa2_level: int = 1,
    sa3_name: str = "",
    sa3_level: int = 0,
    ws_name: str = "",
    ws_level: int = 0,
    ws2_name: str = "",
    ws2_level: int = 0,
    trust_level: int = 0
) -> float:
    """
    快捷函数：计算能力值加成

    参数：
        character: 角色数据字典
        weapon: 武器数据字典（可选）
        level: 角色等级（1-90）
        sa1_name: 第一个特殊能力名称（如敏捷+）
        sa1_level: 第一个特殊能力等级（1-9）
        sa2_name: 第二个特殊能力名称（如物理伤害+）
        sa2_level: 第二个特殊能力等级（1-9）
        sa3_name: 第三条附加属性名称
        sa3_level: 第三条附加属性等级（无第三条时为 0）
        ws_name: 武器「特殊能力」字段名称
        ws_level: 武器「特殊能力」等级（0 表示关闭）
        trust_level: 信赖等级（0-4），信赖加成会加到主能力上

    返回：
        能力值加成值（float）

    计算公式：
        (主能力值 + 武器主能力加成 + 信赖加成) × 0.005 + (副能力值 + 武器副能力加成) × 0.002

    注意：
        - 主能力值和副能力值是根据角色数据中定义的"主能力"和"副能力"属性名称
          从对应的属性列表中获取的数值，再加上武器带来的加成
        - 信赖加成：等级0→0，等级1→10，等级2→15，等级3→15，等级4→20
        - 如果角色没有定义主/副能力，或数据不完整，返回 0.0
        - 同名的加成效果会叠加（如两个敏捷+会相加）
    """
    if character is None:
        return 0.0

    main_attr = character.get('主能力', '')
    sub_attr = character.get('副能力', '')

    level_index = level - 1
    main_value = 0.0
    sub_value = 0.0

    if main_attr and main_attr in character and isinstance(character[main_attr], list):
        attr_list = character[main_attr]
        if 0 <= level_index < len(attr_list):
            main_value = float(attr_list[level_index])

    if sub_attr and sub_attr in character and isinstance(character[sub_attr], list):
        attr_list = character[sub_attr]
        if 0 <= level_index < len(attr_list):
            sub_value = float(attr_list[level_index])

    if weapon:
        # 使用特殊能力等级获取加成值
        bonus_attrs = [key for key in weapon.keys() if key.endswith('+')]
        for attr_name in bonus_attrs:
            # 确定使用哪个特殊能力等级
            if attr_name == sa1_name:
                bonus_level = sa1_level
            elif attr_name == sa2_name:
                bonus_level = sa2_level
            elif attr_name == sa3_name:
                bonus_level = sa3_level
            else:
                # 默认使用武器等级（或第一个等级）
                bonus_level = 1
            
            # 如果第三个特殊能力关闭，跳过
            if attr_name == sa3_name and sa3_level == 0:
                continue
            
            # 添加到对应能力值
            bonus_value = _get_weapon_bonus(weapon[attr_name], bonus_level)
            if attr_name == f"{main_attr}+" or attr_name == "主能力+":
                main_value += bonus_value
            elif attr_name == f"{sub_attr}+" or attr_name == "副能力+":
                sub_value += bonus_value

        from character_weapon_equipment.weapon_data.special_fields import (
            add_special_picks_to_main_sub_bonus,
        )

        md, sd = add_special_picks_to_main_sub_bonus(
            weapon,
            ws_name=ws_name,
            ws_level=ws_level,
            ws2_name=ws2_name,
            ws2_level=ws2_level,
            main_attr=main_attr,
            sub_attr=sub_attr,
        )
        main_value += md
        sub_value += sd

    # 添加信赖加成到主能力（使用公式模块中的 trust_add 常量）
    if 0 <= trust_level < len(trust_add):
        main_value += trust_add[trust_level]

    return main_value * 0.005 + sub_value * 0.002


def calculate_ability_bonus_with_details(
    character: Optional[Dict[str, Any]],
    weapon: Optional[Dict[str, Any]] = None,
    level: int = 1,
    sa1_name: str = "",
    sa1_level: int = 1,
    sa2_name: str = "",
    sa2_level: int = 1,
    sa3_name: str = "",
    sa3_level: int = 0,
    ws_name: str = "",
    ws_level: int = 0,
    ws2_name: str = "",
    ws2_level: int = 0,
    trust_level: int = 0
) -> Dict[str, Any]:
    """
    快捷函数：计算能力值加成，返回详细信息

    参数：
        character: 角色数据字典
        weapon: 武器数据字典（可选）
        level: 角色等级（1-90）
        sa1_name: 第一个特殊能力名称（如敏捷+）
        sa1_level: 第一个特殊能力等级（1-9）
        sa2_name: 第二个特殊能力名称（如物理伤害+）
        sa2_level: 第二个特殊能力等级（1-9）
        sa3_name: 第三条附加属性名称
        sa3_level: 第三条附加属性等级（无第三条时为 0）
        ws_name: 武器「特殊能力」字段名称
        ws_level: 武器「特殊能力」等级（0 表示关闭）
        trust_level: 信赖等级（0-4），信赖加成会加到主能力上

    返回：
        包含详细信息的字典：
        {
            'main_attr': 主能力属性名称,
            'main_value': 主能力值（含武器加成和信赖加成）,
            'main_base': 主能力基础值（不含任何加成）,
            'main_bonus': 主能力武器加成,
            'sub_attr': 副能力属性名称,
            'sub_value': 副能力值（含武器加成）,
            'sub_base': 副能力基础值（不含武器加成）,
            'sub_bonus': 副能力武器加成,
            'bonus': 能力值加成（最终结果）
        }
    """
    if character is None:
        return {
            'main_attr': '',
            'main_value': 0.0,
            'main_base': 0.0,
            'main_bonus': 0.0,
            'sub_attr': '',
            'sub_value': 0.0,
            'sub_base': 0.0,
            'sub_bonus': 0.0,
            'bonus': 0.0
        }

    main_attr = character.get('主能力', '')
    sub_attr = character.get('副能力', '')

    level_index = level - 1
    main_base = 0.0
    sub_base = 0.0
    main_bonus = 0.0
    sub_bonus = 0.0

    if main_attr and main_attr in character and isinstance(character[main_attr], list):
        attr_list = character[main_attr]
        if 0 <= level_index < len(attr_list):
            main_base = float(attr_list[level_index])

    if sub_attr and sub_attr in character and isinstance(character[sub_attr], list):
        attr_list = character[sub_attr]
        if 0 <= level_index < len(attr_list):
            sub_base = float(attr_list[level_index])

    if weapon:
        # 1. 使用特殊能力等级获取直接属性的加成值
        bonus_attrs = [key for key in weapon.keys() if key.endswith('+')]
        for attr_name in bonus_attrs:
            # 确定使用哪个特殊能力等级
            if attr_name == sa1_name:
                bonus_level = sa1_level
            elif attr_name == sa2_name:
                bonus_level = sa2_level
            elif attr_name == sa3_name:
                bonus_level = sa3_level
            else:
                bonus_level = 1

            if attr_name == sa3_name and sa3_name and sa3_level == 0:
                continue

            bonus_value = _get_weapon_bonus(weapon[attr_name], bonus_level)
            if attr_name == f"{main_attr}+" or attr_name == "主能力+":
                main_bonus += bonus_value
            elif attr_name == f"{sub_attr}+" or attr_name == "副能力+":
                sub_bonus += bonus_value
        
        from character_weapon_equipment.weapon_data.special_fields import (
            add_special_picks_to_main_sub_bonus,
        )

        md, sd = add_special_picks_to_main_sub_bonus(
            weapon,
            ws_name=ws_name,
            ws_level=ws_level,
            ws2_name=ws2_name,
            ws2_level=ws2_level,
            main_attr=main_attr,
            sub_attr=sub_attr,
        )
        main_bonus += md
        sub_bonus += sd

    # 计算主能力值（包含武器加成和信赖加成，使用公式模块中的 trust_add 常量）
    trust_bonus = trust_add[trust_level] if 0 <= trust_level < len(trust_add) else 0.0
    
    main_value = main_base + main_bonus + trust_bonus
    sub_value = sub_base + sub_bonus

    bonus = main_value * 0.005 + sub_value * 0.002

    return {
        'main_attr': main_attr,
        'main_value': main_value,
        'main_base': main_base,
        'main_bonus': main_bonus,
        'sub_attr': sub_attr,
        'sub_value': sub_value,
        'sub_base': sub_base,
        'sub_bonus': sub_bonus,
        'bonus': bonus
    }