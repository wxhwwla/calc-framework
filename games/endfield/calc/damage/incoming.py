# SPDX-License-Identifier: AGPL-3.0
"""敌人对干员造成伤害（NGA PART 02 §2.6 等）。"""

from __future__ import annotations

from games.endfield.calc.damage.engine import CritMode, DamageContext, calculate_single_hit_damage


def enemy_burn_tick_damage(
    max_hp: float,
    *,
    hot_resistance_percent: float = 0.0,
    ignore_resistance_percent: float = 0.0,
    crit_mode: CritMode = "non_crit",
) -> float:
    """敌人燃烧：每秒 最大生命×2% 的灼热伤害（无视防御）。"""
    ctx = DamageContext(
        final_attack=float(max_hp),
        skill_multiplier=0.02,
        damage_type="法术-灼热",
        skill_type="异常",
        enemy_defense=0.0,
        enemy_resistance=float(hot_resistance_percent),
        ignore_resistance=float(ignore_resistance_percent),
    )
    return float(
        calculate_single_hit_damage(ctx, crit_mode=crit_mode, damage_pipeline="abnormal").final_damage
    )
