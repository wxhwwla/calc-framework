#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用角色添加脚本（自动生成）
"""
import json
from pathlib import Path

from calculation.formula import (
    calculate_growth_curve,
    calculate_skill_curve,
)

def add_character(
    name: str,
    char_type: str,
    star: int,
    primary: str,
    secondary: str,
    weapon: str,
    strength: dict,
    agility: dict,
    intellect: dict,
    will: dict,
    base_atk: dict,
    sk1: list,
    sk2: list,
    sk3: list,
):
    """添加新角色到 characters.json"""
    def calc_skill(params):
        if params.get("divisor", 1) == 0:
            return []
        special = params.pop("special", None)
        return calculate_skill_curve(**params, special_values=special)

    character = {
        "名称": name,
        "类型": char_type,
        "星级": star,
        "武器": weapon,
        "等级": list(range(1, 91)),
        "潜能": list(range(0, 6)),
        "信赖": list(range(0, 5)),
        "信赖加成": [0, 10, 15, 15, 20],
        "主能力": primary,
        "副能力": secondary,
        "力量": calculate_growth_curve(**strength),
        "敏捷": calculate_growth_curve(**agility),
        "智识": calculate_growth_curve(**intellect),
        "意志": calculate_growth_curve(**will),
        "基础攻击力": calculate_growth_curve(**base_atk),
        "战技倍率": [calc_skill(s.copy()) for s in sk1],
        "连携技倍率": [calc_skill(s.copy()) for s in sk2],
        "终结技倍率": [calc_skill(s.copy()) for s in sk3],
    }

    json_path = Path(__file__).parent / "characters.json"
    with open(json_path, "r", encoding="utf-8") as f:
        characters = json.load(f)

    existing = [c for c in characters if c["名称"] == name]
    if existing:
        print(f"角色「{name}」已存在，覆盖数据。")
        characters = [c for c in characters if c["名称"] != name]

    characters.append(character)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(characters, f, ensure_ascii=False, indent=2)

    print(f"角色「{name}」已添加！")


if __name__ == "__main__":
    print("="*60)
    print("通用角色添加工具（自动生成）")
    print("="*60)

    # ========== 管理员 ==========
    add_character(
        name="管理员",
        char_type="近卫",
        star=6,
        primary="敏捷",
        secondary="力量",
        weapon="单手剑",

        strength={"base": 14, "growth": 11, "divisor": 9, "offset": 8},
        agility={"base": 14, "growth": 17, "divisor": 12, "offset": 5},
        intellect={"base": 9, "growth": 47, "divisor": 48, "offset": 38},
        will={"base": 10, "growth": 13, "divisor": 12, "offset": 9},
        base_atk={"base": 30, "growth": 13, "divisor": 4, "offset": 1},

        sk1=[
            {"base": 156, "growth": 78, "divisor": 5, "offset": 0, "special": [300, 323, 350]},
        ],
        sk2=[
            {"base": 45, "growth": 22, "divisor": 5, "offset": 1, "special": [86, 93, 100]},
            {"base": 178, "growth": 71, "divisor": 4, "offset": 1, "special": [342, 369, 400]},
        ],
        sk3=[
            {"base": 356, "growth": 71, "divisor": 2, "offset": 0, "special": [684, 738, 800]},
            {"base": 267, "growth": 80, "divisor": 3, "offset": 1, "special": [514, 554, 600]},
        ],
    )

    # ========== 陈千语 ==========
    add_character(
        name="陈千语",
        char_type="近卫",
        star=5,
        primary="敏捷",
        secondary="力量",
        weapon="单手剑",

        strength={"base": 10, "growth": 14, "divisor": 13, "offset": 10},
        agility={"base": 20, "growth": 107, "divisor": 63, "offset": 37},
        intellect={"base": 8, "growth": 19, "divisor": 22, "offset": 19},
        will={"base": 9, "growth": 53, "divisor": 56, "offset": 38},
        base_atk={"base": 30, "growth": 3, "divisor": 1, "offset": 0},

        sk1=[
            {"base": 169, "growth": 101, "divisor": 6, "offset": 2, "special": [325, 350, 380]},
        ],
        sk2=[
            {"base": 120, "growth": 12, "divisor": 1, "offset": 0, "special": [231, 249, 270]},
        ],
        sk3=[
            {"base": 36, "growth": 18, "divisor": 5, "offset": 2, "special": [69, 75, 81]},
            {"base": 455, "growth": 318, "divisor": 7, "offset": 0, "special": [875, 943, 1023]},
        ],
    )

    # ========== 昼雪 ==========
    add_character(
        name="昼雪",
        char_type="重装",
        star=5,
        primary="力量",
        secondary="意志",
        weapon="双手剑",

        strength={"base": 18, "growth": 72, "divisor": 47, "offset": 26},
        agility={"base": 12, "growth": 57, "divisor": 55, "offset": 19},
        intellect={"base": 9, "growth": 37, "divisor": 39, "offset": 18},
        will={"base": 10, "growth": 98, "divisor": 89, "offset": 88},
        base_atk={"base": 30, "growth": 3, "divisor": 1, "offset": 0},

        sk1=[
            {"base": 200, "growth": 20, "divisor": 1, "offset": 0, "special": [385, 415, 450]},
        ],
        sk2=[
        ],
        sk3=[
            {"base": 200, "growth": 20, "divisor": 1, "offset": 0, "special": [385, 415, 450]},
            {"base": 29, "growth": 17, "divisor": 6, "offset": 2, "special": [55, 60, 65]},
        ],
    )

    # ========== 佩丽卡 ==========
    add_character(
        name="佩丽卡",
        char_type="术师",
        star=5,
        primary="智识",
        secondary="意志",
        weapon="施术单元",

        strength={"base": 11, "growth": 77, "divisor": 8, "offset": 7},
        agility={"base": 9, "growth": 37, "divisor": 39, "offset": 18},
        intellect={"base": 21, "growth": 96, "divisor": 61, "offset": 39},
        will={"base": 13, "growth": 73, "divisor": 65, "offset": 40},
        base_atk={"base": 30, "growth": 187, "divisor": 61, "offset": 32},

        sk1=[
            {"base": 178, "growth": 89, "divisor": 5, "offset": 1, "special": [342, 369, 400]},
        ],
        sk2=[
            {"base": 80, "growth": 8, "divisor": 1, "offset": 0, "special": [154, 166, 180]},
        ],
        sk3=[
            {"base": 445, "growth": 222, "divisor": 5, "offset": 1, "special": [385, 415, 450]},
        ],
    )

    # ========== 艾尔黛拉 ==========
    add_character(
        name="艾尔黛拉",
        char_type="辅助",
        star=6,
        primary="智识",
        secondary="意志",
        weapon="施术单元",

        strength={"base": 9, "growth": 23, "divisor": 20, "offset": 15},
        agility={"base": 9, "growth": 37, "divisor": 39, "offset": 18},
        intellect={"base": 20, "growth": 41, "divisor": 29, "offset": 3},
        will={"base": 15, "growth": 23, "divisor": 20, "offset": 17},
        base_atk={"base": 30, "growth": 155, "divisor": 47, "offset": 22},

        sk1=[
            {"base": 147, "growth": 57, "divisor": 4, "offset": 2, "special": [274, 295, 320]},
        ],
        sk2=[
            {"base": 45, "growth": 22, "divisor": 5, "offset": 1, "special": [86, 93, 100]},
            {"base": 111, "growth": 56, "divisor": 5, "offset": 0, "special": [214, 230, 250]},
        ],
        sk3=[
            {"base": 73, "growth": 22, "divisor": 3, "offset": 2, "special": [141, 152, 165]},
        ],
    )

    # ========== 埃特拉 ==========
    add_character(
        name="埃特拉",
        char_type="近卫",
        star=4,
        primary="意志",
        secondary="力量",
        weapon="长柄武器",

        strength={"base": 13, "growth": 36, "divisor": 35, "offset": 2},
        agility={"base": 8, "growth": 1, "divisor": 1, "offset": 0},
        intellect={"base": 14, "growth": 131, "divisor": 12, "offset": 1},
        will={"base": 15, "growth": 23, "divisor": 15, "offset": 0},
        base_atk={"base": 30, "growth": 19, "divisor": 6, "offset": 2},

        sk1=[
            {"base": 156, "growth": 78, "divisor": 5, "offset": 0, "special": [300, 323, 350]},
        ],
        sk2=[
            {"base": 160, "growth": 16, "divisor": 1, "offset": 0, "special": [308, 332, 360]},
            {"base": 280, "growth": 28, "divisor": 1, "offset": 0, "special": [539, 581, 630]},
        ],
        sk3=[
            {"base": 489, "growth": 342, "divisor": 7, "offset": 1, "special": [941, 1014, 1100]},
        ],
    )

    # ========== 秋栗 ==========
    add_character(
        name="秋栗",
        char_type="先锋",
        star=4,
        primary="敏捷",
        secondary="智识",
        weapon="单手剑",

        strength={"base": 13, "growth": 61, "divisor": 56, "offset": 25},
        agility={"base": 15, "growth": 65, "divisor": 46, "offset": 7},
        intellect={"base": 12, "growth": 53, "divisor": 50, "offset": 23},
        will={"base": 9, "growth": 61, "divisor": 55, "offset": 16},
        base_atk={"base": 30, "growth": 13, "divisor": 4, "offset": 1},

        sk1=[
            {"base": 142, "growth": 57, "divisor": 4, "offset": 2, "special": [274, 295, 320]},
        ],
        sk2=[
            {"base": 80, "growth": 8, "divisor": 1, "offset": 0, "special": [308, 332, 360]},
        ],
        sk3=[
        ],
    )

    # ========== 狼卫 ==========
    add_character(
        name="狼卫",
        char_type="术师",
        star=5,
        primary="力量",
        secondary="敏捷",
        weapon="手铳",

        strength={"base": 18, "growth": 37, "divisor": 23, "offset": 12},
        agility={"base": 9, "growth": 27, "divisor": 28, "offset": 17},
        intellect={"base": 9, "growth": 76, "divisor": 81, "offset": 30},
        will={"base": 13, "growth": 79, "divisor": 72, "offset": 59},
        base_atk={"base": 30, "growth": 89, "divisor": 30, "offset": 15},

        sk1=[
            {"base": 102, "growth": 41, "divisor": 4, "offset": 1, "special": [196, 212, 230]},
            {"base": 378, "growth": 151, "divisor": 4, "offset": 0, "special": [727, 784, 850]},
        ],
        sk2=[
            {"base": 60, "growth": 6, "divisor": 1, "offset": 0, "special": [116, 125, 135]},
        ],
        sk3=[
            {"base": 32, "growth": 16, "divisor": 5, "offset": 2, "special": [62, 66, 72]},
        ],
    )

    # ========== 卡契尔 ==========
    add_character(
        name="卡契尔",
        char_type="重装",
        star=4,
        primary="力量",
        secondary="意志",
        weapon="双手剑",

        strength={"base": 21, "growth": 40, "divisor": 23, "offset": 14},
        agility={"base": 9, "growth": 47, "divisor": 48, "offset": 38},
        intellect={"base": 8, "growth": 71, "divisor": 81, "offset": 60},
        will={"base": 11, "growth": 61, "divisor": 57, "offset": 26},
        base_atk={"base": 30, "growth": 91, "divisor": 30, "offset": 14},

        sk1=[
            {"base": 178, "growth": 89, "divisor": 5, "offset": 1, "special": [342, 369, 400]},
        ],
        sk2=[
            {"base": 25, "growth": 12, "divisor": 5, "offset": 1, "special": [47, 51, 55]},
            {"base": 100, "growth": 10, "divisor": 1, "offset": 0, "special": [193, 208, 225]},
        ],
        sk3=[
            {"base": 89, "growth": 62, "divisor": 7, "offset": 6, "special": [172, 185, 200]},
            {"base": 120, "growth": 12, "divisor": 1, "offset": 0, "special": [231, 249, 270]},
            {"base": 178, "growth": 71, "divisor": 4, "offset": 1, "special": [342, 369, 400]},
        ],
    )

    # ========== 安塔尔 ==========
    add_character(
        name="安塔尔",
        char_type="辅助",
        star=4,
        primary="智识",
        secondary="力量",
        weapon="施术单元",

        strength={"base": 15, "growth": 51, "divisor": 40, "offset": 35},
        agility={"base": 9, "growth": 53, "divisor": 61, "offset": 29},
        intellect={"base": 15, "growth": 69, "divisor": 41, "offset": 18},
        will={"base": 9, "growth": 32, "divisor": 39, "offset": 30},
        base_atk={"base": 30, "growth": 3, "divisor": 1, "offset": 0},

        sk1=[
            {"base": 89, "growth": 44, "divisor": 5, "offset": 3, "special": [171, 185, 200]},
        ],
        sk2=[
            {"base": 151, "growth": 76, "divisor": 5, "offset": 0, "special": [291, 313, 340]},
        ],
        sk3=[
        ],
    )

    # ========== 萤石 ==========
    add_character(
        name="萤石",
        char_type="术师",
        star=4,
        primary="敏捷",
        secondary="智识",
        weapon="手铳",

        strength={"base": 14, "growth": 47, "divisor": 55, "offset": 7},
        agility={"base": 14, "growth": 119, "divisor": 69, "offset": 47},
        intellect={"base": 12, "growth": 70, "divisor": 61, "offset": 28},
        will={"base": 10, "growth": 57, "divisor": 62, "offset": 6},
        base_atk={"base": 30, "growth": 187, "divisor": 61, "offset": 32},

        sk1=[
            {"base": 187, "growth": 56, "divisor": 3, "offset": 1, "special": [360, 388, 420]},
        ],
        sk2=[
            {"base": 169, "growth": 101, "divisor": 6, "offset": 5, "special": [325, 351, 380]},
        ],
        sk3=[
            {"base": 111, "growth": 56, "divisor": 5, "offset": 1, "special": [214, 231, 250]},
        ],
    )

    # ========== 阿列什 ==========
    add_character(
        name="阿列什",
        char_type="先锋",
        star=5,
        primary="力量",
        secondary="智识",
        weapon="单手剑",

        strength={"base": 20, "growth": 31, "divisor": 20, "offset": 2},
        agility={"base": 9, "growth": 34, "divisor": 35, "offset": 16},
        intellect={"base": 13, "growth": 29, "divisor": 23, "offset": 13},
        will={"base": 10, "growth": 8, "divisor": 9, "offset": 7},
        base_atk={"base": 30, "growth": 213, "divisor": 68, "offset": 33},

        sk1=[
            {"base": 200, "growth": 20, "divisor": 1, "offset": 0, "special": [385, 415, 450]},
        ],
        sk2=[
            {"base": 133, "growth": 40, "divisor": 3, "offset": 2, "special": [257, 277, 300]},
            {"base": 213, "growth": 64, "divisor": 3, "offset": 2, "special": [411, 443, 480]},
        ],
        sk3=[
            {"base": 436, "growth": 305, "divisor": 7, "offset": 0, "special": [839, 904, 980]},
        ],
    )

    # ========== 弧光 ==========
    add_character(
        name="弧光",
        char_type="先锋",
        star=5,
        primary="敏捷",
        secondary="智识",
        weapon="单手剑",

        strength={"base": 14, "growth": 21, "divisor": 20, "offset": 0},
        agility={"base": 14, "growth": 47, "divisor": 32, "offset": 22},
        intellect={"base": 12, "growth": 5, "divisor": 4, "offset": 1},
        will={"base": 10, "growth": 88, "divisor": 87, "offset": 0},
        base_atk={"base": 30, "growth": 31, "divisor": 10, "offset": 4},

        sk1=[
            {"base": 45, "growth": 9, "divisor": 2, "offset": 1, "special": [87, 93, 101]},
            {"base": 180, "growth": 18, "divisor": 1, "offset": 0, "special": [347, 374, 405]},
        ],
        sk2=[
            {"base": 155, "growth": 78, "divisor": 5, "offset": 3, "special": [299, 322, 350]},
        ],
        sk3=[
            {"base": 156, "growth": 78, "divisor": 5, "offset": 0, "special": [300, 323, 350]},
            {"base": 244, "growth": 171, "divisor": 7, "offset": 6, "special": [470, 507, 550]},
        ],
    )

    # ========== 骏卫 ==========
    add_character(
        name="骏卫",
        char_type="先锋",
        star=6,
        primary="意志",
        secondary="敏捷",
        weapon="单手剑",

        strength={"base": 12, "growth": 1, "divisor": 1, "offset": 0},
        agility={"base": 13, "growth": 38, "divisor": 35, "offset": 21},
        intellect={"base": 10, "growth": 38, "divisor": 39, "offset": 11},
        will={"base": 20, "growth": 117, "divisor": 68, "offset": 7},
        base_atk={"base": 30, "growth": 111, "divisor": 34, "offset": 16},

        sk1=[
            {"base": 86, "growth": 17, "divisor": 2, "offset": 0, "special": [165, 177, 192]},
            {"base": 106, "growth": 74, "divisor": 7, "offset": 0, "special": [203, 219, 238]},
        ],
        sk2=[
            {"base": 42, "growth": 21, "divisor": 5, "offset": 2, "special": [81, 87, 95]},
            {"base": 54, "growth": 27, "divisor": 5, "offset": 2, "special": [104, 112, 122]},
            {"base": 66, "growth": 33, "divisor": 5, "offset": 2, "special": [127, 137, 149]},
            {"base": 132, "growth": 66, "divisor": 5, "offset": 2, "special": [254, 274, 297]},
        ],
        sk3=[
            {"base": 133, "growth": 93, "divisor": 7, "offset": 5, "special": [256, 276, 300]},
            {"base": 45, "growth": 31, "divisor": 7, "offset": 0, "special": [86, 92, 100]},
            {"base": 200, "growth": 20, "divisor": 1, "offset": 0, "special": [385, 415, 450]},
        ],
    )

    # ========== 余烬 ==========
    add_character(
        name="余烬",
        char_type="重装",
        star=6,
        primary="力量",
        secondary="意志",
        weapon="双手剑",

        strength={"base": 21, "growth": 40, "divisor": 23, "offset": 14},
        agility={"base": 9, "growth": 47, "divisor": 48, "offset": 38},
        intellect={"base": 8, "growth": 71, "divisor": 81, "offset": 60},
        will={"base": 13, "growth": 103, "divisor": 86, "offset": 52},
        base_atk={"base": 30, "growth": 155, "divisor": 47, "offset": 22},

        sk1=[
            {"base": 173, "growth": 52, "divisor": 3, "offset": 2, "special": [334, 360, 390]},
        ],
        sk2=[
            {"base": 102, "growth": 51, "divisor": 5, "offset": 2, "special": [196, 212, 230]},
        ],
        sk3=[
            {"base": 289, "growth": 144, "divisor": 5, "offset": 3, "special": [556, 599, 650]},
        ],
    )

    # ========== 汤汤 ==========
    add_character(
        name="汤汤",
        char_type="术师",
        star=6,
        primary="敏捷",
        secondary="力量",
        weapon="手铳",

        strength={"base": 13, "growth": 89, "divisor": 72, "offset": 42},
        agility={"base": 23, "growth": 107, "divisor": 61, "offset": 30},
        intellect={"base": 8, "growth": 19, "divisor": 22, "offset": 19},
        will={"base": 10, "growth": 33, "divisor": 32, "offset": 9},
        base_atk={"base": 30, "growth": 111, "divisor": 34, "offset": 16},

        sk1=[
            {"base": 80, "growth": 8, "divisor": 1, "offset": 0, "special": [154, 166, 180]},
            {"base": 133, "growth": 107, "divisor": 8, "offset": 7, "special": [257, 277, 300]},
        ],
        sk2=[
            {"base": 107, "growth": 32, "divisor": 3, "offset": 0, "special": [205, 221, 240]},
        ],
        sk3=[
            {"base": 142, "growth": 57, "divisor": 4, "offset": 2, "special": [274, 295, 320]},
            {"base": 178, "growth": 71, "divisor": 4, "offset": 1, "special": [342, 369, 400]},
            {"base": 311, "growth": 156, "divisor": 5, "offset": 1, "special": [599, 646, 700]},
        ],
    )

    # ========== 赛希 ==========
    add_character(
        name="赛希",
        char_type="辅助",
        star=5,
        primary="意志",
        secondary="智识",
        weapon="施术单元",

        strength={"base": 9, "growth": 19, "divisor": 21, "offset": 6},
        agility={"base": 9, "growth": 38, "divisor": 41, "offset": 15},
        intellect={"base": 15, "growth": 5, "divisor": 4, "offset": 3},
        will={"base": 15, "growth": 97, "divisor": 64, "offset": 9},
        base_atk={"base": 30, "growth": 179, "divisor": 61, "offset": 28},

        sk1=[
        ],
        sk2=[
            {"base": 200, "growth": 20, "divisor": 1, "offset": 0, "special": [385, 415, 450]},
        ],
        sk3=[
        ],
    )

    # ========== 洁尔佩塔 ==========
    add_character(
        name="洁尔佩塔",
        char_type="辅助",
        star=6,
        primary="意志",
        secondary="智识",
        weapon="施术单元",

        strength={"base": 9, "growth": 49, "divisor": 54, "offset": 3},
        agility={"base": 9, "growth": 76, "divisor": 81, "offset": 30},
        intellect={"base": 16, "growth": 61, "divisor": 49, "offset": 12},
        will={"base": 20, "growth": 17, "divisor": 10, "offset": 4},
        base_atk={"base": 30, "growth": 37, "divisor": 11, "offset": 5},

        sk1=[
            {"base": 97, "growth": 39, "divisor": 4, "offset": 2, "special": [187, 202, 219]},
            {"base": 58, "growth": 23, "divisor": 4, "offset": 0, "special": [111, 120, 130]},
        ],
        sk2=[
            {"base": 140, "growth": 14, "divisor": 1, "offset": 0, "special": [270, 291, 315]},
        ],
        sk3=[
            {"base": 333, "growth": 167, "divisor": 5, "offset": 3, "special": [642, 692, 750]},
        ],
    )

    # ========== 黎风 ==========
    add_character(
        name="黎风",
        char_type="近卫",
        star=6,
        primary="敏捷",
        secondary="力量",
        weapon="长柄武器",

        strength={"base": 14, "growth": 71, "divisor": 58, "offset": 43},
        agility={"base": 20, "growth": 63, "divisor": 50, "offset": 6},
        intellect={"base": 13, "growth": 39, "divisor": 34, "offset": 13},
        will={"base": 12, "growth": 47, "divisor": 40, "offset": 35},
        base_atk={"base": 30, "growth": 19, "divisor": 6, "offset": 2},

        sk1=[
            {"base": 38, "growth": 19, "divisor": 5, "offset": 3, "special": [73, 79, 86]},
            {"base": 119, "growth": 59, "divisor": 5, "offset": 4, "special": [229, 247, 268]},
        ],
        sk2=[
            {"base": 47, "growth": 14, "divisor": 3, "offset": 0, "special": [90, 97, 105]},
            {"base": 167, "growth": 50, "divisor": 3, "offset": 0, "special": [321, 346, 375]},
        ],
        sk3=[
            {"base": 178, "growth": 71, "divisor": 4, "offset": 1, "special": [342, 369, 400]},
            {"base": 267, "growth": 80, "divisor": 3, "offset": 1, "special": [514, 554, 600]},
        ],
    )

    # ========== 洛茜 ==========
    add_character(
        name="洛茜",
        char_type="近卫",
        star=6,
        primary="敏捷",
        secondary="智识",
        weapon="单手剑",

        strength={"base": 9, "growth": 86, "divisor": 87, "offset": 86},
        agility={"base": 23, "growth": 81, "divisor": 47, "offset": 8},
        intellect={"base": 14, "growth": 62, "divisor": 53, "offset": 0},
        will={"base": 9, "growth": 39, "divisor": 43, "offset": 3},
        base_atk={"base": 30, "growth": 155, "divisor": 47, "offset": 22},

        sk1=[
            {"base": 85, "growth": 43, "divisor": 5, "offset": 2, "special": [164, 177, 192]},
            {"base": 128, "growth": 51, "divisor": 4, "offset": 1, "special": [246, 265, 288]},
        ],
        sk2=[
            {"base": 67, "growth": 20, "divisor": 3, "offset": 0, "special": [128, 138, 150]},
            {"base": 133, "growth": 40, "divisor": 3, "offset": 2, "special": [257, 277, 300]},
            {"base": 80, "growth": 8, "divisor": 1, "offset": 0, "special": [154, 166, 180]},
        ],
        sk3=[
            {"base": 275, "growth": 25, "divisor": 1, "offset": 0, "special": [525, 550, 600]},
            {"base": 111, "growth": 56, "divisor": 5, "offset": 1, "special": [214, 231, 250]},
            {"base": 333, "growth": 167, "divisor": 5, "offset": 3, "special": [642, 692, 750]},
        ],
    )

    # ========== 大潘 ==========
    add_character(
        name="大潘",
        char_type="突击",
        star=5,
        primary="力量",
        secondary="意志",
        weapon="双手剑",

        strength={"base": 24, "growth": 100, "divisor": 59, "offset": 16},
        agility={"base": 9, "growth": 47, "divisor": 48, "offset": 38},
        intellect={"base": 10, "growth": 41, "divisor": 43, "offset": 4},
        will={"base": 10, "growth": 67, "divisor": 65, "offset": 28},
        base_atk={"base": 30, "growth": 187, "divisor": 61, "offset": 32},

        sk1=[
            {"base": 133, "growth": 93, "divisor": 7, "offset": 5, "special": [256, 276, 300]},
        ],
        sk2=[
            {"base": 289, "growth": 173, "divisor": 6, "offset": 2, "special": [556, 599, 650]},
        ],
        sk3=[
            {"base": 22, "growth": 11, "divisor": 5, "offset": 2, "special": [42, 46, 50]},
            {"base": 178, "growth": 71, "divisor": 4, "offset": 1, "special": [342, 369, 400]},
        ],
    )
 
    # ========== 艾维文娜 ==========
    add_character(
        name="艾维文娜",
        char_type="突击",
        star=5,
        primary="意志",
        secondary="敏捷",
        weapon="长柄武器",

        strength={"base": 12, "growth": 69, "divisor": 65, "offset": 57},
        agility={"base": 10, "growth": 14, "divisor": 13, "offset": 10},
        intellect={"base": 14, "growth": 13, "divisor": 12, "offset": 1},
        will={"base": 15, "growth": 3, "divisor": 2, "offset": 0},
        base_atk={"base": 30, "growth": 19, "divisor": 6, "offset": 2},

        sk1=[
            {"base": 67, "growth": 20, "divisor": 3, "offset": 0, "special": [128, 138, 150]},
            {"base": 75, "growth": 37, "divisor": 5, "offset": 1, "special": [144, 155, 168]},
            {"base": 192, "growth": 96, "divisor": 5, "offset": 2, "special": [370, 398, 432]},
        ],
        sk2=[
            {"base": 169, "growth": 101, "divisor": 6, "offset": 2, "special": [325, 350, 380]},
        ],
        sk3=[
            {"base": 422, "growth": 211, "divisor": 5, "offset": 3, "special": [813, 876, 950]},
        ],
    )

    # ========== 别礼 ==========
    add_character(
        name="别礼",
        char_type="突击",
        star=6,
        primary="力量",
        secondary="意志",
        weapon="双手剑",

        strength={"base": 21, "growth": 3, "divisor": 2, "offset": 1},
        agility={"base": 8, "growth": 59, "divisor": 55, "offset": 42},
        intellect={"base": 9, "growth": 37, "divisor": 39, "offset": 18},
        will={"base": 15, "growth": 21, "divisor": 20, "offset": 17},
        base_atk={"base": 30, "growth": 197, "divisor": 58, "offset": 29},

        sk1=[
            {"base": 142, "growth": 57, "divisor": 4, "offset": 2, "special": [274, 295, 320]},
        ],
        sk2=[
            {"base": 71, "growth": 36, "divisor": 5, "offset": 0, "special": [137, 147, 160]},
            {"base": 107, "growth": 32, "divisor": 3, "offset": 0, "special": [205, 221, 240]},
        ],
        sk3=[
            {"base": 178, "growth": 71, "divisor": 4, "offset": 1, "special": [342, 369, 400]},
            {"base": 356, "growth": 71, "divisor": 2, "offset": 0, "special": [684, 738, 800]},
        ],
    )

    # ========== 莱万汀 ==========
    add_character(
        name="莱万汀",
        char_type="突击",
        star=6,
        primary="智识",
        secondary="力量",
        weapon="单手剑",

        strength={"base": 13, "growth": 86, "divisor": 71, "offset": 41},
        agility={"base": 9, "growth": 64, "divisor": 63, "offset": 36},
        intellect={"base": 22, "growth": 89, "divisor": 51, "offset": 25},
        will={"base": 9, "growth": 49, "divisor": 54, "offset": 3},
        base_atk={"base": 30, "growth": 181, "divisor": 56, "offset": 25},

        sk1=[
            {"base": 62, "growth": 31, "divisor": 5, "offset": 3, "special": [120, 129, 140]},
            {"base": 6, "growth": 3, "divisor": 5, "offset": 4, "special": [12, 13, 14]},
            {"base": 342, "growth": 171, "divisor": 5, "offset": 2, "special": [658, 710, 770]},
            {"base": 147, "growth": 44, "divisor": 3, "offset": 0, "special": [282, 304, 330]},
            {"base": 164, "growth": 115, "divisor": 7, "offset": 6, "special": [316, 341, 370]},
            {"base": 400, "growth": 40, "divisor": 1, "offset": 0, "special": [770, 830, 900]},
        ],
        sk2=[
            {"base": 240, "growth": 24, "divisor": 1, "offset": 0, "special": [462, 498, 540]},
        ],
        sk3=[
            {"base": 65, "growth": 13, "divisor": 2, "offset": 0, "special": [125, 134, 146]},
            {"base": 81, "growth": 41, "divisor": 5, "offset": 0, "special": [156, 168, 182]},
            {"base": 115, "growth": 81, "divisor": 7, "offset": 6, "special": [222, 240, 260]},
            {"base": 203, "growth": 81, "divisor": 4, "offset": 0, "special": [390, 420, 456]},
        ],
    )

    # ========== 庄方宜 ==========
    add_character(
        name="庄方宜",
        char_type="突击",
        star=6,
        primary="意志",
        secondary="智识",
        weapon="施术单元",

        strength={"base": 10, "growth": 1, "divisor": 1, "offset": 0},
        agility={"base": 10, "growth": 1, "divisor": 1, "offset": 0},
        intellect={"base": 17, "growth": 6, "divisor": 5, "offset": 0},
        will={"base": 24, "growth": 95, "divisor": 53, "offset": 39},
        base_atk={"base": 30, "growth": 203, "divisor": 61, "offset": 40},

        sk1=[
            {"base": 20, "growth": 2, "divisor": 1, "offset": 0, "special": [39, 42, 45]},
            {"base": 3, "growth": 1, "divisor": 3, "offset": 2, "special": [7, 8, 9]},
            {"base": 36, "growth": 18, "divisor": 5, "offset": 2, "special": [69, 75, 81]},
            {"base": 8, "growth": 4, "divisor": 5, "offset": 3, "special": [16, 17, 18]},
        ],
        sk2=[
            {"base": 160, "growth": 16, "divisor": 1, "offset": 0, "special": [308, 332, 360]},
            {"base": 240, "growth": 24, "divisor": 1, "offset": 0, "special": [462, 498, 540]},
        ],
        sk3=[
            {"base": 67, "growth": 53, "divisor": 8, "offset": 0, "special": [128, 138, 150]},
            {"base": 94, "growth": 28, "divisor": 3, "offset": 0, "special": [180, 194, 210]},
            {"base": 134, "growth": 40, "divisor": 3, "offset": 0, "special": [257, 277, 300]},
        ],
    )

    # ========== 伊冯 ==========
    add_character(
        name="伊冯",
        char_type="突击",
        star=6,
        primary="智识",
        secondary="敏捷",
        weapon="手铳",

        strength={"base": 8, "growth": 71, "divisor": 85, "offset": 28},
        agility={"base": 14, "growth": 65, "divisor": 51, "offset": 37},
        intellect={"base": 24, "growth": 135, "divisor": 79, "offset": 46},
        will={"base": 10, "growth": 17, "divisor": 16, "offset": 9},
        base_atk={"base": 30, "growth": 111, "divisor": 34, "offset": 16},

        sk1=[
            {"base": 111, "growth": 56, "divisor": 5, "offset": 0, "special": [214, 230, 250]},
            {"base": 67, "growth": 20, "divisor": 3, "offset": 0, "special": [128, 138, 150]},
            {"base": 89, "growth": 44, "divisor": 5, "offset": 3, "special": [171, 185, 200]},
        ],
        sk2=[
            {"base": 45, "growth": 22, "divisor": 5, "offset": 1, "special": [86, 93, 100]},
            {"base": 89, "growth": 53, "divisor": 6, "offset": 5, "special": [171, 185, 200]},
        ],
        sk3=[
            {"base": 8.9, "growth": 6.2, "divisor": 7, "offset": 0.6, "special": [17.2, 18.5, 20.0]},
            {"base": 133, "growth": 93, "divisor": 7, "offset": 5, "special": [256, 276, 300]},
            {"base": 267, "growth": 80, "divisor": 3, "offset": 1, "special": [514, 554, 600]},
        ],
    )




    print("所有角色已添加完成！")