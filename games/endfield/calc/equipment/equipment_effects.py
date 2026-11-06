#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""装备效果文本解析（P2-07 从 ``system.py`` 拆出）。"""

from __future__ import annotations

import re
from typing import Any

from games.endfield.calc.damage.engine import DamageEffect
from games.endfield.calc.damage.types import infer_equipment_damage_types

_PERCENT_RE = re.compile(r"([+-]?\d+(?:\.\d+)?)\s*%")


def _parse_percent_value(text: str) -> float:
    """从文本中解析百分比数值（如 "15%" → 0.15）。"""
    m = _PERCENT_RE.search(text)
    if not m:
        return 0.0
    return float(m.group(1)) / 100.0


def _infer_damage_types(text: str) -> tuple[str, ...]:
    """infer damage types。"""
    return infer_equipment_damage_types(text)


def _parse_effect_text(text: str, *, source: str) -> DamageEffect:
    from games.endfield.calc.equipment.affix import parse_equipment_affix_line

    affix_effects, _ = parse_equipment_affix_line(text, source=source)

    if affix_effects:
        return affix_effects[0]

    value = _parse_percent_value(text)

    if "易伤" in text:
        return DamageEffect("易伤", value=value, source=source, raw_text=text, damage_types=_infer_damage_types(text))

    if "脆弱" in text:
        return DamageEffect("脆弱", value=value, source=source, raw_text=text, damage_types=_infer_damage_types(text))

    if "虚弱" in text:
        return DamageEffect("虚弱", value=value, source=source, raw_text=text)

    if "庇护" in text:
        return DamageEffect("庇护", value=value, source=source, raw_text=text)

    if "伤害减免" in text:
        return DamageEffect(
            "伤害减免", value=value, source=source, raw_text=text, damage_types=_infer_damage_types(text)
        )

    if "连击增伤" in text:
        return DamageEffect("连击增伤", value=value, source=source, raw_text=text)

    if "增幅" in text:
        return DamageEffect("增幅", value=value, source=source, raw_text=text, damage_types=_infer_damage_types(text))

    if "伤害+" in text or "伤害加成" in text:
        damage_types = _infer_damage_types(text)

        effect_type = "伤害类型伤害加成" if damage_types else "其他伤害加成"

        return DamageEffect(
            effect_type,
            value=value,
            source=source,
            raw_text=text,
            damage_types=damage_types,
        )

    return DamageEffect(text.strip(), value=value, source=source, raw_text=text)


def _parse_effect_keys(params: dict[str, Any], prefix: str, source: str) -> list[DamageEffect]:
    effects: list[DamageEffect] = []

    for idx in range(1, 10):
        key = f"{prefix}{idx}"

        text = str(params.get(key, "")).strip()

        if not text:
            continue

        effects.append(_parse_effect_text(text, source=source))

    return effects
