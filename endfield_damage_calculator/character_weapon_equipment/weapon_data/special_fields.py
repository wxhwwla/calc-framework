#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""武器有条件特殊能力字段：特殊能力1 / 特殊能力2（兼容旧 特殊能力）。"""

from __future__ import annotations

from typing import Any

SPECIAL_FIELD_KEYS: tuple[str, ...] = ("特殊能力1", "特殊能力2")
LEGACY_SPECIAL_KEY = "特殊能力"


def parse_special_field(field: Any) -> tuple[bool, str, list[float]]:
    """解析单条特殊能力字段 → (启用, 名称, 曲线)。"""
    if field is False or field == [False]:
        return False, "", []
    if not isinstance(field, list) or len(field) < 3 or field[0] is not True:
        return False, "", []
    name = field[1] if isinstance(field[1], str) else ""
    curve = field[2] if isinstance(field[2], list) else []
    return True, name, [float(v) for v in curve]


def build_special_field(*, enabled: bool, name: str = "", curve: list[float] | None = None) -> list:
    """构造 JSON 特殊能力字段。"""
    if not enabled:
        return [False]
    return [True, name, list(curve or [])]


def read_weapon_special_slots(weapon: dict[str, Any]) -> list[tuple[bool, str, list[float]]]:
    """
    读取武器两条有条件特殊能力。

    若仅有旧字段 ``特殊能力``，视为 ``特殊能力1``。
    """
    slots: list[tuple[bool, str, list[float]]] = []
    for key in SPECIAL_FIELD_KEYS:
        if key in weapon:
            slots.append(parse_special_field(weapon.get(key)))
        else:
            slots.append((False, "", []))
    if not weapon.get(SPECIAL_FIELD_KEYS[0]) and LEGACY_SPECIAL_KEY in weapon:
        slots[0] = parse_special_field(weapon.get(LEGACY_SPECIAL_KEY))
    return slots


def write_weapon_special_slots(
    weapon: dict[str, Any],
    slots: list[tuple[bool, str, list[float]]],
) -> None:
    """写入 ``特殊能力1`` / ``特殊能力2``，并移除旧 ``特殊能力`` 键。"""
    for idx, key in enumerate(SPECIAL_FIELD_KEYS):
        enabled, name, curve = (False, "", [])
        if idx < len(slots):
            enabled, name, curve = slots[idx]
        weapon[key] = build_special_field(enabled=enabled, name=name, curve=curve)
    weapon.pop(LEGACY_SPECIAL_KEY, None)


def weapon_special_field_keys(weapon: dict[str, Any]) -> frozenset[str]:
    """武器 JSON 中所有特殊能力相关键（用于 bonus 键扫描边界）。"""
    keys = set(SPECIAL_FIELD_KEYS)
    if LEGACY_SPECIAL_KEY in weapon:
        keys.add(LEGACY_SPECIAL_KEY)
    return frozenset(keys)


def bonus_attribute_keys(weapon: dict[str, Any]) -> list[str]:
    """``基础攻击力`` 与特殊能力字段之间的 ``xxx+`` 附加属性键（保持 JSON 顺序）。"""
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


def apply_conditional_special_to_stats(
    weapon: dict[str, Any],
    *,
    ws_name: str,
    ws_level: int,
    ws2_name: str = "",
    ws2_level: int = 0,
    main_attr: str,
    sub_attr: str,
) -> tuple[float, float]:
    """
    按 GUI 选用档位，将特殊能力1/2 的数值计入主/副能力加成。

    返回 (main_bonus_delta, sub_bonus_delta)。
    """
    main_delta = 0.0
    sub_delta = 0.0
    picks = ((ws_name, ws_level), (ws2_name, ws2_level))
    for slot_idx, (pick_name, pick_level) in enumerate(picks):
        if pick_level <= 0 or not pick_name:
            continue
        enabled, sa_name, curve = read_weapon_special_slots(weapon)[slot_idx]
        if not enabled or sa_name != pick_name or not curve:
            continue
        idx = pick_level - 1
        if not (0 <= idx < len(curve)):
            continue
        value = float(curve[idx])
        if sa_name in (f"{main_attr}+", "主能力+"):
            main_delta += value
        elif sa_name in (f"{sub_attr}+", "副能力+"):
            sub_delta += value
        # 百分比类（法术伤害+、物理伤害+ 等）由乘区其它路径处理；此处仅主/副能力直加
    return main_delta, sub_delta


def add_special_picks_to_main_sub_bonus(
    weapon: dict[str, Any],
    *,
    ws_name: str,
    ws_level: int,
    ws2_name: str = "",
    ws2_level: int = 0,
    main_attr: str,
    sub_attr: str,
) -> tuple[float, float]:
    """将已启用的特殊能力1/2 档位加成累加到主/副能力（与旧 ``特殊能力`` 逻辑一致）。"""
    main_delta = 0.0
    sub_delta = 0.0
    picks = ((ws_name, ws_level), (ws2_name, ws2_level))
    slots = read_weapon_special_slots(weapon)
    for slot_idx, (pick_name, pick_level) in enumerate(picks):
        if pick_level <= 0 or not pick_name:
            continue
        enabled, sa_name, curve = slots[slot_idx]
        if not enabled or sa_name != pick_name or not curve:
            continue
        idx = pick_level - 1
        if not (0 <= idx < len(curve)):
            continue
        value = float(curve[idx])
        if sa_name in (f"{main_attr}+", "主能力+"):
            main_delta += value
        elif sa_name in (f"{sub_attr}+", "副能力+"):
            sub_delta += value
    return main_delta, sub_delta


def add_special_picks_attack_percent(
    weapon: dict[str, Any],
    *,
    ws_name: str,
    ws_level: int,
    ws2_name: str = "",
    ws2_level: int = 0,
    target_name: str = "攻击力+",
) -> float:
    """特殊能力字段内 ``攻击力+`` 等按档位累加（用于最终攻击乘区）。"""
    total = 0.0
    picks = ((ws_name, ws_level), (ws2_name, ws2_level))
    slots = read_weapon_special_slots(weapon)
    for slot_idx, (pick_name, pick_level) in enumerate(picks):
        if pick_level <= 0 or pick_name != target_name:
            continue
        enabled, sa_name, curve = slots[slot_idx]
        if not enabled or sa_name != target_name or not curve:
            continue
        idx = pick_level - 1
        if 0 <= idx < len(curve):
            total += float(curve[idx])
    return total


def get_special_value_at_level(
    weapon: dict[str, Any],
    slot_index: int,
    *,
    name: str,
    level: int,
) -> float | None:
    """读取某条特殊能力在指定档位下的数值（用于展示）。"""
    if level <= 0:
        return None
    enabled, sa_name, curve = read_weapon_special_slots(weapon)[slot_index]
    if not enabled or sa_name != name or not curve:
        return None
    idx = level - 1
    if 0 <= idx < len(curve):
        return float(curve[idx])
    return None
