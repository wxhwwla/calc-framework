# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""腐蚀持续降抗（NGA PART 02 §2.2）。"""

from __future__ import annotations

from games.endfield.calc.damage.abnormal_attached import corrosion_initial_resistance_shred
from games.endfield.calc.damage.originium_arts import enhance_attached_effect

CORROSION_DURATION_SEC = 15.0
CORROSION_DR_PER_SEC: tuple[float, ...] = (0.84, 1.12, 1.4, 1.68)
CORROSION_DR_CAP: tuple[float, ...] = (12.0, 16.0, 20.0, 24.0)


def _level_index(calc_level: int) -> int:
    """level index。"""
    return min(max(1, int(calc_level)), 4) - 1


def corrosion_total_resistance_shred(
    calc_level: int,
    *,
    elapsed_seconds: float = CORROSION_DURATION_SEC,
    originium_arts_strength: float = 0.0,
    effect_multiplier: float = 1.0,
) -> float:
    """腐蚀状态内总降抗点数（初始 + 持续，带上限）。"""
    idx = _level_index(calc_level)
    initial = corrosion_initial_resistance_shred(
        calc_level,
        originium_arts_strength=originium_arts_strength,
        effect_multiplier=effect_multiplier,
    )
    per_sec_base = CORROSION_DR_PER_SEC[idx] * effect_multiplier
    per_sec = enhance_attached_effect(per_sec_base, originium_arts_strength)
    elapsed = max(0.0, min(float(elapsed_seconds), CORROSION_DURATION_SEC))
    drip = per_sec * elapsed
    cap = enhance_attached_effect(CORROSION_DR_CAP[idx] * effect_multiplier, originium_arts_strength)
    return min(initial + drip, cap)
