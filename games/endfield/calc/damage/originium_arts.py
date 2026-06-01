# SPDX-License-Identifier: AGPL-3.0
"""源石技艺强度（异常伤害乘区，NGA PART 02 §2.4）。"""

from __future__ import annotations

ORIGINIUM_FLAT_STAT_KEY = "源石技艺强度"


def sum_originium_arts_strength(flat_stats: dict[str, float] | None) -> float:
    """从装备平铺属性汇总源石技艺强度。"""
    if not flat_stats:
        return 0.0
    return float(flat_stats.get(ORIGINIUM_FLAT_STAT_KEY, 0.0))


def strength_zone_multiplier(strength: float) -> float:
    """源石技艺强度区 = 1 + 强度/100。"""
    return 1.0 + max(0.0, float(strength)) / 100.0


def attached_effect_enhancement(strength: float) -> float:
    """碎甲/导电/腐蚀附带效果增强 = 2×强度/(强度+300)。"""
    s = max(0.0, float(strength))
    return 2.0 * s / (s + 300.0)


def enhance_attached_effect(base_effect: float, strength: float) -> float:
    """增强后附带效果 = 原始 × (1 + 附带效果增强)。"""
    return float(base_effect) * (1.0 + attached_effect_enhancement(strength))
