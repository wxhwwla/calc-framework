#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
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

import warnings
from typing import Any

from calc_engine.endfield.calc.damage.formula import trust_add


def _get_weapon_bonus(bonus_data, level: int = 1) -> float:
    """从武器加成数据中提取加成值（支持等级选择）"""
    if isinstance(bonus_data, list):
        level_index = level - 1
        if 0 <= level_index < len(bonus_data) and isinstance(bonus_data[level_index], (int, float)):
            return float(bonus_data[level_index])
    elif isinstance(bonus_data, (int, float)):
        return float(bonus_data)
    return 0.0


def _get_bonus_from_normal_skills(weapon: dict[str, Any], effect_name: str, level: int = 1) -> float:
    """从武器的 normal_skills 列表中获取指定效果的加成值"""
    normal_skills = weapon.get("normal_skills", [])
    for skill in normal_skills:
        if isinstance(skill, dict) and skill.get("effect") == effect_name:
            curve = skill.get("curve", [])
            return _get_weapon_bonus(curve, level)
    return 0.0


def _warn_if_legacy_skill_kwargs_used(
    *,
    sa1_name: str,
    sa2_name: str,
    sa3_name: str,
    ws_name: str,
    ws2_name: str,
    normal_skill_1_name: str,
    normal_skill_2_name: str,
    normal_skill_3_name: str,
    special_skill_1_name: str,
    special_skill_2_name: str,
) -> None:
    """当仅使用旧参数名时发出弃用告警。"""
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
            stacklevel=3,
        )


def calculate_ability_bonus(
    character: dict[str, Any] | None,
    weapon: dict[str, Any] | None = None,
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
    equipment_stat_bonus: dict[str, float] | None = None,
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
        - 信赖加成（累积）：等级0→0，等级1→10，等级2→25，等级3→40，等级4→60
        - 如果角色没有定义主/副能力，或数据不完整，返回 0.0
        - 同名的加成效果会叠加（如两个敏捷+会相加）
    """
    _warn_if_legacy_skill_kwargs_used(
        sa1_name=sa1_name,
        sa2_name=sa2_name,
        sa3_name=sa3_name,
        ws_name=ws_name,
        ws2_name=ws2_name,
        normal_skill_1_name=normal_skill_1_name,
        normal_skill_2_name=normal_skill_2_name,
        normal_skill_3_name=normal_skill_3_name,
        special_skill_1_name=special_skill_1_name,
        special_skill_2_name=special_skill_2_name,
    )

    if character is None:
        return 0.0

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

    main_attr = character.get("主能力", "")
    sub_attr = character.get("副能力", "")

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

    main_pct = 0.0
    sub_pct = 0.0

    if weapon:

        def _resolve_level(effect: str) -> int:
            if effect == sa1_name:
                return sa1_level
            elif effect == sa2_name:
                return sa2_level
            elif effect == sa3_name:
                return sa3_level
            return 1

        def _should_skip(effect: str) -> bool:
            return effect == sa3_name and sa3_level == 0

        def _classify(effect: str) -> str:
            if effect == "主能力值+":
                return "main_flat"
            if effect == "副能力值+":
                return "sub_flat"
            if effect == f"{main_attr}+":
                return "main_flat"
            if effect == f"{sub_attr}+":
                return "sub_flat"
            if effect == "主能力+":
                return "main_pct"
            if effect == "副能力+":
                return "sub_pct"
            if effect == "全能力+":
                return "both_pct"
            return ""

        # 1. 从 normal_skills 列表中获取加成
        for skill in weapon.get("normal_skills", []):
            if not isinstance(skill, dict):
                continue
            effect = skill.get("effect", "")
            category = _classify(effect)
            if not category:
                continue
            if _should_skip(effect):
                continue
            bonus_level = _resolve_level(effect)
            bonus_value = _get_weapon_bonus(skill.get("curve", []), bonus_level)
            if category == "main_flat":
                main_value += bonus_value
            elif category == "sub_flat":
                sub_value += bonus_value
            elif category == "main_pct":
                main_pct += bonus_value
            elif category == "sub_pct":
                sub_pct += bonus_value
            elif category == "both_pct":
                main_pct += bonus_value
                sub_pct += bonus_value

        # 2. 从直接属性键中获取加成（向后兼容）
        bonus_attrs = [key for key in weapon if key.endswith("+")]
        for attr_name in bonus_attrs:
            category = _classify(attr_name)
            if not category:
                continue
            if _should_skip(attr_name):
                continue
            bonus_level = _resolve_level(attr_name)
            bonus_value = _get_weapon_bonus(weapon[attr_name], bonus_level)
            if category == "main_flat":
                main_value += bonus_value
            elif category == "sub_flat":
                sub_value += bonus_value
            elif category == "main_pct":
                main_pct += bonus_value
            elif category == "sub_pct":
                sub_pct += bonus_value
            elif category == "both_pct":
                main_pct += bonus_value
                sub_pct += bonus_value

        from calc_engine.endfield.calc.skills.special_fields import (
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
        main_value += md
        sub_value += sd

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
        main_pct += mp
        sub_pct += sp

    # 添加信赖加成到主能力（使用公式模块中的 trust_add 常量）
    if 0 <= trust_level < len(trust_add):
        main_value += trust_add[trust_level]

    if equipment_stat_bonus:
        if main_attr and main_attr in equipment_stat_bonus:
            main_value += float(equipment_stat_bonus[main_attr])
        if sub_attr and sub_attr in equipment_stat_bonus:
            sub_value += float(equipment_stat_bonus[sub_attr])

    main_final = main_value * (1.0 + main_pct / 100.0)
    sub_final = sub_value * (1.0 + sub_pct / 100.0)

    return main_final * 0.005 + sub_final * 0.002


#!/usr/bin/env python3
"""能力值加成乘区：Zone 类定义。"""

from .base_zone import BaseZone


class AbilityBonusZone(BaseZone):
    """
    能力值加成乘区

    根据角色的主能力和副能力计算额外的攻击力加成。
    """

    def __init__(self):
        super().__init__(name="能力值加成", description="主能力×0.005 + 副能力×0.002")

    def calculate(self) -> float:
        """
        计算能力值加成

        公式：main_value×(1+main_pct/100)×0.005 + sub_value×(1+sub_pct/100)×0.002

        返回：
            能力值加成值（float）
        """
        main_value = self._params.get("main_value", 0.0)
        sub_value = self._params.get("sub_value", 0.0)
        main_pct = self._params.get("main_pct", 0.0)
        sub_pct = self._params.get("sub_pct", 0.0)
        return (
            main_value * (1.0 + main_pct / 100.0) * 0.005
            + sub_value * (1.0 + sub_pct / 100.0) * 0.002
        )
