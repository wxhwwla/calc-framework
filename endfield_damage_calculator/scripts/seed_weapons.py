#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量录入示例武器（与 add_weapon 库分离，避免 import 时执行）。"""

from character_weapon_equipment.weapon_data.add_weapon import add_weapon

# 4 星武器示例配置（可按需增删）
_SEED_WEAPONS = [
    {
        "name": "荧光雷羽",
        "weapon_type": "施术单元",
        "star": 4,
        "base_atk": {"base": 34, "growth": 62, "divisor": 18, "offset": 16},
        "bonus_attrs": {
            "意志+": {"base": 12, "growth": 48, "divisor": 5, "offset": 0, "special": [93]},
            "攻击力+": {"base": 3, "growth": 12, "divisor": 5, "offset": 0, "special": [23.4]},
        },
        "special_ability": {
            "enabled": True,
            "name": "攻击力+",
            "base": 12,
            "growth": 4.8,
            "divisor": 2,
            "offset": 0,
            "special": [33.6],
        },
    },
    {
        "name": "全自动骇新星",
        "weapon_type": "施术单元",
        "star": 4,
        "base_atk": {"base": 34, "growth": 62, "divisor": 18, "offset": 16},
        "bonus_attrs": {
            "智识+": {"base": 12, "growth": 96, "divisor": 10, "offset": 0, "special": [93]},
            "法术伤害+": {"base": 3.3, "growth": 16, "divisor": 6, "offset": 0.4, "special": [26.0]},
        },
        "special_ability": {
            "enabled": True,
            "name": "攻击力+",
            "base": 15,
            "growth": 6,
            "divisor": 2,
            "offset": 0,
            "special": [42.0],
        },
    },
    {
        "name": "淬火者",
        "weapon_type": "双手剑",
        "star": 4,
        "base_atk": {"base": 34, "growth": 62, "divisor": 18, "offset": 16},
        "bonus_attrs": {
            "意志+": {"base": 12, "growth": 96, "divisor": 10, "offset": 0, "special": [93]},
            "最大生命值+": {"base": 6, "growth": 9.6, "divisor": 2, "offset": 0, "special": [46.8]},
        },
        "special_ability": {
            "enabled": True,
            "name": "攻击力+",
            "base": 12,
            "growth": 4.8,
            "divisor": 2,
            "offset": 0,
            "special": [33.6],
        },
    },
    {
        "name": "工业零点一",
        "weapon_type": "双手剑",
        "star": 4,
        "base_atk": {"base": 34, "growth": 62, "divisor": 18, "offset": 16},
        "bonus_attrs": {
            "力量+": {"base": 12, "growth": 96, "divisor": 10, "offset": 0, "special": [93]},
            "最大生命值+": {"base": 3, "growth": 4.8, "divisor": 2, "offset": 0, "special": [23.4]},
        },
        "special_ability": {
            "enabled": True,
            "name": "攻击力+",
            "base": 12,
            "growth": 4.8,
            "divisor": 2,
            "offset": 0,
            "special": [33.6],
        },
    },
    {
        "name": "寻路者道标",
        "weapon_type": "长柄武器",
        "star": 4,
        "base_atk": {"base": 34, "growth": 62, "divisor": 18, "offset": 16},
        "bonus_attrs": {
            "敏捷+": {"base": 12, "growth": 96, "divisor": 10, "offset": 0, "special": [93]},
            "攻击力+": {"base": 3, "growth": 4.8, "divisor": 2, "offset": 0, "special": [23.4]},
        },
        "special_ability": {
            "enabled": True,
            "name": "攻击力+",
            "base": 15,
            "growth": 6,
            "divisor": 2,
            "offset": 0,
            "special": [42.0],
        },
    },
    {
        "name": "天使杀手",
        "weapon_type": "长柄武器",
        "star": 4,
        "base_atk": {"base": 34, "growth": 62, "divisor": 18, "offset": 16},
        "bonus_attrs": {
            "敏捷+": {"base": 12, "growth": 96, "divisor": 10, "offset": 0, "special": [93]},
            "攻击力+": {"base": 3.3, "growth": 16, "divisor": 6, "offset": 0.4, "special": [26]},
        },
        "special_ability": {
            "enabled": True,
            "name": "攻击力+",
            "base": 12,
            "growth": 4.8,
            "divisor": 2,
            "offset": 0,
            "special": [33.6],
        },
    },
    {
        "name": "长路",
        "weapon_type": "手铳",
        "star": 4,
        "base_atk": {"base": 34, "growth": 62, "divisor": 18, "offset": 16},
        "bonus_attrs": {
            "力量+": {"base": 12, "growth": 96, "divisor": 10, "offset": 0, "special": [93]},
            "法术伤害+": {"base": 3.3, "growth": 16, "divisor": 6, "offset": 0.4, "special": [26]},
        },
        "special_ability": {
            "enabled": True,
            "name": "攻击力+",
            "base": 12,
            "growth": 4.8,
            "divisor": 2,
            "offset": 0,
            "special": [33.6],
        },
    },
    {
        "name": "呼啸守卫",
        "weapon_type": "手铳",
        "star": 4,
        "base_atk": {"base": 34, "growth": 62, "divisor": 18, "offset": 16},
        "bonus_attrs": {
            "智识+": {"base": 12, "growth": 96, "divisor": 10, "offset": 0, "special": [93]},
            "攻击力+": {"base": 3, "growth": 4.8, "divisor": 2, "offset": 0, "special": [23.4]},
        },
        "special_ability": {
            "enabled": True,
            "name": "攻击力+",
            "base": 12,
            "growth": 4.8,
            "divisor": 2,
            "offset": 0,
            "special": [33.6],
        },
    },







]


def main() -> None:
    for spec in _SEED_WEAPONS:
        add_weapon(**spec)


if __name__ == "__main__":
    main()
