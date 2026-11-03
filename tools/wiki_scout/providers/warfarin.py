# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""华法琳 Wiki（warfarin.wiki）provider — 明日方舟：终末地。

数据来自公开 JSON API（`https://api.warfarin.wiki/v1/cn/...`）：
- `/operators` + `/operators/{slug}`：干员档案、1–90 级属性、技能倍率。
- `/weapons` + `/weapons/{slug}`：武器基础攻击力曲线、技能成长。
- `/gear`：装备面板（列表接口已包含属性词条，无需逐件抓详情）。

属性 `attrType` 对照（已用陈千语 90 级数据验证）：
39 力量 / 40 敏捷 / 41 智识 / 42 意志 / 2 基础攻击力 / 3 基础防御力。
"""

from __future__ import annotations

import math
import re
from collections import defaultdict
from typing import Any

from ..fetcher import Fetcher, FetchError
from ..registry import register_provider
from .base import BaseProvider

_API = "https://api.warfarin.wiki/v1/cn"
_SOURCE = "https://warfarin.wiki"
_GAME = "明日方舟：终末地"

_ATTR_NAMES = {
    39: "力量",
    40: "敏捷",
    41: "智识",
    42: "意志",
    2: "基础攻击力",
    3: "基础防御力",
}

# (组起始索引, 组起始等级)，用于把 103 行属性表映射为 1–90 级。
_ATTR_GROUPS = ((0, 1), (20, 20), (41, 40), (62, 60), (83, 80))
_MAX_LEVEL = 90

_WEAPON_TYPES = {
    1: "单手剑",
    2: "施术单元",
    3: "双手剑",
    5: "长柄武器",
    6: "手铳",
}

_PART_TYPES = {0: "护甲", 1: "护手", 2: "配件"}

_DAMAGE_TYPES = {
    "Physical": "物理",
    "Fire": "火",
    "Ice": "冰",
    "Electric": "雷",
    "Nature": "自然",
    "Ether": "以太",
}

_PACK_ATTR_NAMES = {
    "Str": "力量",
    "Agi": "敏捷",
    "Wisd": "智识",
    "Will": "意志",
    "MaxHp": "生命值",
    "Atk": "攻击力",
    "Def": "防御力",
}

_SKILL_KEYS = (
    ("normal_skill", "战技"),
    ("combo_skill", "连携技"),
    ("ultimate_skill", "终结技"),
)


@register_provider
class WarfarinProvider(BaseProvider):
    """华法琳 Wiki 数据源。"""

    name = "warfarin"
    description = "华法琳 Wiki — 明日方舟：终末地（干员/武器/装备）"

    def fetch(
        self,
        fetcher: Fetcher,
        *,
        limit: int | None = None,
        refresh: bool = False,
    ) -> dict[str, Any]:
        operators = _as_list(fetcher.get_json(f"{_API}/operators", refresh=refresh))[:limit]
        weapons = _as_list(fetcher.get_json(f"{_API}/weapons", refresh=refresh))[:limit]
        gear = _as_list(fetcher.get_json(f"{_API}/gear", refresh=refresh))[:limit]

        operator_details: dict[str, Any] = {}
        errors: dict[str, str] = {}
        for item in operators:
            slug = item.get("slug")
            if not slug:
                continue
            try:
                payload = fetcher.get_json(f"{_API}/operators/{slug}", refresh=refresh)
            except (FetchError, ValueError) as exc:
                errors[f"operators/{slug}"] = str(exc)
                continue
            operator_details[slug] = payload.get("data", payload)

        weapon_details: dict[str, Any] = {}
        for item in weapons:
            slug = item.get("slug")
            if not slug:
                continue
            try:
                payload = fetcher.get_json(f"{_API}/weapons/{slug}", refresh=refresh)
            except (FetchError, ValueError) as exc:
                errors[f"weapons/{slug}"] = str(exc)
                continue
            weapon_details[slug] = payload.get("data", payload)

        return {
            "operators": operators,
            "operator_details": operator_details,
            "weapons": weapons,
            "weapon_details": weapon_details,
            "gear": gear,
            "errors": errors,
        }

    def parse(self, raw: dict[str, Any]) -> dict[str, Any]:
        operators: list[dict[str, Any]] = []
        details = raw.get("operator_details", {})
        for item in raw.get("operators", []):
            detail = details.get(item.get("slug"))
            if detail is not None:
                operators.append(_parse_operator(item, detail))

        weapons: list[dict[str, Any]] = []
        weapon_details = raw.get("weapon_details", {})
        for item in raw.get("weapons", []):
            detail = weapon_details.get(item.get("slug"))
            if detail is not None:
                weapons.append(_parse_weapon(item, detail))

        gear = [_parse_gear(item) for item in raw.get("gear", [])]

        result: dict[str, Any] = {
            "游戏": _GAME,
            "来源": _SOURCE,
            "干员": operators,
            "武器": weapons,
            "装备": gear,
        }
        if raw.get("errors"):
            result["抓取失败"] = raw["errors"]
        return result


def _as_list(payload: Any) -> list[dict[str, Any]]:
    """展开列表接口的响应。

    真实接口形如 `{"meta": {...}, "data": [...], "refs": {...}}`，
    测试夹具则直接是数组；两种形态都接受。
    """
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        data = payload.get("data")
        if isinstance(data, list):
            return data
        return [value for value in payload.values() if isinstance(value, dict)]
    return []


def _level_curve(values: list[Any]) -> list[float]:
    """把属性原始行映射为 1–90 级，取整（显示值 = floor(raw)）。"""
    curve: list[float] = []
    for level in range(1, _MAX_LEVEL + 1):
        start_idx, start_lvl = max(
            (group for group in _ATTR_GROUPS if group[1] <= level),
            key=lambda group: group[1],
        )
        idx = start_idx + (level - start_lvl)
        if idx >= len(values):
            break
        curve.append(float(math.floor(float(values[idx]))))
    return curve


def _stat_curves(character_table: dict[str, Any]) -> dict[str, list[float]]:
    by_type: dict[int, list[Any]] = defaultdict(list)
    for row in character_table.get("attributes", []):
        for attr in (row.get("Attribute") or {}).get("attrs", []):
            by_type[int(attr["attrType"])].append(attr.get("attrValue"))
    return {name: _level_curve(by_type[code]) for code, name in _ATTR_NAMES.items()}


def _find_skill(skill_table: dict[str, Any], suffix: str) -> dict[str, Any] | None:
    for key, value in skill_table.items():
        if key.endswith(suffix):
            return value
    return None


def _skill_segment_curves(skill: dict[str, Any]) -> list[list[float]]:
    levels = sorted(
        skill.get("SkillPatchDataBundle", []),
        key=lambda entry: entry.get("level", 0),
    )
    if not levels:
        return []

    first_board = {b["key"]: b.get("value") for b in levels[0].get("blackboard", [])}
    keys = [key for key in first_board if re.fullmatch(r"atk_scale\d*", key)]
    if not keys:
        return []
    keys.sort(key=lambda key: int(key[len("atk_scale") :] or 0))

    segments: list[list[float]] = []
    for key in keys:
        curve = []
        for entry in levels:
            board = {b["key"]: b.get("value") for b in entry.get("blackboard", [])}
            curve.append(round(float(board.get(key, 0)) * 100, 1))
        segments.append(curve)
    return segments


def _parse_operator(item: dict[str, Any], detail: dict[str, Any]) -> dict[str, Any]:
    table = detail.get("characterTable") or {}
    skill_table = detail.get("skillPatchTable") or {}
    damage_type = _DAMAGE_TYPES.get(
        str(table.get("charTypeId") or item.get("charTypeId") or ""),
        str(table.get("charTypeId") or item.get("charTypeId") or ""),
    )

    operator: dict[str, Any] = {
        "slug": item.get("slug"),
        "id": item.get("id"),
        "名称": item.get("name") or table.get("name"),
        "英文名": table.get("engName") or "",
        "星级": item.get("rarity", table.get("rarity")),
        "类型": item.get("profession") or "",
        "武器类型": _WEAPON_TYPES.get(
            int(table.get("weaponType") or item.get("weaponType") or 0),
            f"类型{table.get('weaponType') or item.get('weaponType')}",
        ),
        "主能力": _ATTR_NAMES.get(int(table.get("mainAttrType") or 0), ""),
        "副能力": _ATTR_NAMES.get(int(table.get("subAttrType") or 0), ""),
        "等级": list(range(1, _MAX_LEVEL + 1)),
    }
    operator.update(_stat_curves(table))

    for suffix, label in _SKILL_KEYS:
        skill = _find_skill(skill_table, suffix)
        curves = _skill_segment_curves(skill) if skill else []
        operator[f"{label}倍率"] = curves
        operator[f"{label}段伤害类型"] = [damage_type] * len(curves)

    return operator


def _parse_skill(skill_id: str, skill: dict[str, Any]) -> dict[str, Any]:
    levels = sorted(
        skill.get("SkillPatchDataBundle", []),
        key=lambda entry: entry.get("level", 0),
    )
    growth = [{b["key"]: b.get("value") for b in entry.get("blackboard", [])} for entry in levels]
    first = levels[0] if levels else {}
    return {
        "id": skill_id,
        "名称": first.get("skillName") or skill_id,
        "描述": first.get("description") or "",
        "成长": growth,
    }


def _parse_weapon(item: dict[str, Any], detail: dict[str, Any]) -> dict[str, Any]:
    basic = detail.get("weaponBasicTable") or {}
    item_table = detail.get("itemTable") or {}
    upgrade_table = detail.get("weaponUpgradeTemplateTable") or {}
    curve_rows = sorted(
        upgrade_table.get("list", []),
        key=lambda row: row.get("weaponLv", 0),
    )
    skills = [_parse_skill(skill_id, skill) for skill_id, skill in (detail.get("skillPatchTable") or {}).items()]
    normal = [skill for skill in skills if skill["id"].startswith(("wpn_attr_", "wpn_sp_"))]
    special = [skill for skill in skills if skill not in normal]

    weapon_type = basic.get("weaponType") or item.get("weaponType")
    return {
        "id": item.get("id"),
        "slug": item.get("slug"),
        "名称": item_table.get("name") or item.get("name"),
        "星级": basic.get("rarity", item.get("rarity")),
        "武器类型": _WEAPON_TYPES.get(int(weapon_type or 0), f"类型{weapon_type}"),
        "最大等级": basic.get("maxLv"),
        "基础攻击力曲线": [float(row.get("baseAtk", 0)) for row in curve_rows],
        "普通技能": normal,
        "特殊技能": special,
    }


def _modifier(raw: dict[str, Any]) -> dict[str, Any]:
    attr_type = int(raw.get("attrType") or 0)
    pack_attr = str(raw.get("packAttrType") or "")
    return {
        "attrType": attr_type,
        "属性类型": _PACK_ATTR_NAMES.get(pack_attr) or _ATTR_NAMES.get(attr_type) or pack_attr,
        "数值": raw.get("attrValue"),
        "强化值": raw.get("enhancedAttrValues") or [],
    }


def _parse_gear(item: dict[str, Any]) -> dict[str, Any]:
    base = item.get("displayBaseAttrModifier")
    return {
        "id": item.get("id"),
        "slug": item.get("slug"),
        "名称": item.get("name"),
        "稀有度": item.get("rarity"),
        "部位": _PART_TYPES.get(int(item.get("partType") or 0), f"部位{item.get('partType')}"),
        "最低穿戴等级": item.get("minWearLv"),
        "套装ID": item.get("suitID") or None,
        "基础属性": _modifier(base) if base else None,
        "属性词条": [_modifier(raw) for raw in item.get("displayAttrModifiers", [])],
    }
