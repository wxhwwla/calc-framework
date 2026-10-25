#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""武器有条件特殊能力字段：特殊能力1 / 特殊能力2（兼容旧 特殊能力）。"""

from __future__ import annotations

from typing import Any

from .name_utils import (
    _extract_effect_name_from_special_name,
    _split_special_name,
    bonus_attribute_keys,
    bonus_curve_for_key,
    weapon_special_field_keys,
)
from .slots_io import read_weapon_special_slots


def read_weapon_skills_schema(weapon: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """

    读取武器技能 schema（normal_skills / special_skills）。



    - 若已是新结构，按新结构归一化返回

    - 若是旧结构（xxx+ + 特殊能力1/2），动态映射为新结构视图

    """

    normal_raw = weapon.get("normal_skills")

    special_raw = weapon.get("special_skills")

    if isinstance(normal_raw, list) and isinstance(special_raw, list):
        normal_skills: list[dict[str, Any]] = []

        for idx, item in enumerate(normal_raw):
            if not isinstance(item, dict):
                continue

            curve = item.get("curve")

            normal_skills.append(
                {
                    "zone": int(item.get("zone", idx + 1)),
                    "effect": str(item.get("effect", "")),
                    "curve": [float(v) for v in curve] if isinstance(curve, list) else [],
                }
            )

        special_skills: list[dict[str, Any]] = []

        for item in special_raw:
            if not isinstance(item, dict):
                continue

            name = str(item.get("name", ""))

            effect = str(item.get("effect", "")) or _extract_effect_name_from_special_name(name)

            condition = str(item.get("condition", ""))

            curve = item.get("curve")

            special_skills.append(
                {
                    "zone": int(item.get("zone", 3)),
                    "name": name,
                    "condition": condition,
                    "effect": effect,
                    "curve": [float(v) for v in curve] if isinstance(curve, list) else [],
                    "max_stack": max(1, int(item.get("max_stack", 1))),
                }
            )

        return {"normal_skills": normal_skills, "special_skills": special_skills}

    normal_skills = []

    for idx, attr_key in enumerate(bonus_attribute_keys(weapon), start=1):
        normal_skills.append(
            {
                "zone": idx,
                "effect": attr_key,
                "curve": bonus_curve_for_key(weapon, attr_key),
            }
        )

    special_skills = []

    for enabled, name, curve, max_stack in read_weapon_special_slots(weapon):
        if not enabled or not name:
            continue

        condition, effect = _split_special_name(name)

        special_skills.append(
            {
                "zone": 3,
                "name": name,
                "condition": condition,
                "effect": effect,
                "curve": [float(v) for v in curve],
                "max_stack": max(1, int(max_stack)),
            }
        )

    return {"normal_skills": normal_skills, "special_skills": special_skills}


def write_weapon_skills_schema(
    weapon: dict[str, Any],
    *,
    normal_skills: list[dict[str, Any]],
    special_skills: list[dict[str, Any]],
) -> None:
    """

    写入新武器技能 schema，并清理旧 ``xxx+`` / ``特殊能力1/2`` 字段。

    """

    for key in bonus_attribute_keys(weapon):
        weapon.pop(key, None)

    for key in weapon_special_field_keys(weapon):
        weapon.pop(key, None)

    weapon.pop("normal_skills", None)

    weapon.pop("special_skills", None)

    weapon["normal_skills"] = [
        {
            "zone": int(item.get("zone", idx + 1)),
            "effect": str(item.get("effect", "")),
            "curve": [float(v) for v in (item.get("curve") if isinstance(item.get("curve"), list) else [])],
        }
        for idx, item in enumerate(normal_skills)
        if isinstance(item, dict) and str(item.get("effect", "")).strip()
    ]

    weapon["special_skills"] = [
        {
            "zone": int(item.get("zone", 3)),
            "name": str(item.get("name", "")),
            "condition": str(item.get("condition", "")),
            "effect": str(item.get("effect", "")),
            "curve": [float(v) for v in (item.get("curve") if isinstance(item.get("curve"), list) else [])],
            "max_stack": max(1, int(item.get("max_stack", 1))),
        }
        for item in special_skills
        if isinstance(item, dict) and str(item.get("name", "")).strip()
    ]


def migrate_weapon_record_to_skill_schema(weapon: dict[str, Any]) -> bool:
    """

    将单条武器记录迁移为 ``normal_skills`` / ``special_skills`` 结构。



    返回值：

    - ``True``: 记录被改写

    - ``False``: 记录已是新结构且无需改动

    """

    keys = list(weapon.keys())

    old_bonus_keys: list[str] = []

    try:
        start = keys.index("基础攻击力") + 1

    except ValueError:
        start = len(keys)

    for key in keys[start:]:
        if key in weapon_special_field_keys(weapon):
            break

        if key.endswith("+") and isinstance(weapon.get(key), list):
            old_bonus_keys.append(key)

    old_special_keys = [key for key in weapon_special_field_keys(weapon) if key in weapon]

    has_new_schema = isinstance(weapon.get("normal_skills"), list) and isinstance(weapon.get("special_skills"), list)

    needs_migration = bool(old_bonus_keys or old_special_keys or not has_new_schema)

    if not needs_migration:
        return False

    schema = read_weapon_skills_schema(weapon)

    write_weapon_skills_schema(
        weapon,
        normal_skills=schema["normal_skills"],
        special_skills=schema["special_skills"],
    )

    return True


def migrate_weapon_records_to_skill_schema(
    weapons: list[dict[str, Any]],
) -> list[str]:
    """批量迁移武器记录，返回发生变更的武器名称列表。"""

    changed_names: list[str] = []

    for weapon in weapons:
        if migrate_weapon_record_to_skill_schema(weapon):
            changed_names.append(str(weapon.get("名称", "")))

    return changed_names
