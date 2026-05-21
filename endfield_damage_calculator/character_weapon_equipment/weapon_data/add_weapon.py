#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用武器添加脚本

用法:
    python -m character_weapon_equipment.weapon_data.add_weapon  # 查看说明
    python scripts/seed_weapons.py  # 批量录入示例武器
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from calculation.formula import (
    calculate_growth_curve as calculate_weapon_attack,
    calculate_bonus_attribute,
)
from data.loader import reload_weapons

_GROWTH_KEYS = frozenset({"base", "growth", "divisor", "offset", "special"})


def _build_special_ability_curve(special_ability: dict[str, Any]) -> list:
    if "curve" in special_ability:
        return list(special_ability.get("curve", []))
    params = {k: v for k, v in special_ability.items() if k in _GROWTH_KEYS}
    return calculate_bonus_attribute(max_level=9, **params)


def add_weapon(
    name: str,
    weapon_type: str,
    star: int,
    base_atk: dict,
    bonus_attrs: dict | None = None,
    special_ability: dict | None = None,
    *,
    json_path: Path | None = None,
) -> dict:
    """
    添加新武器到 weapons.json（不修改调用方传入的字典对象）。
    """
    weapon: dict[str, Any] = {
        "名称": name,
        "类型": weapon_type,
        "星级": star,
        "等级": list(range(1, 91)),
        "潜能": list(range(0, 6)),
        "基础攻击力": calculate_weapon_attack(**dict(base_atk)),
    }

    if bonus_attrs:
        for attr_name, params in bonus_attrs.items():
            if not attr_name.endswith("+"):
                attr_name = attr_name + "+"
            p = copy.deepcopy(params)
            special = p.pop("special", None)
            weapon[attr_name] = calculate_bonus_attribute(special=special, **p)

    sa = copy.deepcopy(special_ability) if special_ability else None
    if sa and sa.get("enabled"):
        weapon["特殊能力"] = [
            True,
            sa.get("name", ""),
            _build_special_ability_curve(sa),
        ]
    else:
        weapon["特殊能力"] = [False]

    if json_path is None:
        json_path = Path(__file__).parent / "weapons.json"

    with open(json_path, "r", encoding="utf-8") as f:
        weapons = json.load(f)

    if any(w["名称"] == name for w in weapons):
        print(f"Warning: 武器「{name}」已存在，覆盖数据。")
        weapons = [w for w in weapons if w["名称"] != name]

    weapons.append(weapon)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(weapons, f, ensure_ascii=False, indent=2)

    reload_weapons()

    print(f"OK: 武器「{name}」已添加！")
    print(f"   类型: {weapon_type}  星级: {star}星")
    print(f"   基础攻击力: {weapon['基础攻击力'][0]} - {weapon['基础攻击力'][-1]}")
    if bonus_attrs:
        print(f"   附加属性: {', '.join(bonus_attrs.keys())}")
    if sa and sa.get("enabled"):
        print(f"   特殊能力: {sa.get('name')}")
    print(f"   当前武器总数: {len(weapons)}")
    return weapon


def remove_weapon(name: str, *, json_path: Path | None = None) -> bool:
    """
    从 weapons.json 按名称删除一把武器。

    返回：
        是否删除了条目（名称不存在时为 False）
    """
    if json_path is None:
        json_path = Path(__file__).parent / "weapons.json"

    with open(json_path, "r", encoding="utf-8") as f:
        weapons = json.load(f)

    before = len(weapons)
    weapons = [w for w in weapons if w.get("名称") != name]
    if len(weapons) == before:
        print(f"Warning: 武器「{name}」不存在，未修改 JSON。")
        return False

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(weapons, f, ensure_ascii=False, indent=2)

    reload_weapons()
    print(f"OK: 已删除武器「{name}」，当前武器总数: {len(weapons)}")
    return True


if __name__ == "__main__":
    print("武器录入: add_weapon(...)")
    print("武器删除: remove_weapon('名称')")
    print("批量示例请运行: python scripts/seed_weapons.py")
