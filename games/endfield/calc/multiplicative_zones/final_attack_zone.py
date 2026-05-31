#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""
最终攻击力乘区模块

计算角色的最终攻击力。

计算公式：
    最终攻击力 = 中间攻击力 × (能力值加成 + 1)
    中间攻击力 = 基础攻击力 + 附加攻击力+

说明：
    - 基础攻击力：角色基础攻击力 + 武器基础攻击力（根据等级）
    - 附加攻击力+：武器提供的额外攻击力加成（根据武器等级）
    - 中间攻击力：基础攻击力 + 附加攻击力+
    - 能力值加成：来自 AbilityBonusZone 的计算结果（包含武器加成）
"""

import warnings
from typing import Any

from .ability_bonus_calc import calculate_ability_bonus
from .base_zone import BaseZone


class FinalAttackZone(BaseZone):
    """
    最终攻击力乘区

    根据基础攻击力和能力值加成计算最终攻击力。
    """

    def __init__(self):
        super().__init__(name="最终攻击力", description="基础攻击力 × (能力值加成 + 1)")

    def calculate(self) -> float:
        """
        计算最终攻击力

        返回：
            最终攻击力值（float）
        """
        base_attack = self._params.get("base_attack", 0.0)
        ability_bonus = self._params.get("ability_bonus", 0.0)
        return base_attack * (ability_bonus + 1.0)


def calculate_final_attack(base_attack: float, ability_bonus: float) -> float:
    """
    快捷函数：计算最终攻击力

    参数：
        base_attack: 基础攻击力
        ability_bonus: 能力值加成

    返回：
        最终攻击力值（float）

    计算公式：
        基础攻击力 × (能力值加成 + 1)
    """
    return base_attack * (ability_bonus + 1.0)


def calculate_final_attack_with_details(
    character: dict[str, Any] | None,
    weapon: dict[str, Any] | None = None,
    char_level: int = 1,
    weapon_level: int = 1,
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
    equipment_stat_bonus: dict[str, float] | None = None,
    equipment_attack_percent: float = 0.0,
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
) -> dict[str, float]:
    """
    快捷函数：计算最终攻击力，返回详细信息

    参数：
        character: 角色数据字典
        weapon: 武器数据字典（可选）
        char_level: 角色等级（1-90）
        weapon_level: 武器等级（1-90）
        sa1_name: 第一个特殊能力名称（如敏捷+）
        sa1_level: 第一个特殊能力等级（1-9）
        sa2_name: 第二个特殊能力名称（如物理伤害+）
        sa2_level: 第二个特殊能力等级（1-9）
        sa3_name: 第三条附加属性名称
        sa3_level: 第三条附加属性等级
        ws_name: 武器「特殊能力」字段名称
        ws_level: 武器「特殊能力」等级（0 表示关闭）
        trust_level: 信赖等级（0-4），信赖加成会加到主能力上

    返回：
        包含详细信息的字典：
        {
            'base_attack': 基础攻击力（角色+武器）,
            'char_base_attack': 角色基础攻击力,
            'weapon_base_attack': 武器基础攻击力,
            'attack_bonus_multiplier': 攻击力+乘区（1+攻击力+/100）,
            'attack_bonus_attack': 攻击加成攻击力（基础攻击力×攻击力+乘区）,
            'additional_attack': 附加攻击力+,
            'intermediate_attack': 中间攻击力（攻击加成攻击力+附加攻击力+）,
            'ability_bonus': 能力值加成（含武器加成和信赖加成）,
            'final_attack': 最终攻击力（最终结果）
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

    if character is None:
        return {
            "base_attack": 0.0,
            "char_base_attack": 0.0,
            "weapon_base_attack": 0.0,
            "attack_bonus_multiplier": 1.0,
            "attack_bonus_attack": 0.0,
            "additional_attack": 0.0,
            "intermediate_attack": 0.0,
            "ability_bonus": 0.0,
            "final_attack": 0.0,
        }

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

    # 获取角色基础攻击力（使用角色等级）
    char_level_index = char_level - 1
    char_base_attack = 0.0
    if "基础攻击力" in character and isinstance(character["基础攻击力"], list):
        attack_list = character["基础攻击力"]
        if 0 <= char_level_index < len(attack_list):
            char_base_attack = float(attack_list[char_level_index])

    # 获取武器基础攻击力（使用武器等级）
    weapon_base_attack = 0.0
    if weapon and "基础攻击力" in weapon and isinstance(weapon["基础攻击力"], list):
        weapon_level_index = weapon_level - 1
        attack_list = weapon["基础攻击力"]
        if 0 <= weapon_level_index < len(attack_list):
            weapon_base_attack = float(attack_list[weapon_level_index])

    # 总基础攻击力 = 角色基础攻击力 + 武器基础攻击力
    base_attack = char_base_attack + weapon_base_attack

    # 获取武器攻击力+（使用特殊能力等级，同名效果叠加）
    attack_bonus_percent = 0.0
    if weapon:
        # 1. 先从 normal_skills 列表中获取攻击力+
        for skill in weapon.get("normal_skills", []):
            if not isinstance(skill, dict):
                continue
            effect = skill.get("effect", "")
            if effect == "攻击力+":
                # 如果第三个特殊能力关闭，跳过
                if effect == sa3_name and sa3_level == 0:
                    continue
                # 根据属性名称确定使用哪个特殊能力等级
                if effect == sa1_name:
                    level = sa1_level
                elif effect == sa2_name:
                    level = sa2_level
                elif effect == sa3_name:
                    level = sa3_level
                else:
                    level = 1

                bonus_data = skill.get("curve", [])
                if isinstance(bonus_data, list):
                    level_index = level - 1
                    if 0 <= level_index < len(bonus_data):
                        attack_bonus_percent += float(bonus_data[level_index])
                elif isinstance(bonus_data, (int, float)):
                    attack_bonus_percent += float(bonus_data)

        # 2. 再遍历所有以+结尾的属性，累加攻击力+（排除附加攻击力+）
        for attr_name in weapon:
            if attr_name.endswith("+") and attr_name == "攻击力+":
                # 如果第三个特殊能力关闭，跳过
                if attr_name == sa3_name and sa3_level == 0:
                    continue
                # 根据属性名称确定使用哪个特殊能力等级
                if attr_name == sa1_name:
                    level = sa1_level
                elif attr_name == sa2_name:
                    level = sa2_level
                elif attr_name == sa3_name:
                    level = sa3_level
                else:
                    # 属性不属于任何特殊能力时，使用默认等级1
                    level = 1

                # 获取该等级的加成值（直接属性总是应用，使用对应滑块等级或默认等级1）
                bonus_data = weapon[attr_name]
                if isinstance(bonus_data, list):
                    level_index = level - 1
                    if 0 <= level_index < len(bonus_data):
                        attack_bonus_percent += float(bonus_data[level_index])
                elif isinstance(bonus_data, (int, float)):
                    attack_bonus_percent += float(bonus_data)

        from games.endfield.calc.skills.special_fields import (
            add_special_picks_attack_percent,
        )

        attack_bonus_percent += add_special_picks_attack_percent(
            weapon,
            ws_name=ws_name,
            ws_level=ws_level,
            ws_stack=ws_stack,
            ws2_name=ws2_name,
            ws2_level=ws2_level,
            ws2_stack=ws2_stack,
            target_name="攻击力+",
        )

    attack_bonus_percent += float(equipment_attack_percent) * 100.0

    # 攻击力+乘区 = 1 + 攻击力+/100
    attack_bonus_multiplier = 1.0 + attack_bonus_percent / 100.0

    # 攻击加成攻击力 = 基础攻击力 × 攻击力+乘区
    attack_bonus_attack = base_attack * attack_bonus_multiplier

    # 获取武器附加攻击力+（使用特殊能力等级）
    additional_attack = 0.0

    if weapon:
        # 1. 先从 normal_skills 列表中获取附加攻击力+
        for skill in weapon.get("normal_skills", []):
            if not isinstance(skill, dict):
                continue
            effect = skill.get("effect", "")
            if effect == "附加攻击力+":
                # 确定使用哪个特殊能力等级
                if effect == sa1_name:
                    level = sa1_level
                elif effect == sa2_name:
                    level = sa2_level
                elif effect == sa3_name:
                    level = sa3_level
                else:
                    level = 1

                # 如果第三个特殊能力关闭，跳过
                if effect == sa3_name and sa3_level == 0:
                    continue

                bonus_data = skill.get("curve", [])
                if isinstance(bonus_data, list):
                    level_index = level - 1
                    if 0 <= level_index < len(bonus_data):
                        additional_attack += float(bonus_data[level_index])
                elif isinstance(bonus_data, (int, float)):
                    additional_attack += float(bonus_data)

        # 2. 再从直接属性键中获取附加攻击力+（向后兼容）
        if "附加攻击力+" in weapon:
            # 确定使用哪个特殊能力等级
            if sa1_name == "附加攻击力+":
                level = sa1_level
            elif sa2_name == "附加攻击力+":
                level = sa2_level
            elif sa3_name == "附加攻击力+":
                level = sa3_level
            else:
                level = 1

            # 如果第三个特殊能力关闭，跳过
            if not (sa3_name == "附加攻击力+" and sa3_level == 0):
                bonus_data = weapon["附加攻击力+"]
                if isinstance(bonus_data, list):
                    level_index = level - 1
                    if 0 <= level_index < len(bonus_data):
                        additional_attack += float(bonus_data[level_index])
                elif isinstance(bonus_data, (int, float)):
                    additional_attack += float(bonus_data)

    # 中间攻击力 = 攻击加成攻击力 + 附加攻击力+ + 装备平铺攻击力
    equipment_flat_attack = 0.0
    if equipment_stat_bonus and "攻击力" in equipment_stat_bonus:
        equipment_flat_attack = float(equipment_stat_bonus["攻击力"])
    intermediate_attack = attack_bonus_attack + additional_attack + equipment_flat_attack

    # 计算能力值加成（包含武器加成和信赖加成，使用特殊能力等级）
    stat_bonus = dict(equipment_stat_bonus) if equipment_stat_bonus else None
    if stat_bonus and "攻击力" in stat_bonus:
        stat_bonus = {k: v for k, v in stat_bonus.items() if k != "攻击力"}

    ability_bonus = calculate_ability_bonus(
        character,
        weapon,
        char_level,
        sa1_name=sa1_name,
        sa1_level=sa1_level,
        sa2_name=sa2_name,
        sa2_level=sa2_level,
        sa3_name=sa3_name,
        sa3_level=sa3_level,
        ws_name=ws_name,
        ws_level=ws_level,
        ws_stack=ws_stack,
        ws2_name=ws2_name,
        ws2_level=ws2_level,
        ws2_stack=ws2_stack,
        equipment_stat_bonus=stat_bonus,
        trust_level=trust_level,
        normal_skill_1_name=normal_skill_1_name,
        normal_skill_1_level=normal_skill_1_level,
        normal_skill_2_name=normal_skill_2_name,
        normal_skill_2_level=normal_skill_2_level,
        normal_skill_3_name=normal_skill_3_name,
        normal_skill_3_level=normal_skill_3_level,
        special_skill_1_name=special_skill_1_name,
        special_skill_1_level=special_skill_1_level,
        special_skill_1_stack=special_skill_1_stack,
        special_skill_2_name=special_skill_2_name,
        special_skill_2_level=special_skill_2_level,
        special_skill_2_stack=special_skill_2_stack,
    )

    # 计算最终攻击力：中间攻击力 × (能力值加成 + 1)
    final_attack = intermediate_attack * (ability_bonus + 1.0)

    return {
        "base_attack": base_attack,
        "char_base_attack": char_base_attack,
        "weapon_base_attack": weapon_base_attack,
        "attack_bonus_multiplier": attack_bonus_multiplier,
        "attack_bonus_attack": attack_bonus_attack,
        "additional_attack": additional_attack,
        "intermediate_attack": intermediate_attack,
        "ability_bonus": ability_bonus,
        "final_attack": final_attack,
    }
