#!/usr/bin/env python3
"""终末地 DataContext 加载器 — 实现框架的 DataContextLoader 接口。"""

from __future__ import annotations

from typing import Any

from calc_framework.data.context import make_context
from calc_framework.data.loader import DataContextLoader


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
        char = kwargs["character"]
        weapon = kwargs.get("weapon")
        char_level = kwargs.get("char_level", 1)
        weapon_level = kwargs.get("weapon_level", 1)
        trust_level = kwargs.get("trust_level", 0)
        bonuses_kwargs: dict[str, Any] = kwargs.get("bonuses_kwargs", {})

        attr, ability, final = _run_existing_engines(
            char, weapon,
            char_level=char_level,
            weapon_level=weapon_level,
            trust_level=trust_level,
            bonuses_kwargs=bonuses_kwargs,
        )

        main_attr = ability["main_attr"]
        sub_attr = ability["sub_attr"]

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
            },
            weapon={
                "基础攻击": final["weapon_base_attack"],
                "攻击力+": final["attack_bonus_multiplier"] - 1.0,
                "附加攻击力+": final["additional_attack"],
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
                "能力值加成": ability["bonus"],
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
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    from calculation.multiplicative_zones.ability_bonus_details import (
        calculate_ability_bonus_with_details,
    )
    from calculation.multiplicative_zones.attribute_zone import (
        calculate_attribute_zones_with_details,
    )
    from calculation.multiplicative_zones.final_attack_zone import (
        calculate_final_attack_with_details,
    )

    attr = calculate_attribute_zones_with_details(
        char, weapon, level=char_level, trust_level=trust_level, **bonuses_kwargs,
    )
    ability = calculate_ability_bonus_with_details(
        char, weapon, level=char_level, trust_level=trust_level, **bonuses_kwargs,
    )
    final = calculate_final_attack_with_details(
        char, weapon,
        char_level=char_level, weapon_level=weapon_level,
        trust_level=trust_level, **bonuses_kwargs,
    )
    return attr, ability, final
