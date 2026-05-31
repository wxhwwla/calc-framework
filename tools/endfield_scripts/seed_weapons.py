#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""批量录入示例武器（与 add_weapon 库分离，避免 import 时执行）。"""

from tools.endfield_scripts.add_weapon import add_weapon

# 4 星武器示例配置（可按需增删）
_SEED_WEAPONS = [
    {
        "name": "J.E.T.",
        "weapon_type": "长柄武器",
        "star": 6,
        "base_atk": {"base": 51, "growth": 111, "divisor": 22, "offset": 10},
        "bonus_attrs": {
            "主能力值+": {"base": 17.0, "growth": 68, "divisor": 5, "offset": 0, "special": [132.0]},
            "攻击力+": {"base": 5.0, "growth": 4, "divisor": 1, "offset": 0, "special": [39.0]},
            "法术伤害+": {"base": 12.0, "growth": 2.4, "divisor": 1, "offset": 0.0, "special": [33.6]},
        },
        "special_1": {
            "enabled": True,
            "name": "施放战技后，法术伤害+",
            "base": 12.0,
            "growth": 2.4,
            "divisor": 1,
            "offset": 0.0,
            "special": [33.6],
        },
        "special_2": {
            "enabled": True,
            "name": "施放连携技后，法术伤害+",
            "base": 12.0,
            "growth": 2.4,
            "divisor": 1,
            "offset": 0.0,
            "special": [33.6],
        },
    },
    {
        "name": "O.B.J.尖峰",
        "weapon_type": "长柄武器",
        "star": 5,
        "base_atk": {"base": 42, "growth": 199, "divisor": 48, "offset": 24},
        "bonus_attrs": {
            "意志+": {"base": 16.0, "growth": 64, "divisor": 5, "offset": 0, "special": [124.0]},
            "物理伤害+": {"base": 4.4, "growth": 24.9, "divisor": 7, "offset": 0.6, "special": [34.7]},
        },
        "special_1": {
            "enabled": True,
            "name": "造成的伤害增加+",
            "base": 8.0,
            "growth": 1.6,
            "divisor": 1,
            "offset": 0.0,
            "special": [22.4],
        },
        "special_2": {
            "enabled": True,
            "name": "攻击力+",
            "curve": [12.0, 14.4, 16.9, 19.2, 21.6, 24.0, 26.4, 28.8, 33.6],
        },
    },
    {
        "name": "O.B.J.术识",
        "weapon_type": "施术单元",
        "star": 5,
        "base_atk": {"base": 42, "growth": 199, "divisor": 48, "offset": 24},
        "bonus_attrs": {
            "智识+": {"base": 16.0, "growth": 64, "divisor": 5, "offset": 0, "special": [124.0]},
            "源石技艺强度+": {"base": 8.0, "growth": 32, "divisor": 5, "offset": 0, "special": [62.0]},
            "最大生命值+": {"base": 10.0, "growth": 2, "divisor": 1, "offset": 0, "special": [28.0]},
        },
        "special_ability": {
            "enabled": True,
            "name": "全队灼热和电磁伤害+",
            "base": 8.0,
            "growth": 1.6,
            "divisor": 1,
            "offset": 0.0,
            "special": [22.4],
        },
    },
    {
        "name": "O.B.J.轻芒",
        "weapon_type": "单手剑",
        "star": 5,
        "base_atk": {"base": 42, "growth": 199, "divisor": 48, "offset": 24},
        "bonus_attrs": {
            "敏捷+": {"base": 16.0, "growth": 64, "divisor": 5, "offset": 0, "special": [124.0]},
            "攻击力+": {"base": 4.0, "growth": 3.2, "divisor": 1, "offset": 0.0, "special": [31.2]},
            "副能力+": {"base": 5.0, "growth": 9, "divisor": 8, "offset": 0, "special": []},
        },
        "special_ability": {
            "enabled": True,
            "name": "灼热和电磁伤害+",
            "base": 3.0,
            "growth": 0.6,
            "divisor": 1,
            "offset": 0.0,
            "special": [8.4],
            "max_stack": 3,
        },
    },
    {
        "name": "O.B.J.迅极",
        "weapon_type": "手铳",
        "star": 5,
        "base_atk": {"base": 42, "growth": 199, "divisor": 48, "offset": 24},
        "bonus_attrs": {
            "敏捷+": {"base": 16.0, "growth": 64, "divisor": 5, "offset": 0, "special": [124.0]},
            "终结技充能效率+": {"base": 4.8, "growth": 3.8, "divisor": 1, "offset": 0.0, "special": [37.1]},
            "攻击力+": {"base": 5.0, "growth": 9, "divisor": 8, "offset": 0, "special": []},
        },
        "special_ability": {
            "enabled": True,
            "name": "自然伤害+",
            "base": 5.0,
            "growth": 9,
            "divisor": 8,
            "offset": 0,
            "special": [],
        },
    },
    {
        "name": "O.B.J.重荷",
        "weapon_type": "双手剑",
        "star": 5,
        "base_atk": {"base": 42, "growth": 199, "divisor": 48, "offset": 24},
        "bonus_attrs": {
            "力量+": {"base": 16.0, "growth": 64, "divisor": 5, "offset": 0, "special": [124.0]},
            "最大生命值+": {"base": 8.0, "growth": 6.4, "divisor": 1, "offset": 0.0, "special": [62.4]},
            "副能力+": {"base": 5.0, "growth": 9, "divisor": 8, "offset": 0, "special": []},
        },
        "special_ability": {
            "enabled": True,
            "name": "防御力+",
            "base": 18.0,
            "growth": 3.6,
            "divisor": 1,
            "offset": 0.0,
            "special": [50.4],
        },
    },
    {
        "name": "不知归",
        "weapon_type": "单手剑",
        "star": 6,
        "base_atk": {"base": 51, "growth": 111, "divisor": 22, "offset": 10},
        "bonus_attrs": {
            "意志+": {"base": 20.0, "growth": 16, "divisor": 1, "offset": 0, "special": [156.0]},
            "攻击力+": {"base": 5.0, "growth": 4, "divisor": 1, "offset": 0, "special": [39.0]},
            "物理伤害+": {"base": 16.0, "growth": 3.2, "divisor": 1, "offset": 0.0, "special": [44.8]},
        },
        "special_ability": {
            "enabled": True,
            "name": "技能恢复技力时物理伤害+",
            "base": 5.0,
            "growth": 9,
            "divisor": 8,
            "offset": 0,
            "special": [],
            "max_stack": 5,
        },
    },
    {
        "name": "仰止",
        "weapon_type": "单手剑",
        "star": 5,
        "base_atk": {"base": 42, "growth": 199, "divisor": 48, "offset": 24},
        "bonus_attrs": {
            "敏捷+": {"base": 16.0, "growth": 64, "divisor": 5, "offset": 0, "special": [124.0]},
            "物理伤害+": {"base": 4.4, "growth": 24.9, "divisor": 7, "offset": 0.6, "special": [34.7]},
            "终结技伤害+": {"base": 16.0, "growth": 3.2, "divisor": 1, "offset": 0.0, "special": [44.8]},
        },
        "special_ability": {
            "enabled": True,
            "name": "下次终结技期间造成的物理伤害+",
            "base": 12.0,
            "growth": 2.4,
            "divisor": 1,
            "offset": 0.0,
            "special": [33.6],
            "max_stack": 3,
        },
    },
    {
        "name": "作品：众生",
        "weapon_type": "手铳",
        "star": 5,
        "base_atk": {"base": 42, "growth": 199, "divisor": 48, "offset": 24},
        "bonus_attrs": {
            "敏捷+": {"base": 16.0, "growth": 64, "divisor": 5, "offset": 0, "special": [124.0]},
            "法术伤害+": {"base": 4.4, "growth": 24.9, "divisor": 7, "offset": 0.6, "special": [34.7]},
            "暴击率+": {"base": 3.0, "growth": 0.6, "divisor": 1, "offset": 0.0, "special": [8.4]},
        },
        "special_ability": {
            "enabled": True,
            "name": "攻击力+",
            "base": 7.5,
            "growth": 1.5,
            "divisor": 1,
            "offset": 0.0,
            "special": [21.0],
            "max_stack": 2,
        },
    },
    {
        "name": "作品：蚀迹",
        "weapon_type": "施术单元",
        "star": 6,
        "base_atk": {"base": 49, "growth": 49, "divisor": 10, "offset": 4},
        "bonus_attrs": {
            "意志+": {"base": 20.0, "growth": 16, "divisor": 1, "offset": 0, "special": [156.0]},
            "自然伤害+": {"base": 5.6, "growth": 31.1, "divisor": 7, "offset": 0.0, "special": [43.3]},
            "攻击力+": {"base": 7.0, "growth": 1.4, "divisor": 1, "offset": 0.0, "special": [19.6]},
        },
        "special_ability": {
            "enabled": True,
            "name": "其他干员获得法术伤害+",
            "base": 5.0,
            "growth": 9,
            "divisor": 8,
            "offset": 0,
            "special": [],
        },
    },
    {
        "name": "使命必达",
        "weapon_type": "施术单元",
        "star": 6,
        "base_atk": {"base": 51, "growth": 111, "divisor": 22, "offset": 10},
        "bonus_attrs": {
            "意志+": {"base": 20.0, "growth": 16, "divisor": 1, "offset": 0, "special": [156.0]},
            "终结技充能效率+": {"base": 6.0, "growth": 23.8, "divisor": 5, "offset": 0.0, "special": [46.4]},
            "自然伤害+": {"base": 16.0, "growth": 3.2, "divisor": 1, "offset": 0.0, "special": [44.8]},
        },
        "special_ability": {
            "enabled": True,
            "name": "全队增加法术伤害+",
            "base": 12.0,
            "growth": 2.4,
            "divisor": 1,
            "offset": 0.0,
            "special": [33.6],
        },
    },
    {
        "name": "光荣记忆",
        "weapon_type": "单手剑",
        "star": 6,
        "base_atk": {"base": 50, "growth": 89, "divisor": 18, "offset": 8},
        "bonus_attrs": {
            "敏捷+": {"base": 20.0, "growth": 16, "divisor": 1, "offset": 0, "special": [156.0]},
            "暴击率+": {"base": 2.5, "growth": 2.0, "divisor": 1, "offset": 0.0, "special": [19.5]},
            "攻击力+": {"base": 7.0, "growth": 1.4, "divisor": 1, "offset": 0.0, "special": [19.6]},
        },
        "special_ability": {
            "enabled": True,
            "name": "终结技期间造成的伤害+",
            "base": 12.0,
            "growth": 2.4,
            "divisor": 1,
            "offset": 0.0,
            "special": [33.6],
            "max_stack": 3,
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
        "name": "典范",
        "weapon_type": "双手剑",
        "star": 6,
        "base_atk": {"base": 51, "growth": 111, "divisor": 22, "offset": 10},
        "bonus_attrs": {
            "主能力值+": {"base": 17.0, "growth": 68, "divisor": 5, "offset": 0, "special": [132.0]},
            "攻击力+": {"base": 5.0, "growth": 4, "divisor": 1, "offset": 0, "special": [39.0]},
            "物理伤害+": {"base": 10.0, "growth": 2, "divisor": 1, "offset": 0, "special": [28.0]},
        },
        "special_ability": {
            "enabled": True,
            "name": "额外增加物理伤害+",
            "base": 10.0,
            "growth": 2,
            "divisor": 1,
            "offset": 0,
            "special": [28.0],
            "max_stack": 3,
        },
    },
    {
        "name": "十二问",
        "weapon_type": "单手剑",
        "star": 5,
        "base_atk": {"base": 42, "growth": 199, "divisor": 48, "offset": 24},
        "bonus_attrs": {
            "敏捷+": {"base": 16.0, "growth": 64, "divisor": 5, "offset": 0, "special": [124.0]},
            "攻击力+": {"base": 4.0, "growth": 3.2, "divisor": 1, "offset": 0.0, "special": [31.2]},
            "副能力+": {"base": 5.0, "growth": 9, "divisor": 8, "offset": 0, "special": []},
        },
        "special_ability": {
            "enabled": True,
            "name": "攻击力+",
            "base": 7.5,
            "growth": 1.5,
            "divisor": 1,
            "offset": 0.0,
            "special": [21.0],
            "max_stack": 2,
        },
    },
    {
        "name": "古渠",
        "weapon_type": "双手剑",
        "star": 5,
        "base_atk": {"base": 42, "growth": 199, "divisor": 48, "offset": 24},
        "bonus_attrs": {
            "力量+": {"base": 16.0, "growth": 64, "divisor": 5, "offset": 0, "special": [124.0]},
            "源石技艺强度+": {"base": 10.0, "growth": 2, "divisor": 1, "offset": 0, "special": [28.0]},
        },
        "special_ability": {
            "enabled": True,
            "name": "物理伤害增加+",
            "base": 5.0,
            "growth": 9,
            "divisor": 8,
            "offset": 0,
            "special": [],
        },
    },
    {
        "name": "同类相食",
        "weapon_type": "手铳",
        "star": 6,
        "base_atk": {"base": 50, "growth": 89, "divisor": 18, "offset": 8},
        "bonus_attrs": {
            "主能力值+": {"base": 17.0, "growth": 68, "divisor": 5, "offset": 0, "special": [132.0]},
            "法术伤害+": {"base": 12.0, "growth": 2.4, "divisor": 1, "offset": 0.0, "special": [33.6]},
        },
        "special_ability": {
            "enabled": True,
            "name": "对应属性易伤+",
            "base": 10.0,
            "growth": 2,
            "divisor": 1,
            "offset": 0,
            "special": [28.0],
        },
    },
    {
        "name": "向心之引",
        "weapon_type": "长柄武器",
        "star": 5,
        "base_atk": {"base": 42, "growth": 199, "divisor": 48, "offset": 24},
        "bonus_attrs": {
            "意志+": {"base": 16.0, "growth": 64, "divisor": 5, "offset": 0, "special": [124.0]},
            "电磁伤害+": {"base": 4.4, "growth": 24.9, "divisor": 7, "offset": 0.6, "special": [34.7]},
            "连携技伤害+": {"base": 10.0, "growth": 2, "divisor": 1, "offset": 0, "special": [28.0]},
        },
        "special_ability": {
            "enabled": True,
            "name": "电磁伤害增加+",
            "base": 10.0,
            "growth": 2,
            "divisor": 1,
            "offset": 0,
            "special": [28.0],
            "max_stack": 3,
        },
    },
    {
        "name": "坚城铸造者",
        "weapon_type": "单手剑",
        "star": 5,
        "base_atk": {"base": 42, "growth": 83, "divisor": 20, "offset": 0},
        "bonus_attrs": {
            "智识+": {"base": 16.0, "growth": 64, "divisor": 5, "offset": 0, "special": [124.0]},
            "终结技充能效率+": {"base": 4.8, "growth": 3.8, "divisor": 1, "offset": 0.0, "special": [37.1]},
            "攻击力+": {"base": 5.0, "growth": 9, "divisor": 8, "offset": 0, "special": []},
        },
        "special_ability": {
            "enabled": True,
            "name": "源石技艺强度+",
            "base": 25.0,
            "growth": 5,
            "divisor": 1,
            "offset": 0,
            "special": [70.0],
        },
    },
    {
        "name": "塔尔11",
        "weapon_type": "单手剑",
        "star": 3,
        "base_atk": {"base": 29, "growth": 163, "divisor": 57, "offset": 3},
        "bonus_attrs": {
            "主能力+": {"base": 10, "growth": 41, "divisor": 5, "offset": 0, "special": [79]},
            "附加攻击力+": {"base": 12, "growth": 12, "divisor": 5, "offset": 2, "special": [34]},
        },
        "special_ability": {"enabled": False},
    },
    {
        "name": "大雷斑",
        "weapon_type": "双手剑",
        "star": 6,
        "base_atk": {"base": 50, "growth": 5, "divisor": 1, "offset": 0},
        "bonus_attrs": {
            "力量+": {"base": 20.0, "growth": 16, "divisor": 1, "offset": 0, "special": [156.0]},
            "最大生命值+": {"base": 10.0, "growth": 8, "divisor": 1, "offset": 0, "special": [78.0]},
            "施加的'''护盾'''效果+": {"base": 24.0, "growth": 4.8, "divisor": 1, "offset": 0.0, "special": [67.2]},
        },
        "special_ability": {
            "enabled": True,
            "name": "额外获得护盾+",
            "base": 7.0,
            "growth": 1.4,
            "divisor": 1,
            "offset": 0.0,
            "special": [19.6],
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
        "name": "孤舟",
        "weapon_type": "施术单元",
        "star": 6,
        "base_atk": {"base": 52, "growth": 247, "divisor": 48, "offset": 24},
        "bonus_attrs": {
            "意志+": {"base": 20.0, "growth": 16, "divisor": 1, "offset": 0, "special": [156.0]},
            "攻击力+": {"base": 5.0, "growth": 4, "divisor": 1, "offset": 0, "special": [39.0]},
            "电磁伤害+": {"base": 16.0, "growth": 3.2, "divisor": 1, "offset": 0.0, "special": [44.8]},
        },
        "special_ability": {
            "enabled": True,
            "name": "战技'''消耗''' '''法术异常'''，战技电磁伤害+",
            "base": 20.0,
            "growth": 4,
            "divisor": 1,
            "offset": 0,
            "special": [56.0],
            "max_stack": 2,
        },
    },
    {
        "name": "宏愿",
        "weapon_type": "单手剑",
        "star": 6,
        "base_atk": {"base": 51, "growth": 111, "divisor": 22, "offset": 10},
        "bonus_attrs": {
            "敏捷+": {"base": 20.0, "growth": 16, "divisor": 1, "offset": 0, "special": [156.0]},
            "攻击力+": {"base": 5.0, "growth": 4, "divisor": 1, "offset": 0, "special": [39.0]},
            "源石技艺强度+": {"base": 30.0, "growth": 6, "divisor": 1, "offset": 0, "special": [84.0]},
        },
        "special_ability": {
            "enabled": True,
            "name": "物理伤害+",
            "base": 36.0,
            "growth": 7.2,
            "divisor": 1,
            "offset": 0.0,
            "special": [100.8],
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
        "name": "嵌合正义",
        "weapon_type": "长柄武器",
        "star": 5,
        "base_atk": {"base": 42, "growth": 199, "divisor": 48, "offset": 24},
        "bonus_attrs": {
            "力量+": {"base": 16.0, "growth": 64, "divisor": 5, "offset": 0, "special": [124.0]},
            "终结技充能效率+": {"base": 4.8, "growth": 3.8, "divisor": 1, "offset": 0.0, "special": [37.1]},
            "暴击率+": {"base": 3.0, "growth": 0.6, "divisor": 1, "offset": 0.0, "special": [8.4]},
        },
        "special_ability": {
            "enabled": True,
            "name": "攻击力+",
            "base": 15.0,
            "growth": 3,
            "divisor": 1,
            "offset": 0,
            "special": [42.0],
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
        "name": "布道自由",
        "weapon_type": "施术单元",
        "star": 5,
        "base_atk": {"base": 42, "growth": 199, "divisor": 48, "offset": 24},
        "bonus_attrs": {
            "意志+": {"base": 16.0, "growth": 64, "divisor": 5, "offset": 0, "special": [124.0]},
            "治疗效率+": {"base": 4.8, "growth": 3.8, "divisor": 1, "offset": 0.0, "special": [37.1]},
            "主能力+": {"base": 5.0, "growth": 9, "divisor": 8, "offset": 0, "special": []},
        },
        "special_ability": {
            "enabled": True,
            "name": "额外回复+",
            "base": 60.0,
            "growth": 12,
            "divisor": 1,
            "offset": 0,
            "special": [168.0],
        },
    },
    {
        "name": "悼亡诗",
        "weapon_type": "施术单元",
        "star": 5,
        "base_atk": {"base": 42, "growth": 199, "divisor": 48, "offset": 24},
        "bonus_attrs": {
            "智识+": {"base": 16.0, "growth": 64, "divisor": 5, "offset": 0, "special": [124.0]},
            "攻击力+": {"base": 4.0, "growth": 3.2, "divisor": 1, "offset": 0.0, "special": [31.2]},
            "最大生命值+": {"base": 10.0, "growth": 2, "divisor": 1, "offset": 0, "special": [28.0]},
        },
        "special_ability": {
            "enabled": True,
            "name": "攻击力+",
            "base": 8.0,
            "growth": 1.6,
            "divisor": 1,
            "offset": 0.0,
            "special": [22.4],
        },
    },
    {
        "name": "扶摇",
        "weapon_type": "单手剑",
        "star": 6,
        "base_atk": {"base": 50, "growth": 5, "divisor": 1, "offset": 0},
        "bonus_attrs": {
            "主能力值+": {"base": 17.0, "growth": 68, "divisor": 5, "offset": 0, "special": [132.0]},
            "暴击率+": {"base": 2.5, "growth": 2.0, "divisor": 1, "offset": 0.0, "special": [19.5]},
            "战技和终结技造成的物理伤害+": {"base": 15.0, "growth": 3, "divisor": 1, "offset": 0, "special": [42.0]},
        },
        "special_ability": {
            "enabled": True,
            "name": "对'''失衡'''状态造成伤害+",
            "base": 35.0,
            "growth": 7,
            "divisor": 1,
            "offset": 0,
            "special": [98.0],
        },
    },
    {
        "name": "探骊",
        "weapon_type": "双手剑",
        "star": 5,
        "base_atk": {"base": 42, "growth": 199, "divisor": 48, "offset": 24},
        "bonus_attrs": {
            "力量+": {"base": 16.0, "growth": 64, "divisor": 5, "offset": 0, "special": [124.0]},
            "终结技充能效率+": {"base": 4.8, "growth": 3.8, "divisor": 1, "offset": 0.0, "special": [37.1]},
            "主能力+": {"base": 5.0, "growth": 9, "divisor": 8, "offset": 0, "special": []},
        },
        "special_ability": {
            "enabled": True,
            "name": "攻击力+",
            "base": 6.0,
            "growth": 1.2,
            "divisor": 1,
            "offset": 0.0,
            "special": [16.8],
            "max_stack": 3,
        },
    },
    {
        "name": "昔日精品",
        "weapon_type": "双手剑",
        "star": 6,
        "base_atk": {"base": 50, "growth": 5, "divisor": 1, "offset": 0},
        "bonus_attrs": {
            "意志+": {"base": 20.0, "growth": 16, "divisor": 1, "offset": 0, "special": [156.0]},
            "最大生命值+": {"base": 10.0, "growth": 8, "divisor": 1, "offset": 0, "special": [78.0]},
            "治疗效率+": {"base": 10.0, "growth": 2, "divisor": 1, "offset": 0, "special": [28.0]},
        },
        "special_ability": {
            "enabled": True,
            "name": "回复生命值+",
            "base": 84.0,
            "growth": 84,
            "divisor": 5,
            "offset": 2,
            "special": [235.0],
        },
    },
    {
        "name": "显赫声名",
        "weapon_type": "单手剑",
        "star": 6,
        "base_atk": {"base": 50, "growth": 89, "divisor": 18, "offset": 8},
        "bonus_attrs": {
            "主能力值+": {"base": 17.0, "growth": 68, "divisor": 5, "offset": 0, "special": [132.0]},
            "物理伤害+": {"base": 5.6, "growth": 31.1, "divisor": 7, "offset": 0.0, "special": [43.3]},
            "攻击力+": {"base": 10.0, "growth": 2, "divisor": 1, "offset": 0, "special": [28.0]},
        },
        "special_ability": {
            "enabled": True,
            "name": "'''消耗'''破防加攻+",
            "base": 5.0,
            "growth": 9,
            "divisor": 8,
            "offset": 0,
            "special": [],
        },
    },
    {
        "name": "显锋",
        "weapon_type": "单手剑",
        "star": 4,
        "base_atk": {"base": 34, "growth": 62, "divisor": 18, "offset": 16},
        "bonus_attrs": {
            "敏捷+": {"base": 12, "growth": 48, "divisor": 5, "offset": 0, "special": [93]},
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
        "name": "望乡",
        "weapon_type": "手铳",
        "star": 6,
        "base_atk": {"base": 50, "growth": 89, "divisor": 18, "offset": 8},
        "bonus_attrs": {
            "敏捷+": {"base": 20.0, "growth": 16, "divisor": 1, "offset": 0, "special": [156.0]},
            "寒冷伤害+": {"base": 5.6, "growth": 31.1, "divisor": 7, "offset": 0.0, "special": [43.3]},
            "攻击力+": {"base": 7.0, "growth": 1.4, "divisor": 1, "offset": 0.0, "special": [19.6]},
        },
        "special_ability": {
            "enabled": True,
            "name": "寒冷和自然伤害+",
            "base": 8.0,
            "growth": 1.6,
            "divisor": 1,
            "offset": 0.0,
            "special": [22.4],
            "max_stack": 2,
        },
    },
    {
        "name": "楔子",
        "weapon_type": "手铳",
        "star": 6,
        "base_atk": {"base": 51, "growth": 111, "divisor": 22, "offset": 10},
        "bonus_attrs": {
            "主能力值+": {"base": 17.0, "growth": 68, "divisor": 5, "offset": 0, "special": [132.0]},
            "暴击率+": {"base": 2.5, "growth": 2.0, "divisor": 1, "offset": 0.0, "special": [19.5]},
            "法术伤害+": {"base": 12.0, "growth": 2.4, "divisor": 1, "offset": 0.0, "special": [33.6]},
        },
        "special_ability": {
            "enabled": True,
            "name": "施放战技时，法术伤害+",
            "base": 8.0,
            "growth": 1.6,
            "divisor": 1,
            "offset": 0.0,
            "special": [22.4],
        },
    },
    {
        "name": "沧溟星梦",
        "weapon_type": "施术单元",
        "star": 6,
        "base_atk": {"base": 50, "growth": 5, "divisor": 1, "offset": 0},
        "bonus_attrs": {
            "智识+": {"base": 20.0, "growth": 16, "divisor": 1, "offset": 0, "special": [156.0]},
            "治疗效率+": {"base": 6.0, "growth": 23.8, "divisor": 5, "offset": 0.0, "special": [46.4]},
            "副能力+": {"base": 16.0, "growth": 3.2, "divisor": 1, "offset": 0.0, "special": [44.8]},
        },
        "special_ability": {
            "enabled": True,
            "name": "法术易伤+",
            "base": 10.0,
            "growth": 2,
            "divisor": 1,
            "offset": 0,
            "special": [28.0],
        },
    },
    {
        "name": "浪潮",
        "weapon_type": "单手剑",
        "star": 4,
        "base_atk": {"base": 34, "growth": 62, "divisor": 18, "offset": 16},
        "bonus_attrs": {
            "智识+": {"base": 12, "growth": 48, "divisor": 5, "offset": 0, "special": [93]},
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
        "name": "热熔切割器",
        "weapon_type": "单手剑",
        "star": 6,
        "base_atk": {"base": 50, "growth": 89, "divisor": 18, "offset": 8},
        "bonus_attrs": {
            "意志+": {"base": 20.0, "growth": 16, "divisor": 1, "offset": 0, "special": [156.0]},
            "攻击力+": {"base": 10.0, "growth": 2, "divisor": 1, "offset": 0, "special": [28.0]},
        },
        "special_ability": {
            "enabled": True,
            "name": "全队攻击力+",
            "base": 5.0,
            "growth": 9,
            "divisor": 8,
            "offset": 0,
            "special": [],
            "max_stack": 2,
        },
    },
    {
        "name": "熔铸火焰",
        "weapon_type": "单手剑",
        "star": 6,
        "base_atk": {"base": 52, "growth": 247, "divisor": 48, "offset": 24},
        "bonus_attrs": {
            "智识+": {"base": 20.0, "growth": 16, "divisor": 1, "offset": 0, "special": [156.0]},
            "攻击力+": {"base": 5.0, "growth": 4, "divisor": 1, "offset": 0, "special": [39.0]},
            "灼热伤害+": {"base": 16.0, "growth": 3.2, "divisor": 1, "offset": 0.0, "special": [44.8]},
        },
        "special_ability": {
            "enabled": True,
            "name": "普通攻击伤害+",
            "base": 75.0,
            "growth": 15,
            "divisor": 1,
            "offset": 0,
            "special": [210.0],
        },
    },
    {
        "name": "爆破单元",
        "weapon_type": "施术单元",
        "star": 6,
        "base_atk": {"base": 50, "growth": 89, "divisor": 18, "offset": 8},
        "bonus_attrs": {
            "主能力值+": {"base": 17.0, "growth": 68, "divisor": 5, "offset": 0, "special": [132.0]},
            "源石技艺强度+": {"base": 10.0, "growth": 8, "divisor": 1, "offset": 0, "special": [78.0]},
            "副能力+": {"base": 10.0, "growth": 2, "divisor": 1, "offset": 0, "special": [28.0]},
        },
        "special_ability": {
            "enabled": True,
            "name": "法术易伤+",
            "base": 9.0,
            "growth": 1.8,
            "divisor": 1,
            "offset": 0.0,
            "special": [25.2],
        },
    },
    {
        "name": "狼之绯",
        "weapon_type": "单手剑",
        "star": 6,
        "base_atk": {"base": 51, "growth": 51, "divisor": 10, "offset": 5},
        "bonus_attrs": {
            "敏捷+": {"base": 20.0, "growth": 16, "divisor": 1, "offset": 0, "special": [156.0]},
            "暴击率+": {"base": 2.5, "growth": 2.0, "divisor": 1, "offset": 0.0, "special": [19.5]},
            "攻击力+": {"base": 16.0, "growth": 3.2, "divisor": 1, "offset": 0.0, "special": [44.8]},
        },
        "special_ability": {
            "enabled": True,
            "name": "每层'''狼血'''获得物理和灼热伤害+",
            "base": 1.0,
            "growth": 0.2,
            "divisor": 1,
            "offset": 0.0,
            "special": [2.8],
            "max_stack": 16,
        },
    },
    {
        "name": "理性告别",
        "weapon_type": "手铳",
        "star": 5,
        "base_atk": {"base": 42, "growth": 199, "divisor": 48, "offset": 24},
        "bonus_attrs": {
            "力量+": {"base": 16.0, "growth": 64, "divisor": 5, "offset": 0, "special": [124.0]},
            "灼热伤害+": {"base": 4.4, "growth": 24.9, "divisor": 7, "offset": 0.6, "special": [34.7]},
            "战技伤害+": {"base": 10.0, "growth": 2, "divisor": 1, "offset": 0, "special": [28.0]},
        },
        "special_ability": {
            "enabled": True,
            "name": "攻击力+",
            "base": 16.0,
            "growth": 3.2,
            "divisor": 1,
            "offset": 0.0,
            "special": [44.8],
        },
    },
    {
        "name": "白夜新星",
        "weapon_type": "单手剑",
        "star": 6,
        "base_atk": {"base": 51, "growth": 51, "divisor": 10, "offset": 5},
        "bonus_attrs": {
            "主能力值+": {"base": 17.0, "growth": 68, "divisor": 5, "offset": 0, "special": [132.0]},
            "源石技艺强度+": {"base": 10.0, "growth": 8, "divisor": 1, "offset": 0, "special": [78.0]},
            "法术伤害+": {"base": 12.0, "growth": 2.4, "divisor": 1, "offset": 0.0, "special": [33.6]},
        },
        "special_ability": {
            "enabled": True,
            "name": "施加'''燃烧'''或'''导电'''后法术伤害+",
            "base": 12.0,
            "growth": 2.4,
            "divisor": 1,
            "offset": 0.0,
            "special": [33.6],
        },
    },
    {
        "name": "破碎君王",
        "weapon_type": "双手剑",
        "star": 6,
        "base_atk": {"base": 50, "growth": 89, "divisor": 18, "offset": 8},
        "bonus_attrs": {
            "力量+": {"base": 20.0, "growth": 16, "divisor": 1, "offset": 0, "special": [156.0]},
            "暴击率+": {"base": 2.5, "growth": 2.0, "divisor": 1, "offset": 0.0, "special": [19.5]},
            "装备者对敌人造成'''重击'''时，攻击力+": {
                "base": 10.0,
                "growth": 2,
                "divisor": 1,
                "offset": 0,
                "special": [28.0],
            },
        },
        "special_ability": {
            "enabled": True,
            "name": "'''重击'''造成的失衡值+",
            "base": 12.0,
            "growth": 2.4,
            "divisor": 1,
            "offset": 0.0,
            "special": [33.6],
        },
    },
    {
        "name": "终点之声",
        "weapon_type": "双手剑",
        "star": 5,
        "base_atk": {"base": 42, "growth": 199, "divisor": 48, "offset": 24},
        "bonus_attrs": {
            "力量+": {"base": 16.0, "growth": 64, "divisor": 5, "offset": 0, "special": [124.0]},
            "最大生命值+": {"base": 8.0, "growth": 6.4, "divisor": 1, "offset": 0.0, "special": [62.4]},
            "副能力+": {"base": 5.0, "growth": 9, "divisor": 8, "offset": 0, "special": []},
        },
        "special_ability": {
            "enabled": True,
            "name": "连携技的治疗效果+",
            "base": 20.0,
            "growth": 4,
            "divisor": 1,
            "offset": 0,
            "special": [56.0],
        },
    },
    {
        "name": "艺术暴君",
        "weapon_type": "手铳",
        "star": 6,
        "base_atk": {"base": 51, "growth": 51, "divisor": 10, "offset": 5},
        "bonus_attrs": {
            "智识+": {"base": 20.0, "growth": 16, "divisor": 1, "offset": 0, "special": [156.0]},
            "暴击率+": {"base": 2.5, "growth": 2.0, "divisor": 1, "offset": 0.0, "special": [19.5]},
            "寒冷伤害+": {"base": 16.0, "growth": 3.2, "divisor": 1, "offset": 0.0, "special": [44.8]},
        },
        "special_ability": {
            "enabled": True,
            "name": "战技或连携技暴击后，寒冷伤害+",
            "base": 14.0,
            "growth": 2.8,
            "divisor": 1,
            "offset": 0.0,
            "special": [39.2],
            "max_stack": 3,
        },
    },
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
        "name": "莫奈何",
        "weapon_type": "施术单元",
        "star": 5,
        "base_atk": {"base": 42, "growth": 199, "divisor": 48, "offset": 24},
        "bonus_attrs": {
            "意志+": {"base": 16.0, "growth": 64, "divisor": 5, "offset": 0, "special": [124.0]},
            "终结技充能效率+": {"base": 4.8, "growth": 3.8, "divisor": 1, "offset": 0.0, "special": [37.1]},
            "主能力+": {"base": 5.0, "growth": 9, "divisor": 8, "offset": 0, "special": []},
        },
        "special_ability": {
            "enabled": True,
            "name": "源石技艺强度+",
            "base": 25.0,
            "growth": 5,
            "divisor": 1,
            "offset": 0,
            "special": [70.0],
        },
    },
    {
        "name": "落草",
        "weapon_type": "手铳",
        "star": 6,
        "base_atk": {"base": 51, "growth": 51, "divisor": 10, "offset": 5},
        "bonus_attrs": {
            "敏捷+": {"base": 20.0, "growth": 16, "divisor": 1, "offset": 0, "special": [156.0]},
            "攻击力+": {"base": 5.0, "growth": 4, "divisor": 1, "offset": 0, "special": [39.0]},
            "寒冷伤害+": {"base": 16.0, "growth": 3.2, "divisor": 1, "offset": 0.0, "special": [44.8]},
        },
        "special_ability": {
            "enabled": True,
            "name": "战技或连携技施加寒冷附着后，寒冷伤害+",
            "base": 20.0,
            "growth": 4,
            "divisor": 1,
            "offset": 0,
            "special": [56.0],
        },
    },
    {
        "name": "负山",
        "weapon_type": "长柄武器",
        "star": 6,
        "base_atk": {"base": 51, "growth": 111, "divisor": 22, "offset": 10},
        "bonus_attrs": {
            "敏捷+": {"base": 20.0, "growth": 16, "divisor": 1, "offset": 0, "special": [156.0]},
            "物理伤害+": {"base": 5.6, "growth": 31.1, "divisor": 7, "offset": 0.0, "special": [43.3]},
            "对'''破防'''敌人额外造成伤害+": {"base": 20.0, "growth": 4, "divisor": 1, "offset": 0, "special": [56.0]},
        },
        "special_ability": {
            "enabled": True,
            "name": "战技施加'''破防'''时，全能力+",
            "base": 8.0,
            "growth": 1.6,
            "divisor": 1,
            "offset": 0.0,
            "special": [22.4],
        },
    },
    {
        "name": "赫拉芬格",
        "weapon_type": "双手剑",
        "star": 6,
        "base_atk": {"base": 51, "growth": 51, "divisor": 10, "offset": 5},
        "bonus_attrs": {
            "力量+": {"base": 20.0, "growth": 16, "divisor": 1, "offset": 0, "special": [156.0]},
            "攻击力+": {"base": 5.0, "growth": 4, "divisor": 1, "offset": 0, "special": [39.0]},
            "所有技能伤害+": {"base": 20.0, "growth": 4, "divisor": 1, "offset": 0, "special": [56.0]},
        },
        "special_ability": {
            "enabled": True,
            "name": "战技造成附着获得寒冷伤害+",
            "base": 10.0,
            "growth": 2,
            "divisor": 1,
            "offset": 0,
            "special": [28.0],
        },
    },
    {
        "name": "迷失荒野",
        "weapon_type": "施术单元",
        "star": 5,
        "base_atk": {"base": 42, "growth": 199, "divisor": 48, "offset": 24},
        "bonus_attrs": {
            "智识+": {"base": 16.0, "growth": 64, "divisor": 5, "offset": 0, "special": [124.0]},
            "电磁伤害+": {"base": 4.4, "growth": 24.9, "divisor": 7, "offset": 0.6, "special": [34.7]},
            "源石技艺强度+": {"base": 10.0, "growth": 2, "divisor": 1, "offset": 0, "special": [28.0]},
        },
        "special_ability": {
            "enabled": True,
            "name": "全队获得物理和电磁伤害+",
            "base": 8.0,
            "growth": 1.6,
            "divisor": 1,
            "offset": 0.0,
            "special": [22.4],
        },
    },
    {
        "name": "逐鳞3.0",
        "weapon_type": "单手剑",
        "star": 5,
        "base_atk": {"base": 42, "growth": 83, "divisor": 20, "offset": 0},
        "bonus_attrs": {
            "力量+": {"base": 16.0, "growth": 64, "divisor": 5, "offset": 0, "special": [124.0]},
            "寒冷伤害+": {"base": 4.4, "growth": 24.9, "divisor": 7, "offset": 0.6, "special": [34.7]},
            "攻击力+": {"base": 5.0, "growth": 9, "divisor": 8, "offset": 0, "special": []},
        },
        "special_ability": {
            "enabled": True,
            "name": "目标受到的寒冷伤害+",
            "base": 7.0,
            "growth": 1.4,
            "divisor": 1,
            "offset": 0.0,
            "special": [19.6],
        },
    },
    {
        "name": "遗忘",
        "weapon_type": "施术单元",
        "star": 6,
        "base_atk": {"base": 50, "growth": 5, "divisor": 1, "offset": 0},
        "bonus_attrs": {
            "智识+": {"base": 20.0, "growth": 16, "divisor": 1, "offset": 0, "special": [156.0]},
            "法术伤害+": {"base": 5.6, "growth": 31.1, "divisor": 7, "offset": 0.0, "special": [43.3]},
            "暴击率+": {"base": 5.0, "growth": 9, "divisor": 8, "offset": 0, "special": []},
        },
        "special_ability": {
            "enabled": True,
            "name": "施放终结技获得法术伤害+",
            "base": 24.0,
            "growth": 4.8,
            "divisor": 1,
            "offset": 0.0,
            "special": [67.2],
        },
    },
    {
        "name": "钢铁余音",
        "weapon_type": "单手剑",
        "star": 5,
        "base_atk": {"base": 42, "growth": 199, "divisor": 48, "offset": 24},
        "bonus_attrs": {
            "敏捷+": {"base": 16.0, "growth": 64, "divisor": 5, "offset": 0, "special": [124.0]},
            "物理伤害+": {"base": 4.4, "growth": 24.9, "divisor": 7, "offset": 0.6, "special": [34.7]},
            "攻击力+": {"base": 5.0, "growth": 9, "divisor": 8, "offset": 0, "special": []},
        },
        "special_ability": {
            "enabled": True,
            "name": "造成'''物理异常'''时获得攻击力+",
            "base": 7.5,
            "growth": 1.5,
            "divisor": 1,
            "offset": 0.0,
            "special": [21.0],
            "max_stack": 2,
        },
    },
    {
        "name": "雾中微光",
        "weapon_type": "施术单元",
        "star": 6,
        "base_atk": {"base": 50, "growth": 89, "divisor": 18, "offset": 8},
        "bonus_attrs": {
            "意志+": {"base": 20.0, "growth": 16, "divisor": 1, "offset": 0, "special": [156.0]},
            "电磁伤害+": {"base": 5.6, "growth": 31.1, "divisor": 7, "offset": 0.0, "special": [43.3]},
            "攻击力+": {"base": 7.0, "growth": 1.4, "divisor": 1, "offset": 0.0, "special": [19.6]},
        },
        "special_ability": {
            "enabled": True,
            "name": "电磁伤害增加+",
            "base": 5.5,
            "growth": 1.1,
            "divisor": 1,
            "offset": 0.0,
            "special": [15.4],
            "max_stack": 3,
        },
    },
    {
        "name": "领航者",
        "weapon_type": "手铳",
        "star": 6,
        "base_atk": {"base": 50, "growth": 89, "divisor": 18, "offset": 8},
        "bonus_attrs": {
            "智识+": {"base": 17.0, "growth": 68, "divisor": 5, "offset": 0, "special": [132.0]},
            "寒冷伤害+": {"base": 5.6, "growth": 31.1, "divisor": 7, "offset": 0.0, "special": [43.3]},
            "暴击率+": {"base": 3.5, "growth": 0.7, "divisor": 1, "offset": 0.0, "special": [9.8]},
        },
        "special_ability": {
            "enabled": True,
            "name": "寒冷或自然伤害+",
            "base": 3.5,
            "growth": 0.7,
            "divisor": 1,
            "offset": 0.0,
            "special": [9.8],
        },
    },
    {
        "name": "骁勇",
        "weapon_type": "长柄武器",
        "star": 6,
        "base_atk": {"base": 50, "growth": 5, "divisor": 1, "offset": 0},
        "bonus_attrs": {
            "敏捷+": {"base": 20.0, "growth": 16, "divisor": 1, "offset": 0, "special": [156.0]},
            "物理伤害+": {"base": 5.6, "growth": 31.1, "divisor": 7, "offset": 0.0, "special": [43.3]},
            "攻击力+": {"base": 10.0, "growth": 2, "divisor": 1, "offset": 0, "special": [28.0]},
        },
        "special_ability": {
            "enabled": True,
            "name": "额外造成伤害+",
            "base": 120.0,
            "growth": 24,
            "divisor": 1,
            "offset": 0,
            "special": [336.0],
        },
    },
    {
        "name": "骑士精神",
        "weapon_type": "施术单元",
        "star": 6,
        "base_atk": {"base": 49, "growth": 49, "divisor": 10, "offset": 4},
        "bonus_attrs": {
            "意志+": {"base": 20.0, "growth": 16, "divisor": 1, "offset": 0, "special": [156.0]},
            "最大生命值+": {"base": 10.0, "growth": 8, "divisor": 1, "offset": 0, "special": [78.0]},
            "治疗效率+": {"base": 10.0, "growth": 2, "divisor": 1, "offset": 0, "special": [28.0]},
        },
        "special_ability": {
            "enabled": True,
            "name": "全队攻击力+",
            "base": 9.0,
            "growth": 1.8,
            "divisor": 1,
            "offset": 0.0,
            "special": [25.2],
        },
    },
    {
        "name": "黯色火炬",
        "weapon_type": "单手剑",
        "star": 6,
        "base_atk": {"base": 50, "growth": 89, "divisor": 18, "offset": 8},
        "bonus_attrs": {
            "智识+": {"base": 20.0, "growth": 16, "divisor": 1, "offset": 0, "special": [156.0]},
            "灼热伤害+": {"base": 5.6, "growth": 31.1, "divisor": 7, "offset": 0.0, "special": [43.3]},
            "攻击力+": {"base": 7.0, "growth": 1.4, "divisor": 1, "offset": 0.0, "special": [19.6]},
        },
        "special_ability": {
            "enabled": True,
            "name": "灼热自然伤害增加+",
            "base": 8.0,
            "growth": 1.6,
            "divisor": 1,
            "offset": 0.0,
            "special": [22.4],
            "max_stack": 2,
        },
    },
]


def main() -> None:
    for spec in _SEED_WEAPONS:
        add_weapon(**spec)


if __name__ == "__main__":
    main()
