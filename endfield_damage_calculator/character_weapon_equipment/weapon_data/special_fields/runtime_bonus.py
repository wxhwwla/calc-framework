#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""武器有条件特殊能力字段：特殊能力1 / 特殊能力2（兼容旧 特殊能力）。"""

from __future__ import annotations

from typing import Any

import re

from .name_utils import _special_name_matches
from .slots_io import read_weapon_special_slots


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
) -> tuple[float, float, float, float]:
    """
    按 GUI 选用档位，将特殊能力1/2 的数值计入主/副能力加成。

    返回 (main_flat_delta, sub_flat_delta, main_pct_delta, sub_pct_delta)。

    分类规则：
        - 平值加成：主能力值+、副能力值+、{main_attr}+、{sub_attr}+
        - 百分比加成：主能力+、副能力+、全能力+（同时影响主副）
    """
    main_flat = 0.0
    sub_flat = 0.0
    main_pct = 0.0
    sub_pct = 0.0
    picks = (
        (ws_name, ws_level, ws_stack),
        (ws2_name, ws2_level, ws2_stack),
    )
    for slot_idx, (pick_name, pick_level, pick_stack) in enumerate(picks):
        if pick_level <= 0 or not pick_name:
            continue
        enabled, sa_name, curve, max_stack = read_weapon_special_slots(weapon)[slot_idx]
        if not enabled or not _special_name_matches(pick_name, sa_name) or not curve:
            continue
        value = special_pick_bonus(
            curve, max_stack, skill_level=pick_level, stack_count=pick_stack
        )
        if sa_name == "主能力值+":
            main_flat += value
        elif sa_name == "副能力值+":
            sub_flat += value
        elif sa_name == f"{main_attr}+":
            main_flat += value
        elif sa_name == f"{sub_attr}+":
            sub_flat += value
        elif sa_name == "主能力+":
            main_pct += value
        elif sa_name == "副能力+":
            sub_pct += value
        elif sa_name == "全能力+":
            main_pct += value
            sub_pct += value
    return main_flat, sub_flat, main_pct, sub_pct


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
    """仅返回特殊能力中的平值加成 (主, 副) —— 向后兼容。"""
    mf, sf, _, _ = apply_conditional_special_to_stats(
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
    return mf, sf


def add_special_picks_to_ability_pct(
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
    """仅返回特殊能力中的百分比加成 (主, 副)。"""
    _, _, mp, sp = apply_conditional_special_to_stats(
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
    return mp, sp


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
        if not enabled or not _special_name_matches(pick_name, sa_name) or not curve:
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
    special_raw = weapon.get("special_skills")
    if isinstance(special_raw, list) and slot_index < len(special_raw):
        item = special_raw[slot_index]
        if isinstance(item, dict):
            special_name = str(item.get("name", ""))
            special_effect = str(item.get("effect", ""))
            curve = item.get("curve")
            if not _special_name_matches(name, special_name, special_effect):
                return None
            if not isinstance(curve, list) or not curve:
                return None
            return special_pick_bonus(
                [float(v) for v in curve],
                int(item.get("max_stack", 1)),
                skill_level=level,
                stack_count=stack_count,
            )

    enabled, sa_name, curve, max_stack = read_weapon_special_slots(weapon)[slot_index]
    if not enabled or not _special_name_matches(name, sa_name) or not curve:
        return None
    return special_pick_bonus(curve, max_stack, skill_level=level, stack_count=stack_count)


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
