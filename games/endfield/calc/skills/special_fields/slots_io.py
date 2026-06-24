#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""武器有条件特殊能力字段：特殊能力1 / 特殊能力2（兼容旧 特殊能力）。"""

from __future__ import annotations

from typing import Any

from .codec import LEGACY_SPECIAL_KEY, SPECIAL_FIELD_KEYS, build_special_field, parse_special_field
from .name_utils import _extract_effect_name_from_special_name


def read_weapon_special_slots(
    weapon: dict[str, Any],
) -> list[tuple[bool, str, list[float], int]]:
    """

    读取武器两条有条件特殊能力。



    若仅有旧字段 ``特殊能力``，视为 ``特殊能力1``。

    """

    special_raw = weapon.get("special_skills")

    if isinstance(special_raw, list):
        slots: list[tuple[bool, str, list[float], int]] = []

        for idx in range(2):
            if idx >= len(special_raw) or not isinstance(special_raw[idx], dict):
                slots.append((False, "", [], 1))

                continue

            item = special_raw[idx]

            name = str(item.get("name", "")).strip()

            effect = str(item.get("effect", "")).strip()

            curve = item.get("curve")

            max_stack = max(1, int(item.get("max_stack", 1)))

            if not name and effect:
                name = effect

            if not isinstance(curve, list) or not curve:
                slots.append((False, "", [], 1))

                continue

            slots.append((True, name, [float(v) for v in curve], max_stack))

        return slots

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

    if isinstance(weapon.get("special_skills"), list):
        existing = weapon.get("special_skills") or []

        out: list[dict[str, Any]] = []

        for idx in range(2):
            enabled, name, curve, max_stack = False, "", [], 1

            if idx < len(slots):
                slot = slots[idx]

                enabled, name, curve = slot[0], slot[1], slot[2]

                max_stack = int(slot[3]) if len(slot) > 3 else 1

            if not enabled or not name or not curve:
                continue

            old = existing[idx] if idx < len(existing) and isinstance(existing[idx], dict) else {}

            condition = str(old.get("condition", ""))

            effect = str(old.get("effect", "")) or _extract_effect_name_from_special_name(name)

            out.append(
                {
                    "zone": int(old.get("zone", 3)),
                    "name": name,
                    "condition": condition,
                    "effect": effect,
                    "curve": [float(v) for v in curve],
                    "max_stack": max(1, max_stack),
                }
            )

        weapon["special_skills"] = out

        for key in SPECIAL_FIELD_KEYS:
            weapon.pop(key, None)

        weapon.pop(LEGACY_SPECIAL_KEY, None)

        return

    for idx, key in enumerate(SPECIAL_FIELD_KEYS):
        enabled, name, curve, max_stack = False, "", [], 1

        if idx < len(slots):
            slot = slots[idx]

            enabled, name, curve = slot[0], slot[1], slot[2]

            max_stack = int(slot[3]) if len(slot) > 3 else 1

        weapon[key] = build_special_field(enabled=enabled, name=name, curve=curve, max_stack=max_stack)

    weapon.pop(LEGACY_SPECIAL_KEY, None)
