#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""

通用武器添加脚本



使用方法：

    直接运行脚本，按照提示输入武器参数，或者在代码中配置参数。

"""

import json

import sys

from pathlib import Path


# 添加项目根目录到路径，确保模块导入正确

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


from games.endfield.calc.damage.formula import calculate_bonus_attribute

from games.endfield.calc.damage.formula import (  # pyright: ignore[reportMissingImports]
    calculate_growth_curve as calculate_weapon_attack,
)


def add_weapon(
    name: str,
    weapon_type: str,
    star: int,
    base_atk: dict,  # {"base": int, "growth": int, "divisor": int, "offset": int}
    bonus_attrs: dict
    | None = None,  # {"属性名+": {"base": int, "growth": int, "divisor": int, "offset": int, "special": list}}
    special_ability: dict
    | None = None,  # {"enabled": bool, "name": str, "curve": list} or {"enabled": bool, "name": str, "base": int/float, "growth": int/float, "divisor": int/float, "offset": int/float, "special": list}
    json_path: Path | None = None,
):
    """

    添加新武器到 weapons.json



    参数：

        name: 武器名称

        weapon_type: 武器类型（如"单手剑", "双手剑", "施术单元", "长柄武器", "手铳"）

        star: 星级（3-6）

        base_atk: 基础攻击力成长参数

        bonus_attrs: 附加属性成长参数（字典，键为属性名+，如"敏捷+", "攻击力+"等）

        special_ability: 特殊能力配置（可选）

                        {"enabled": True/False, "name": "属性名+", "curve": [等级1值, 等级2值, ...]}

                        或 {"enabled": True/False, "name": "属性名+", "base": int/float, "growth": int/float, "divisor": int/float, "offset": int/float, "special": list}

    """

    # 构建武器数据

    weapon = {
        "名称": name,
        "类型": weapon_type,
        "星级": star,
        "等级": list(range(1, 91)),
        "潜能": list(range(0, 6)),
        "基础攻击力": calculate_weapon_attack(**base_atk),
    }

    # 添加附加属性

    if bonus_attrs:
        for attr_name, params in bonus_attrs.items():
            if not attr_name.endswith("+"):
                attr_name = attr_name + "+"

            # 提取 special 字段（如果存在）

            special = params.get("special")

            other_params = {k: v for k, v in params.items() if k != "special"}

            weapon[attr_name] = calculate_bonus_attribute(special=special, **other_params)

    # 添加特殊能力

    if special_ability and special_ability.get("enabled"):
        # 支持两种格式：

        # 1. 旧格式：{"curve": [值列表]}

        # 2. 新格式：{"base": int/float, "growth": int/float, "divisor": int/float, "offset": int/float, "special": list}

        if "curve" in special_ability:
            # 旧格式：直接使用 curve 列表

            curve = special_ability.get("curve", [])

        else:
            # 新格式：使用公式计算曲线

            params = {
                k: v for k, v in special_ability.items() if k in ["base", "growth", "divisor", "offset", "special"]
            }

            curve = calculate_bonus_attribute(max_level=9, **params)

        weapon["特殊能力"] = [True, special_ability.get("name", ""), curve]

    else:
        weapon["特殊能力"] = [False]

    # 读取现有数据

    _json_path = (
        json_path
        if json_path is not None
        else Path(__file__).resolve().parent.parent.parent / "games" / "endfield" / "data" / "weapons.json"
    )

    with open(_json_path, encoding="utf-8") as f:
        weapons = json.load(f)

    # 检查是否已存在

    existing = [w for w in weapons if w["名称"] == name]

    if existing:
        print(f"Warning: 武器「{name}」已存在，覆盖数据。")

        weapons = [w for w in weapons if w["名称"] != name]

    # 添加新武器

    weapons.append(weapon)

    # 保存

    with open(_json_path, "w", encoding="utf-8") as f:
        json.dump(weapons, f, ensure_ascii=False, indent=2)

    print(f"OK: 武器「{name}」已添加！")

    print(f"   类型: {weapon_type}  星级: {star}星")

    print(f"   基础攻击力: {weapon['基础攻击力'][0]} - {weapon['基础攻击力'][-1]}")

    if bonus_attrs:
        print(f"   附加属性: {', '.join(bonus_attrs.keys())}")

    if special_ability and special_ability.get("enabled"):
        print(f"   特殊能力: {special_ability.get('name')}")

    print(f"   当前武器总数: {len(weapons)}")


def remove_weapon(name: str, json_path: Path | None = None) -> bool:
    """按名称从 weapons.json 删除武器条目，返回是否成功删除。"""

    _json_path = (
        json_path
        if json_path is not None
        else Path(__file__).resolve().parent.parent.parent / "games" / "endfield" / "data" / "weapons.json"
    )

    with open(_json_path, encoding="utf-8") as f:
        weapons = json.load(f)

    new_weapons = [w for w in weapons if w.get("名称") != name]

    if len(new_weapons) == len(weapons):
        return False

    with open(_json_path, "w", encoding="utf-8") as f:
        json.dump(new_weapons, f, ensure_ascii=False, indent=2)

    return True


if __name__ == "__main__":
    print("=" * 60)

    print("通用武器添加工具")

    print("=" * 60)

    # =============== 在这里配置你的新武器参数 ===============

    # 示例：添加一把新武器

    add_weapon(
        name="荧光雷羽",
        weapon_type="施术单元",
        star=4,
        # 基础攻击力成长参数（公式：base + floor((growth * (lv-1) + offset) / divisor)）
        base_atk={"base": 34, "growth": 62, "divisor": 18, "offset": 16},
        # 附加属性（潜能1-9级）
        # 格式：{"base": int, "growth": int, "divisor": int, "offset": int, "special": list}
        # special字段可选：前8级用公式计算，第9级使用special[0]（如果提供）
        bonus_attrs={
            "意志+": {"base": 12, "growth": 48, "divisor": 5, "offset": 0, "special": [93]},
            "攻击力+": {"base": 3, "growth": 12, "divisor": 5, "offset": 0, "special": [23.4]},
        },
        # 特殊能力（可选）- 无特殊能力时可以不写或设为 None
        # 新格式：使用公式参数，与 bonus_attrs 格式一致
        special_ability={
            "enabled": True,
            "name": "攻击力+",
            "base": 12,
            "growth": 4.8,
            "divisor": 2,
            "offset": 0,
            "special": [33.6],
        },
    )

    add_weapon(
        name="全自动骇新星",
        weapon_type="施术单元",
        star=4,
        # 基础攻击力成长参数（公式：base + floor((growth * (lv-1) + offset) / divisor)）
        base_atk={"base": 34, "growth": 62, "divisor": 18, "offset": 16},
        # 附加属性（潜能1-9级）
        # 格式：{"base": int, "growth": int, "divisor": int, "offset": int, "special": list}
        # special字段可选：前8级用公式计算，第9级使用special[0]（如果提供）
        bonus_attrs={
            "智识+": {"base": 12, "growth": 96, "divisor": 10, "offset": 0, "special": [93]},
            "法术伤害+": {"base": 3.3, "growth": 16, "divisor": 6, "offset": 0.4, "special": [26.0]},
        },
        # 特殊能力（可选）- 无特殊能力时可以不写或设为 None
        # 新格式：使用公式参数，与 bonus_attrs 格式一致
        special_ability={
            "enabled": True,
            "name": "攻击力+",
            "base": 15,
            "growth": 6,
            "divisor": 2,
            "offset": 0,
            "special": [45.0],
        },
    )

    add_weapon(
        name="淬火者",
        weapon_type="双手剑",
        star=4,
        # 基础攻击力成长参数（公式：base + floor((growth * (lv-1) + offset) / divisor)）
        base_atk={"base": 34, "growth": 62, "divisor": 18, "offset": 16},
        # 附加属性（潜能1-9级）
        # 格式：{"base": int, "growth": int, "divisor": int, "offset": int, "special": list}
        # special字段可选：前8级用公式计算，第9级使用special[0]（如果提供）
        bonus_attrs={
            "意志+": {"base": 12, "growth": 96, "divisor": 10, "offset": 0, "special": [93]},
            "最大生命值+": {"base": 6, "growth": 9.6, "divisor": 2, "offset": 0, "special": [46.8]},
        },
        # 特殊能力（可选）- 无特殊能力时可以不写或设为 None
        # 新格式：使用公式参数，与 bonus_attrs 格式一致
        special_ability={
            "enabled": True,
            "name": "攻击力+",
            "base": 12,
            "growth": 4.8,
            "divisor": 2,
            "offset": 0,
            "special": [33.6],
        },
    )

    add_weapon(
        name="工业零点一",
        weapon_type="双手剑",
        star=4,
        # 基础攻击力成长参数（公式：base + floor((growth * (lv-1) + offset) / divisor)）
        base_atk={"base": 34, "growth": 62, "divisor": 18, "offset": 16},
        # 附加属性（潜能1-9级）
        # 格式：{"base": int, "growth": int, "divisor": int, "offset": int, "special": list}
        # special字段可选：前8级用公式计算，第9级使用special[0]（如果提供）
        bonus_attrs={
            "力量+": {"base": 12, "growth": 96, "divisor": 10, "offset": 0, "special": [93]},
            "攻击力+": {"base": 6, "growth": 9.6, "divisor": 2, "offset": 0, "special": [46.8]},
        },
        # 特殊能力（可选）- 无特殊能力时可以不写或设为 None
        # 新格式：使用公式参数，与 bonus_attrs 格式一致
        special_ability={
            "enabled": True,
            "name": "攻击力+",
            "base": 12,
            "growth": 4.8,
            "divisor": 2,
            "offset": 0,
            "special": [33.6],
        },
    )

    # ======================================================
