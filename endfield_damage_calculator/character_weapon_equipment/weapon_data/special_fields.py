#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""武器有条件特殊能力字段：特殊能力1 / 特殊能力2（兼容旧 特殊能力）。"""

from __future__ import annotations

from typing import Any

SPECIAL_FIELD_KEYS: tuple[str, ...] = ("特殊能力1", "特殊能力2")
LEGACY_SPECIAL_KEY = "特殊能力"


def parse_special_field(field: Any) -> tuple[bool, str, list[float], int]:
    """解析单条特殊能力字段 → (启用, 名称, 九档曲线, 最大叠加层数)。"""
    if field is False or field == [False]:
        return False, "", [], 1
    if not isinstance(field, list) or len(field) < 3 or field[0] is not True:
        return False, "", [], 1
    name = field[1] if isinstance(field[1], str) else ""
    curve = field[2] if isinstance(field[2], list) else []
    max_stack = 1
    if len(field) >= 4 and isinstance(field[3], int):
        max_stack = max(1, int(field[3]))
    return True, name, [float(v) for v in curve], max_stack


def build_special_field(
    *,
    enabled: bool,
    name: str = "",
    curve: list[float] | None = None,
    max_stack: int = 1,
) -> list:
    """构造 JSON 特殊能力字段。"""
    if not enabled:
        return [False]
    out: list[Any] = [True, name, list(curve or [])]
    if max_stack > 1:
        out.append(int(max_stack))
    return out


def read_weapon_special_slots(
    weapon: dict[str, Any],
) -> list[tuple[bool, str, list[float], int]]:
    """
    读取武器两条有条件特殊能力。

    若仅有旧字段 ``特殊能力``，视为 ``特殊能力1``。
    """
    slots: list[tuple[bool, str, list[float], int]] = []
    for key in SPECIAL_FIELD_KEYS:
        if key in weapon:
            slots.append(parse_special_field(weapon.get(key)))
        else:
            slots.append((False, "", [], 1))
    if not weapon.get(SPECIAL_FIELD_KEYS[0]) and LEGACY_SPECIAL_KEY in weapon:
        slots[0] = parse_special_field(weapon.get(LEGACY_SPECIAL_KEY))
    return slots


def write_weapon_special_slots(
    weapon: dict[str, Any],
    slots: list[tuple[bool, str, list[float], int] | tuple[bool, str, list[float]]],
) -> None:
    """写入 ``特殊能力1`` / ``特殊能力2``，并移除旧 ``特殊能力`` 键。"""
    for idx, key in enumerate(SPECIAL_FIELD_KEYS):
        enabled, name, curve, max_stack = False, "", [], 1
        if idx < len(slots):
            slot = slots[idx]
            enabled, name, curve = slot[0], slot[1], slot[2]
            max_stack = int(slot[3]) if len(slot) > 3 else 1
        weapon[key] = build_special_field(
            enabled=enabled, name=name, curve=curve, max_stack=max_stack
        )
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


def bonus_curve_for_key(weapon: dict[str, Any], attr_key: str) -> list[float]:
    """读取附加属性 ``xxx+`` 的层数曲线。"""
    raw = weapon.get(attr_key)
    if not isinstance(raw, list):
        return []
    return [float(v) for v in raw]


def special_pick_bonus(
    curve: list[float],
    max_stack: int,
    *,
    skill_level: int,
    stack_count: int,
) -> float:
    """特殊能力加成：九档基准 × 叠加层数（不可叠加武器内部固定 ×1）。"""
    if skill_level <= 0 or not curve:
        return 0.0
    effective_stack = 1 if max_stack <= 1 else max(0, int(stack_count))
    if effective_stack <= 0:
        return 0.0
    idx = max(0, min(int(skill_level) - 1, len(curve) - 1))
    return float(curve[idx]) * effective_stack


def apply_conditional_special_to_stats(
    weapon: dict[str, Any],
    *,
    ws_name: str,
    ws_level: int,
    ws_stack: int = 1,
    ws2_name: str = "",
    ws2_level: int = 1,
    ws2_stack: int = 1,
    main_attr: str,
    sub_attr: str,
) -> tuple[float, float]:
    """
    按 GUI 选用档位，将特殊能力1/2 的数值计入主/副能力加成。

    返回 (main_bonus_delta, sub_bonus_delta)。
    """
    main_delta = 0.0
    sub_delta = 0.0
    picks = (
        (ws_name, ws_level, ws_stack),
        (ws2_name, ws2_level, ws2_stack),
    )
    for slot_idx, (pick_name, pick_level, pick_stack) in enumerate(picks):
        if pick_level <= 0 or not pick_name:
            continue
        enabled, sa_name, curve, max_stack = read_weapon_special_slots(weapon)[slot_idx]
        if not enabled or sa_name != pick_name or not curve:
            continue
        value = special_pick_bonus(
            curve, max_stack, skill_level=pick_level, stack_count=pick_stack
        )
        if sa_name in (f"{main_attr}+", "主能力+"):
            main_delta += value
        elif sa_name in (f"{sub_attr}+", "副能力+"):
            sub_delta += value
    return main_delta, sub_delta


def add_special_picks_to_main_sub_bonus(
    weapon: dict[str, Any],
    *,
    ws_name: str,
    ws_level: int,
    ws_stack: int = 1,
    ws2_name: str = "",
    ws2_level: int = 1,
    ws2_stack: int = 1,
    main_attr: str,
    sub_attr: str,
) -> tuple[float, float]:
    """将已启用的特殊能力1/2 档位加成累加到主/副能力（与旧 ``特殊能力`` 逻辑一致）。"""
    return apply_conditional_special_to_stats(
        weapon,
        ws_name=ws_name,
        ws_level=ws_level,
        ws_stack=ws_stack,
        ws2_name=ws2_name,
        ws2_level=ws2_level,
        ws2_stack=ws2_stack,
        main_attr=main_attr,
        sub_attr=sub_attr,
    )


def add_special_picks_attack_percent(
    weapon: dict[str, Any],
    *,
    ws_name: str,
    ws_level: int,
    ws_stack: int = 1,
    ws2_name: str = "",
    ws2_level: int = 1,
    ws2_stack: int = 1,
    target_name: str = "攻击力+",
) -> float:
    """特殊能力字段内 ``攻击力+`` 等按技能等级与叠加层数累加（用于最终攻击乘区）。"""
    total = 0.0
    picks = (
        (ws_name, ws_level, ws_stack),
        (ws2_name, ws2_level, ws2_stack),
    )
    slots = read_weapon_special_slots(weapon)
    for slot_idx, (pick_name, pick_level, pick_stack) in enumerate(picks):
        if pick_level <= 0 or not pick_name:
            continue
        enabled, sa_name, curve, max_stack = slots[slot_idx]
        if not enabled or sa_name != pick_name or not curve:
            continue
        if target_name in sa_name:
            total += special_pick_bonus(
                curve, max_stack, skill_level=pick_level, stack_count=pick_stack
            )
    return total


def get_special_value_at_level(
    weapon: dict[str, Any],
    slot_index: int,
    *,
    name: str,
    level: int,
    stack_count: int = 1,
) -> float | None:
    """读取某条特殊能力在指定技能等级与叠加层下的数值（用于展示）。"""
    if level <= 0:
        return None
    enabled, sa_name, curve, max_stack = read_weapon_special_slots(weapon)[slot_index]
    if not enabled or sa_name != name or not curve:
        return None
    return special_pick_bonus(
        curve, max_stack, skill_level=level, stack_count=stack_count
    )


def migrate_legacy_weapon_special_level(
    ws_level: int,
    *,
    ws_stack: int | None = None,
) -> tuple[int, int]:
    """旧预设 ``ws_level`` → (技能等级, 叠加层数)。"""
    if ws_stack is not None:
        return max(1, int(ws_level)), max(0, int(ws_stack))
    level = int(ws_level)
    if level <= 0:
        return 1, 0
    return level, 1
