# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""物理/法术异常共用倍率与乘区。"""

from __future__ import annotations

from games.endfield.calc.damage.originium_arts import strength_zone_multiplier


def abnormal_level_factor(calc_level: int) -> float:
    """异常等级系数 (1+等级)，与 NGA 交叉异常/碎甲/猛击一致。"""
    return 1.0 + float(max(1, int(calc_level)))


def physical_abnormal_base_multiplier(abnormal: str, calc_level: int) -> float:
    """单次触发基础技能倍率（未乘等级系数区、源石技艺区）。"""
    if abnormal in ("倒地", "击飞"):
        return 1.2
    factor = abnormal_level_factor(calc_level)
    if abnormal == "碎甲":
        return 0.5 * factor
    if abnormal == "猛击":
        return 1.5 * factor
    return 0.0


def apply_abnormal_post_zones(damage: float, *, originium_arts_strength: float) -> float:
    """异常伤害在 15 乘区后再乘源石技艺强度区。"""
    return float(damage) * strength_zone_multiplier(originium_arts_strength)
