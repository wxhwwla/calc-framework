#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""法术异常参数表（集中维护）。"""

from __future__ import annotations

from typing import TypedDict


class SpellAbnormalParamRow(TypedDict):
    """法术异常参数定义行。"""

    key: str
    damage_type: str
    event_kind: str
    level_coeffs: tuple[float, float, float, float, float]


_DEFAULT_LEVEL_COEFFS: tuple[float, float, float, float, float] = (1.0, 2.0, 3.0, 4.0, 5.0)

SPELL_ABNORMAL_PARAM_ROWS: tuple[SpellAbnormalParamRow, ...] = (
    {
        "key": "灼热异常",
        "damage_type": "法术-灼热",
        "event_kind": "异常",
        "level_coeffs": _DEFAULT_LEVEL_COEFFS,
    },
    {
        "key": "灼热爆发",
        "damage_type": "法术-灼热",
        "event_kind": "爆发",
        "level_coeffs": _DEFAULT_LEVEL_COEFFS,
    },
    {
        "key": "电磁异常",
        "damage_type": "法术-电磁",
        "event_kind": "异常",
        "level_coeffs": _DEFAULT_LEVEL_COEFFS,
    },
    {
        "key": "电磁爆发",
        "damage_type": "法术-电磁",
        "event_kind": "爆发",
        "level_coeffs": _DEFAULT_LEVEL_COEFFS,
    },
    {
        "key": "寒冷异常",
        "damage_type": "法术-寒冷",
        "event_kind": "异常",
        "level_coeffs": _DEFAULT_LEVEL_COEFFS,
    },
    {
        "key": "寒冷爆发",
        "damage_type": "法术-寒冷",
        "event_kind": "爆发",
        "level_coeffs": _DEFAULT_LEVEL_COEFFS,
    },
    {
        "key": "自然异常",
        "damage_type": "法术-自然",
        "event_kind": "异常",
        "level_coeffs": _DEFAULT_LEVEL_COEFFS,
    },
    {
        "key": "自然爆发",
        "damage_type": "法术-自然",
        "event_kind": "爆发",
        "level_coeffs": _DEFAULT_LEVEL_COEFFS,
    },
)

