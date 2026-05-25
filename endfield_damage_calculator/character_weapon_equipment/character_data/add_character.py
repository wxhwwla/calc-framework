#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用角色添加脚本

用法:
    python -m character_weapon_equipment.character_data.add_character  # 查看说明
    python scripts/seed_characters.py  # 批量录入角色配置
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from calculation.curve_baker import bake_character_curves
from data.loader import reload_characters


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
    sk1_dt: list | None = None,
    sk2_dt: list | None = None,
    sk3_dt: list | None = None,
    *,
    json_path: Path | None = None,
) -> dict:
    """添加新角色到 characters.json（不修改调用方传入的字典对象）。"""
    character: dict[str, Any] = {
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
        **bake_character_curves(
            strength=copy.deepcopy(strength),
            agility=copy.deepcopy(agility),
            intellect=copy.deepcopy(intellect),
            will=copy.deepcopy(will),
            base_atk=copy.deepcopy(base_atk),
            sk1=copy.deepcopy(sk1),
            sk2=copy.deepcopy(sk2),
            sk3=copy.deepcopy(sk3),
            sk1_dt=copy.deepcopy(sk1_dt) if sk1_dt else None,
            sk2_dt=copy.deepcopy(sk2_dt) if sk2_dt else None,
            sk3_dt=copy.deepcopy(sk3_dt) if sk3_dt else None,
        ),
    }

    if json_path is None:
        json_path = Path(__file__).parent / "characters.json"

    with open(json_path, "r", encoding="utf-8") as f:
        characters = json.load(f)

    if any(c["名称"] == name for c in characters):
        print(f"Warning: 角色「{name}」已存在，覆盖数据。")
        characters = [c for c in characters if c["名称"] != name]

    characters.append(character)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(characters, f, ensure_ascii=False, indent=2)

    reload_characters()

    print(f"OK: 角色「{name}」已添加！")
    print(f"   类型: {char_type}  星级: {star}星  武器: {weapon}")
    print(f"   主/副能力: {primary} / {secondary}")
    print(f"   基础攻击力: {character['基础攻击力'][0]} - {character['基础攻击力'][-1]}")
    print(f"   当前角色总数: {len(characters)}")
    return character


if __name__ == "__main__":
    print("角色录入库函数: add_character(...)")
    print("批量配置请运行: python scripts/seed_characters.py")
