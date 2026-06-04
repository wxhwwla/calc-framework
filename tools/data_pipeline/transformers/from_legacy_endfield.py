#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""终末地旧 JSON 格式 → 标准 EntitySchema 迁移器。



处理现有的 ``characters.json`` 和 ``weapons.json`` 中的旧格式，

自动推断技能结构、段、倍率。

"""

from __future__ import annotations


from typing import Any, Dict, List


from ..schema import EntitySchema, SegmentSchema


CHARACTER_SKILL_MAP: List[Dict[str, Any]] = [
    {"name": "战技", "multiplier_field": "战技倍率", "type_field": "战技段伤害类型"},
    {"name": "连携技", "multiplier_field": "连携技倍率", "type_field": "连携技段伤害类型"},
    {"name": "终结技", "multiplier_field": "终结技倍率", "type_field": "终结技段伤害类型"},
]


def from_characters(raw_list: List[Dict[str, Any]]) -> List[EntitySchema]:
    """from_characters 实现。

    Args:
        raw_list: 参数描述。

    Returns:
        返回值描述。
    """
    return [_migrate_character(r) for r in raw_list]


def from_weapons(raw_list: List[Dict[str, Any]]) -> List[EntitySchema]:
    """from_weapons 实现。

    Args:
        raw_list: 参数描述。

    Returns:
        返回值描述。
    """
    return [_migrate_weapon(r) for r in raw_list]


# ── 角色迁移 ──


def _migrate_character(raw: Dict[str, Any]) -> EntitySchema:
    """_migrate_character 实现。"""
    entity: EntitySchema = {
        "名称": str(raw.get("名称", "")),
        "技能": [],
        "_entity_type": "character",
    }

    _migrate_character_skills(raw, entity)

    _passthrough(raw, entity, exclude_prefixes=("战技", "连携技", "终结技"))

    return entity


def _migrate_character_skills(raw: Dict[str, Any], entity: EntitySchema) -> None:
    """_migrate_character_skills 实现。"""
    for skill_def in CHARACTER_SKILL_MAP:
        skill_name = skill_def["name"]

        mf = skill_def["multiplier_field"]

        tf = skill_def["type_field"]

        segments = _extract_character_segments(raw, mf, tf)

        if segments:
            entity["技能"].append(
                {
                    "名称": skill_name,
                    "标签": "主动",
                    "百分比": True,
                    "段": segments,
                }
            )


def _extract_character_segments(raw: Dict[str, Any], mf: str, tf: str) -> List[SegmentSchema]:
    """_extract_character_segments 实现。"""
    raw_types = raw.get(tf)

    segments: List[SegmentSchema] = []

    # 方案 A：尝试带编号的字段（战技倍率1, 战技倍率2, ...）

    seg_index = 1

    while True:
        field = f"{mf}{seg_index}"

        rate_list = raw.get(field)

        if rate_list is None:
            alt_field = f"{mf}_{seg_index}"

            rate_list = raw.get(alt_field)

        if rate_list is None:
            break

        if not isinstance(rate_list, list) or not rate_list:
            break

        seg = _make_segment(rate_list, raw_types, seg_index)

        segments.append(seg)

        seg_index += 1

    if segments:
        return segments

    # 方案 B：尝试无编号字段（战技倍率），值为 [[seg1_levels], [seg2_levels], ...]

    main_field = raw.get(mf)

    if isinstance(main_field, list) and main_field:
        # 检查是否嵌套列表（多段）

        if main_field and isinstance(main_field[0], list):
            for si, inner in enumerate(main_field, start=1):
                if isinstance(inner, list) and inner:
                    seg = _make_segment(inner, raw_types, si)

                    segments.append(seg)

        else:
            # 单段扁平列表

            seg = _make_segment(main_field, raw_types, 1)

            segments.append(seg)

    return segments


def _make_segment(rate_list: List[Any], raw_types: Any, seg_index: int) -> SegmentSchema:
    """_make_segment 实现。"""
    seg: SegmentSchema = {"倍率": _convert_rates(rate_list)}

    dt = _read_damage_type(raw_types, seg_index)

    if dt:
        seg["伤害类型"] = dt

    return seg


def _read_damage_type(type_field_value: Any, index: int) -> str | None:
    """_read_damage_type 实现。"""
    if not isinstance(type_field_value, list):
        return None

    idx = index - 1

    if 0 <= idx < len(type_field_value):
        raw = type_field_value[idx]

        if raw is not None and str(raw).strip():
            return str(raw).strip()

    return None


def _convert_rates(raw_list: List[Any]) -> List[int]:
    """_convert_rates 实现。"""
    result: List[int] = []

    for v in raw_list:
        if v is None:
            continue

        try:
            fv = float(v)

            if fv == int(fv) and fv < 100:
                result.append(int(fv))

            elif fv < 100:
                result.append(round(fv * 100))

            else:
                result.append(round(fv))

        except (ValueError, TypeError):
            pass

    return result


# ── 武器迁移 ──


def _migrate_weapon(raw: Dict[str, Any]) -> EntitySchema:
    """_migrate_weapon 实现。"""
    entity: EntitySchema = {
        "名称": str(raw.get("名称", "")),
        "技能": [],
        "_entity_type": "weapon",
    }

    _migrate_weapon_skills(raw, entity)

    _passthrough(raw, entity, exclude_keys={"normal_skills", "special_skills", "special"})

    return entity


def _migrate_weapon_skills(raw: Dict[str, Any], entity: EntitySchema) -> None:
    """_migrate_weapon_skills 实现。"""
    normal_skills = _read_weapon_skills(raw, "normal_skills")

    special_skills = _read_weapon_skills(raw, "special_skills")

    for sk in normal_skills:
        effect = sk.get("effect", "")

        curve = sk.get("curve", [])

        if not effect or not isinstance(curve, list):
            continue

        entity["技能"].append(
            {
                "名称": str(effect),
                "标签": "被动",
                "百分比": _infer_passive_is_percent(str(effect)),
                "段": [{"倍率": _convert_passive_rates(curve, str(effect))}],
            }
        )

    for sk in special_skills:
        effect = sk.get("effect", "")

        curve = sk.get("curve", [])

        if not effect or not isinstance(curve, list):
            continue

        entity["技能"].append(
            {
                "名称": str(effect),
                "标签": "被动",
                "百分比": False,
                "段": [{"倍率": _convert_passive_rates(curve, str(effect))}],
            }
        )


def _read_weapon_skills(raw: Dict[str, Any], key: str) -> List[Dict[str, Any]]:
    """读取武器技能列表，兼容新旧两种 schema。"""

    skills = raw.get(key, [])

    if isinstance(skills, list):
        return skills

    return raw.get("特殊技能" if key == "special_skills" else "普通技能", [])


_PERCENT_PASSIVE_EXACT = frozenset(
    {
        "攻击力+",
        "主能力+",
        "副能力+",
        "全能力+",
        "物理伤害+",
        "法术伤害+",
        "战技伤害加成",
        "连携技伤害加成",
        "终结技伤害加成",
        "所有技能伤害",
        "暴击+",
        "暴击伤害+",
        "充能效率",
    }
)


def _infer_passive_is_percent(effect: str) -> bool:
    """_infer_passive_is_percent 实现。"""
    return effect.strip() in _PERCENT_PASSIVE_EXACT


def _convert_passive_rates(curve: List[Any], effect: str) -> List[int]:
    """_convert_passive_rates 实现。"""
    is_pct = _infer_passive_is_percent(effect)

    result: List[int] = []

    for v in curve:
        if v is None:
            continue

        try:
            fv = float(v)

            if is_pct and fv < 1.0:
                result.append(round(fv * 100))

            else:
                result.append(round(fv))

        except (ValueError, TypeError):
            pass

    return result


# ── 透传 ──


def _passthrough(
    raw: Dict[str, Any],
    entity: EntitySchema,
    *,
    exclude_prefixes: tuple | None = None,
    exclude_keys: set | None = None,
) -> None:
    """_passthrough 实现。"""
    for key, value in raw.items():
        if key in entity:
            continue

        if exclude_prefixes and any(key.startswith(p) for p in exclude_prefixes):
            continue

        if exclude_keys and key in exclude_keys:
            continue

        entity[key] = value
