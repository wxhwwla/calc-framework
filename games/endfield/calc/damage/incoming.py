# SPDX-License-Identifier: AGPL-3.0
"""敌人对干员造成伤害（NGA PART 01 §1.12、PART 02 §2.6 等）。"""

from __future__ import annotations

from games.endfield.calc.damage.engine import CritMode, DamageContext, calculate_single_hit_damage

# 干员抗性乘数下限（最多减伤 90%）
MIN_OPERATOR_RESISTANCE_MULT = 0.1


def operator_resistance_multiplier(stat_value: float) -> float:
    """敌人对干员伤害时的抗性乘数：1 / (0.001×属性整数 + 1)，下限 0.1。"""
    stat_int = max(0, int(stat_value))
    return max(MIN_OPERATOR_RESISTANCE_MULT, 1.0 / (0.001 * stat_int + 1.0))


def operator_resistance_points(stat_value: float) -> float:
    """面板抗性点数 = 100 - 100/(0.001×属性整数 + 1)。"""
    stat_int = max(0, int(stat_value))
    return 100.0 - 100.0 / (0.001 * stat_int + 1.0)


def enemy_incoming_damage_to_operator(
    raw_damage: float,
    *,
    agility: float = 0.0,
    intellect: float = 0.0,
    damage_type: str = "物理",
) -> float:
    """敌人对干员伤害经敏捷(物理)/智识(法术)抗性后的估算值。"""
    dtype = str(damage_type or "物理")
    if dtype.startswith("法术") or dtype in ("灼热", "电磁", "寒冷", "自然", "法术-灼热", "法术-电磁", "法术-寒冷", "法术-自然"):
        mult = operator_resistance_multiplier(intellect)
    else:
        mult = operator_resistance_multiplier(agility)
    return float(raw_damage) * mult


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
