#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""终末地 DataContext 加载器 — 实现框架的 DataContextLoader 接口。

迁移自 ``multiplicative_zones.dag.loader``。
"""

from __future__ import annotations

from typing import Any

from calc_framework.data.context import make_context
from calc_framework.data.loader import DataContextLoader


def _get_char_attr_at_level(char: dict[str, Any], key: str, level: int) -> float:
    """从角色 JSON 读取某属性在指定等级的值，返回 float。"""
    values = char.get(key)
    if not isinstance(values, list):
        return 0.0
    idx = min(level - 1, len(values) - 1)
    if idx < 0:
        return 0.0
    return float(values[idx])


def _get_weapon_refinement_bonus(weapon: dict[str, Any] | None, *, refine_level: int) -> dict[str, float]:
    """从武器 JSON 读取精炼等级对应的 normal_skills 加成值。

    返回:
        {"主能力值+": float, "附加攻击力+": float}
    """
    result: dict[str, float] = {
        "主能力值+": 0.0,
        "附加攻击力+": 0.0,
    }
    if not weapon:
        return result
    skills = weapon.get("normal_skills", [])
    if not isinstance(skills, list):
        return result
    idx = min(refine_level - 1, 8)
    if idx < 0:
        idx = 0
    for skill in skills:
        effect = skill.get("effect", "")
        curve = skill.get("curve", [])
        if isinstance(curve, list) and len(curve) > idx:
            if effect == "主能力值+":
                result["主能力值+"] = float(curve[idx])
            elif effect == "附加攻击力+":
                result["附加攻击力+"] = float(curve[idx])
    return result


class EndfieldContextLoader(DataContextLoader):
    """从终末地角色/武器原始数据构建 DataContext。

    委托现有引擎做重型预处理（装备词条解析、武器技能分类），
    然后将中间结果填入标准化的 DataContext。

    用法::

        loader = EndfieldContextLoader()
        ctx = loader.build_context(
            character=char_dict,
            weapon=weapon_dict,
            char_level=80,
            weapon_level=80,
            trust_level=0,
            bonuses_kwargs={...},
        )
    """

    def build_context(self, **kwargs: Any) -> dict[str, Any]:
        """从原始角色/武器数据构建 DAG 求值上下文。

        委托现有的属性乘区/能力值加成/最终攻击力引擎做预处理，
        然后将中间结果填入框架 DataContext。

        Args:
            kwargs: 含 character/weapon/char_level/weapon_level/trust_level/bonuses_kwargs 等。

        Returns:
            DataContext 兼容的嵌套字典，可直接传入 DAGService.evaluate()。
        """
        char = kwargs["character"]
        weapon = kwargs.get("weapon")
        char_level = kwargs.get("char_level", 1)
        weapon_level = kwargs.get("weapon_level", 1)
        trust_level = kwargs.get("trust_level", 0)
        bonuses_kwargs: dict[str, Any] = kwargs.get("bonuses_kwargs", {})
        equipment_stat_bonus = kwargs.get("equipment_stat_bonus")
        equipment_attack_percent = float(kwargs.get("equipment_attack_percent", 0.0))

        attr, ability, final = _run_existing_engines(
            char,
            weapon,
            char_level=char_level,
            weapon_level=weapon_level,
            trust_level=trust_level,
            bonuses_kwargs=bonuses_kwargs,
            equipment_stat_bonus=equipment_stat_bonus,
            equipment_attack_percent=equipment_attack_percent,
        )

        main_attr = ability["main_attr"]
        sub_attr = ability["sub_attr"]

        refine_level = weapon.get("精炼等级", 1) if weapon else 1
        refine_bonus = _get_weapon_refinement_bonus(weapon, refine_level=refine_level)

        return make_context(
            character={
                "基础攻击": final["char_base_attack"],
                "力量": attr["力量"]["base"],
                "敏捷": attr["敏捷"]["base"],
                "智识": attr["智识"]["base"],
                "意志": attr["意志"]["base"],
                "暴击率": char.get("暴击率", char.get("crit_rate", 0.05)),
                "暴击伤害": char.get("暴击伤害", char.get("crit_damage", 0.5)),
                "主能力": main_attr,
                "副能力": sub_attr,
                "基础生命值": _get_char_attr_at_level(char, "基础生命值", char_level),
                "基础防御力": _get_char_attr_at_level(char, "基础防御力", char_level),
            },
            weapon={
                "基础攻击": final["weapon_base_attack"],
                "攻击力+": final["attack_bonus_multiplier"] - 1.0,
                "附加攻击力+": final["additional_attack"],
                "精炼等级": refine_level,
                "法术伤害+": 0.0,
                "攻击力+平值": 0.0,
                "最大生命值+": 0.0,
            },
            equipment={
                "攻击力平值": 0.0,
            },
            enemy={
                "防御": 100,
            },
            computed={
                "主能力平值加算": ability["main_flat"],
                "副能力平值加算": ability["sub_flat"],
                "主能力百分比": ability["main_pct"],
                "副能力百分比": ability["sub_pct"],
                "主能力": main_attr,
                "副能力": sub_attr,
                "力量基础值": attr["力量"]["base"],
                "力量加成值": attr["力量"]["bonus"],
                "力量最终值": attr["力量"]["total"],
                "敏捷基础值": attr["敏捷"]["base"],
                "敏捷加成值": attr["敏捷"]["bonus"],
                "敏捷最终值": attr["敏捷"]["total"],
                "智识基础值": attr["智识"]["base"],
                "智识加成值": attr["智识"]["bonus"],
                "智识最终值": attr["智识"]["total"],
                "意志基础值": attr["意志"]["base"],
                "意志加成值": attr["意志"]["bonus"],
                "意志最终值": attr["意志"]["total"],
                "最终攻击力": final["final_attack"],
                "基础攻击力合计": final["base_attack"],
                "角色基础攻击力": final["char_base_attack"],
                "武器基础攻击力": final["weapon_base_attack"],
                "攻击加成攻击力": final["attack_bonus_attack"],
                "中间攻击力": final["intermediate_attack"],
                "额外攻击力": final["additional_attack"],
                "能力值加成": final["ability_bonus"],
                "技能倍率": 1.0,
                "暴击区": 1.0,
                "伤害加成": 1.0,
                "伤害减免": 1.0,
                "增幅": 1.0,
                "虚弱": 1.0,
                "庇护": 1.0,
                "脆弱": 1.0,
                "易伤": 1.0,
                "防御": 0.5,
                "失衡易伤": 1.0,
                "抗性": 1.0,
                "非主控减伤": 1.0,
                "连击增伤": 1.0,
                "特殊乘区": 1.0,
                "武器精炼主能力值加成": refine_bonus["主能力值+"],
                "武器精炼附加攻击力加成": refine_bonus["附加攻击力+"],
            },
        )


def _run_existing_engines(
    char: dict[str, Any],
    weapon: dict[str, Any] | None,
    *,
    char_level: int,
    weapon_level: int,
    trust_level: int,
    bonuses_kwargs: dict[str, Any],
    equipment_stat_bonus: dict[str, Any] | None = None,
    equipment_attack_percent: float = 0.0,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """运行现有的属性乘区/能力值加成/最终攻击力引擎，返回预处理结果。

    使用旧引擎（非 DAG 引擎）做重型预处理（装备词条解析、武器技能分类等），
    将结果返回给 ``EndfieldContextLoader.build_context`` 填入标准化 DataContext。

    Returns:
        (属性乘区结果dict, 能力值加成结果dict, 最终攻击力结果dict)
    """
    from games.endfield.calc.multiplicative_zones.ability_bonus_details import (
        calculate_ability_bonus_with_details,
    )
    from games.endfield.calc.multiplicative_zones.attribute_zone import (
        calculate_attribute_zones_with_details,
    )
    from games.endfield.calc.multiplicative_zones.final_attack_zone import (
        calculate_final_attack_with_details,
    )

    stat_bonus = dict(equipment_stat_bonus) if equipment_stat_bonus else None

    attr = calculate_attribute_zones_with_details(
        char,
        weapon,
        level=char_level,
        trust_level=trust_level,
        **bonuses_kwargs,
    )
    ability = calculate_ability_bonus_with_details(
        char,
        weapon,
        level=char_level,
        trust_level=trust_level,
        **bonuses_kwargs,
    )
    final = calculate_final_attack_with_details(
        char,
        weapon,
        char_level=char_level,
        weapon_level=weapon_level,
        trust_level=trust_level,
        equipment_stat_bonus=stat_bonus,
        equipment_attack_percent=equipment_attack_percent,
        **bonuses_kwargs,
    )
    return attr, ability, final
