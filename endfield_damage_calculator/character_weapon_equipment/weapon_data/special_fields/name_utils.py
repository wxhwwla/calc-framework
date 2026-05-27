#!/usr/bin/env python3
"""武器有条件特殊能力字段：特殊能力1 / 特殊能力2（兼容旧 特殊能力）。"""

from __future__ import annotations

import re
from typing import Any

from .codec import LEGACY_SPECIAL_KEY, SPECIAL_FIELD_KEYS

_EFFECT_NAME_RE = re.compile(r'([^\s，。；:：,\.()（）"“”\[\]【】]+?\+)')


def weapon_special_field_keys(weapon: dict[str, Any]) -> frozenset[str]:
    """武器 JSON 中所有特殊能力相关键（用于 bonus 键扫描边界）。"""
    keys = set(SPECIAL_FIELD_KEYS)
    if LEGACY_SPECIAL_KEY in weapon:
        keys.add(LEGACY_SPECIAL_KEY)
    return frozenset(keys)


def bonus_attribute_keys(weapon: dict[str, Any]) -> list[str]:
    """``基础攻击力`` 与特殊能力字段之间的 ``xxx+`` 附加属性键（保持 JSON 顺序）。"""
    normal_raw = weapon.get("normal_skills")
    if isinstance(normal_raw, list):
        out: list[str] = []
        for item in normal_raw:
            if not isinstance(item, dict):
                continue
            effect = str(item.get("effect", "")).strip()
            curve = item.get("curve")
            if effect and isinstance(curve, list):
                out.append(effect)
        return out

    keys = list(weapon.keys())
    try:
        start = keys.index("基础攻击力") + 1
    except ValueError:
        return []
    special = weapon_special_field_keys(weapon)
    out: list[str] = []
    for key in keys[start:]:
        if key in special:
            break
        if key.endswith("+") and isinstance(weapon.get(key), list):
            out.append(key)
    return out


def bonus_curve_for_key(weapon: dict[str, Any], attr_key: str) -> list[float]:
    """读取附加属性 ``xxx+`` 的层数曲线。"""
    normal_raw = weapon.get("normal_skills")
    if isinstance(normal_raw, list):
        for item in normal_raw:
            if not isinstance(item, dict):
                continue
            if str(item.get("effect", "")).strip() != attr_key:
                continue
            curve = item.get("curve")
            if isinstance(curve, list):
                return [float(v) for v in curve]
        return []

    raw = weapon.get(attr_key)
    if not isinstance(raw, list):
        return []
    return [float(v) for v in raw]


def _extract_effect_name_from_special_name(raw_name: str) -> str:
    """从特殊技能完整名称中提取 ``xxx+`` 词条名。"""
    name = (raw_name or "").strip()
    if not name:
        return ""
    if name.endswith("+") and all(ch not in name for ch in ("，", "。")):
        return name
    matches = _EFFECT_NAME_RE.findall(name)
    if matches:
        return matches[-1]
    return name


def _split_special_name(raw_name: str) -> tuple[str, str]:
    """拆分特殊技能名称为 (condition, effect)。"""
    name = (raw_name or "").strip()
    effect = _extract_effect_name_from_special_name(name)
    if not name or not effect:
        return "", effect
    if name == effect or effect not in name:
        return "", effect
    condition = name[: name.rfind(effect)].strip("，。；:：, ")
    for marker in ("时获得", "获得", "提高", "提升", "增加", "降低", "使得", "使"):
        if condition.endswith(marker):
            condition = condition[: -len(marker)].strip("，。；:：, ")
            break
    return condition, effect


def _special_name_matches(pick_name: str, special_name: str, special_effect: str = "") -> bool:
    """特殊技能名称匹配：支持完整名称与词条名互认。"""
    pick = (pick_name or "").strip()
    name = (special_name or "").strip()
    effect = (special_effect or "").strip() or _extract_effect_name_from_special_name(name)
    return bool(pick and (pick in (name, effect)))
