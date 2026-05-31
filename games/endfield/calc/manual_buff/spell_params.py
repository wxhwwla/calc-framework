#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""法术异常参数表（集中维护）。"""

from __future__ import annotations

from typing import Literal, TypedDict

# 公测口径：法术异常/爆发等级系数区
SPELL_LEVEL_COEFF_DIVISOR = 196.0

# 交叉附着触发的四类法术异常（导电/腐蚀/燃烧/冻结）初始伤害倍率
SPELL_CROSS_ANOMALY_INITIAL_RATIO = 0.80
# 燃烧持续伤害：每秒一次，默认持续 10 秒
SPELL_BURN_DOT_RATIO = 0.12
SPELL_BURN_DURATION_SECONDS = 10
# 任意同属性法术爆发
SPELL_BURST_RATIO = 1.60
# 碎冰：物理伤害，等级系数按法术异常（/196）
SPELL_SHATTER_ICE_RATIO = 1.20

SpellFormulaKind = Literal["cross_anomaly", "burn", "burst", "shatter_ice"]


class SpellAbnormalParamRow(TypedDict):
    """法术异常参数定义行。"""

    key: str
    damage_type: str
    event_kind: str
    formula: SpellFormulaKind
    # 游戏内名称（说明用）
    game_name: str


SPELL_ABNORMAL_PARAM_ROWS: tuple[SpellAbnormalParamRow, ...] = (
    {
        "key": "灼热异常",
        "damage_type": "法术-灼热",
        "event_kind": "异常",
        "formula": "burn",
        "game_name": "燃烧",
    },
    {
        "key": "灼热爆发",
        "damage_type": "法术-灼热",
        "event_kind": "爆发",
        "formula": "burst",
        "game_name": "法术爆发",
    },
    {
        "key": "电磁异常",
        "damage_type": "法术-电磁",
        "event_kind": "异常",
        "formula": "cross_anomaly",
        "game_name": "导电",
    },
    {
        "key": "电磁爆发",
        "damage_type": "法术-电磁",
        "event_kind": "爆发",
        "formula": "burst",
        "game_name": "法术爆发",
    },
    {
        "key": "寒冷异常",
        "damage_type": "法术-寒冷",
        "event_kind": "异常",
        "formula": "cross_anomaly",
        "game_name": "冻结",
    },
    {
        "key": "寒冷爆发",
        "damage_type": "法术-寒冷",
        "event_kind": "爆发",
        "formula": "burst",
        "game_name": "法术爆发",
    },
    {
        "key": "自然异常",
        "damage_type": "法术-自然",
        "event_kind": "异常",
        "formula": "cross_anomaly",
        "game_name": "腐蚀",
    },
    {
        "key": "自然爆发",
        "damage_type": "法术-自然",
        "event_kind": "爆发",
        "formula": "burst",
        "game_name": "法术爆发",
    },
    {
        "key": "碎冰",
        "damage_type": "物理",
        "event_kind": "碎冰",
        "formula": "shatter_ice",
        "game_name": "碎冰",
    },
)


def calc_level_from_ui(ui_level: int) -> int:
    """UI L0–L4 → 计算异常等级 1–5（与物理异常一致）。"""
    return max(1, min(5, int(ui_level) + 1))


def base_multiplier_for_formula(formula: SpellFormulaKind, *, calc_level: int) -> float:
    """
    单次触发的基础技能倍率（未乘等级系数区、未乘最终攻击以外的乘区）。

    - 交叉异常：80% × (1 + 异常等级)
    - 燃烧：初始 + 10 秒 DoT（12% × (1 + 异常等级)/秒）
    - 爆发：固定 160%
    - 碎冰：120% × (1 + 异常等级)，伤害类型为物理
    """
    level_factor = 1.0 + float(calc_level)
    if formula == "burst":
        return SPELL_BURST_RATIO
    if formula == "shatter_ice":
        return SPELL_SHATTER_ICE_RATIO * level_factor
    if formula == "burn":
        initial = SPELL_CROSS_ANOMALY_INITIAL_RATIO * level_factor
        dot_total = SPELL_BURN_DOT_RATIO * level_factor * float(SPELL_BURN_DURATION_SECONDS)
        return initial + dot_total
    return SPELL_CROSS_ANOMALY_INITIAL_RATIO * level_factor


def preview_level_multipliers(formula: SpellFormulaKind) -> tuple[float, float, float, float, float]:
    """返回 UI L0–L4 各档的基础倍率（供快照/测试）。"""
    return tuple(base_multiplier_for_formula(formula, calc_level=calc_level_from_ui(ui_level)) for ui_level in range(5))
