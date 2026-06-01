# SPDX-License-Identifier: AGPL-3.0
"""角色基础属性派生（NGA PART 04 §4.2）。"""

from __future__ import annotations


def base_hp_at_level(level: int) -> float:
    """生命值 = 500 + ROUND(5500/98×(等级-1))。"""
    lv = max(1, int(level))
    return 500.0 + round(5500.0 / 98.0 * (lv - 1), 0)


def strength_hp_bonus(strength: float) -> float:
    """力量提供的生命值加成 = 5×力量（整数部分）。"""
    return 5.0 * int(strength)


def total_max_hp(strength: float, *, level: int = 1) -> float:
    return base_hp_at_level(level) + strength_hp_bonus(strength)
