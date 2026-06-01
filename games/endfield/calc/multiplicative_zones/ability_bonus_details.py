#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""能力值加成：带明细的快捷计算。"""

from typing import Anyfrom games.endfield.calc.damage.formula import trust_addfrom .ability_bonus_calc import _get_weapon_bonus, _warn_if_legacy_skill_kwargs_useddef calculate_ability_bonus_with_details(
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
) -> dict[str, Any]:
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
        return {
            "main_attr": "",
            "main_value": 0.0,
            "main_base": 0.0,
            "main_bonus": 0.0,
            "sub_attr": "",
            "sub_value": 0.0,
            "sub_base": 0.0,
            "sub_bonus": 0.0,
            "bonus": 0.0,
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

    main_attr = character.get("主能力", "")
    sub_attr = character.get("副能力", "")

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

    main_pct = 0.0
    sub_pct = 0.0

    if weapon:

        def _resolve_level(attr_name: str) -> int:
            if attr_name == sa1_name:
                return sa1_level
            elif attr_name == sa2_name:
                return sa2_level
            elif attr_name == sa3_name:
                return sa3_level
            return 1

        def _should_skip(attr_name: str) -> bool:
            return attr_name == sa3_name and sa3_name and sa3_level == 0

        def _classify(attr_name: str) -> str:
            if attr_name == "主能力值+":
                return "main_flat"
            if attr_name == "副能力值+":
                return "sub_flat"
            if attr_name == f"{main_attr}+":
                return "main_flat"
            if attr_name == f"{sub_attr}+":
                return "sub_flat"
            if attr_name == "主能力+":
                return "main_pct"
            if attr_name == "副能力+":
                return "sub_pct"
            if attr_name == "全能力+":
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
                main_bonus += bonus_value
            elif category == "sub_flat":
                sub_bonus += bonus_value
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
                main_bonus += bonus_value
            elif category == "sub_flat":
                sub_bonus += bonus_value
            elif category == "main_pct":
                main_pct += bonus_value
            elif category == "sub_pct":
                sub_pct += bonus_value
            elif category == "both_pct":
                main_pct += bonus_value
                sub_pct += bonus_value

        from games.endfield.calc.skills.special_fields import (            add_special_picks_to_ability_pct,            add_special_picks_to_main_sub_bonus,        )

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
        main_bonus += md
        sub_bonus += sd

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

    trust_bonus = trust_add[trust_level] if 0 <= trust_level < len(trust_add) else 0.0

    main_flat = main_base + main_bonus + trust_bonus
    sub_flat = sub_base + sub_bonus

    main_value = main_flat * (1.0 + main_pct / 100.0)
    sub_value = sub_flat * (1.0 + sub_pct / 100.0)

    bonus = int(main_value) * 0.005 + int(sub_value) * 0.002

    return {
        "main_attr": main_attr,
        "main_value": main_value,
        "main_flat": main_flat,
        "main_pct": main_pct,
        "main_base": main_base,
        "main_bonus": main_bonus,
        "sub_attr": sub_attr,
        "sub_value": sub_value,
        "sub_flat": sub_flat,
        "sub_pct": sub_pct,
        "sub_base": sub_base,
        "sub_bonus": sub_bonus,
        "bonus": bonus,
    }
