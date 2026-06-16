# SPDX-License-Identifier: AGPL-3.0
"""处决伤害（NGA PART 03 §3.3）。"""

from __future__ import annotations

from games.endfield.calc.dag_adapter.search_evaluate import evaluate_search_damage
from games.endfield.calc.damage.engine import CritMode, DamageContext, DamageEffect

# 敌人等阶 → 处决承伤系数
EXECUTE_DAMAGE_MULT: dict[str, float] = {
    "普通": 1.0,
    "进阶": 1.25,
    "精英": 1.5,
    "头目": 1.5,
    "领袖": 1.75,
}

# 处决恢复技力
EXECUTE_SP_RESTORE: dict[str, int] = {
    "普通": 25,
    "进阶": 35,
    "精英": 50,
    "头目": 50,
    "领袖": 100,
}


def execute_damage_multiplier(enemy_tier: str) -> float:
    """execute damage multiplier。"""
    return float(EXECUTE_DAMAGE_MULT.get(str(enemy_tier).strip(), 1.0))


def execute_sp_restore(enemy_tier: str) -> int:
    """execute sp restore。"""
    return int(EXECUTE_SP_RESTORE.get(str(enemy_tier).strip(), 25))


def calculate_execute_damage(
    *,
    context: DamageContext,
    normal_attack_multiplier: float,
    enemy_tier: str = "普通",
    effects: list[DamageEffect] | None = None,
    crit_mode: CritMode = "non_crit",
    manual_buffs: list[dict[str, str | float]] | None = None,
) -> tuple[float, float]:
    """处决伤害 = 常规 15 乘区伤害 × 处决承伤系数。

    返回 (最终伤害, 处决承伤系数)。
    """
    mult = execute_damage_multiplier(enemy_tier)
    base = evaluate_search_damage(
        final_attack=context.final_attack,
        skill_multiplier=float(normal_attack_multiplier),
        damage_type=context.damage_type,
        skill_type="普通攻击",
        is_unbalanced=True,
        is_true_damage=context.is_true_damage,
        enemy_defense=context.enemy_defense,
        enemy_resistance=context.enemy_resistance,
        ignore_resistance=context.ignore_resistance,
        imbalance_vulnerability_coeff=context.imbalance_vulnerability_coeff,
        crit_rate=context.crit_rate,
        crit_damage=context.crit_damage,
        damage_type_bonus=context.damage_type_bonus,
        skill_type_bonus=context.skill_type_bonus,
        imbalance_damage_bonus=context.imbalance_damage_bonus,
        other_damage_bonus=context.other_damage_bonus,
        combo_stacks=context.combo_stacks,
        break_defense_stacks=context.break_defense_stacks,
        base_damage_bonus=context.base_damage_bonus,
        effects=effects,
        crit_mode=crit_mode,
        manual_buffs=manual_buffs,
    )
    return float(base.final_damage) * mult, mult
