# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""技力与终结技能量（NGA PART 04 节选）。"""

from __future__ import annotations

SP_NATURAL_REGEN_PER_SEC = 8.0
DODGE_SP_GAIN = 7.5
# 文内提及重击回能但未给固定值；此处为占位常量，供循环估算调参
HEAVY_ATTACK_SP_GAIN = 20.0

ULTIMATE_CHARGE_PER_100_SP = 6.5
LINK_SKILL_ULTIMATE_CHARGE = 10.0
DEFAULT_MAX_SP = 100.0
DEFAULT_MAX_ULTIMATE_CHARGE = 100.0


def sp_after_natural_regen(
    current_sp: float,
    seconds: float,
    *,
    max_sp: float = DEFAULT_MAX_SP,
) -> float:
    """自然回能后的技力（上限 max_sp）。"""
    return min(float(max_sp), float(current_sp) + SP_NATURAL_REGEN_PER_SEC * max(0.0, float(seconds)))


def ultimate_charge_from_sp_gain(
    sp_gained: float,
    *,
    is_refund: bool = False,
) -> float:
    """技力增量 → 终结技能量；返还技力不计终结充能（NGA）。"""
    if is_refund or sp_gained <= 0.0:
        return 0.0
    return float(sp_gained) * ULTIMATE_CHARGE_PER_100_SP / 100.0


def estimate_ultimate_after_actions(
    current_charge: float,
    *,
    sp_gains: tuple[float, ...] = (),
    sp_refunds: tuple[float, ...] = (),
    link_skill_count: int = 0,
    max_charge: float = DEFAULT_MAX_ULTIMATE_CHARGE,
) -> float:
    """叠加多次技力获取与连携终结充能后的终结技能量。"""
    charge = float(current_charge)
    for gain in sp_gains:
        charge += ultimate_charge_from_sp_gain(gain, is_refund=False)
    for refund in sp_refunds:
        charge += ultimate_charge_from_sp_gain(refund, is_refund=True)
    charge += max(0, int(link_skill_count)) * LINK_SKILL_ULTIMATE_CHARGE
    return min(float(max_charge), charge)
