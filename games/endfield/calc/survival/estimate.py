# SPDX-License-Identifier: AGPL-3.0
"""处决/治疗/失衡/技力估算（GUI 与 Web 共用）。"""

from __future__ import annotations

from typing import Any

from games.endfield.calc.character_stats import total_max_hp
from games.endfield.calc.damage.combat_resources import (
    DODGE_SP_GAIN,
    SP_NATURAL_REGEN_PER_SEC,
    ULTIMATE_CHARGE_PER_100_SP,
    estimate_ultimate_after_actions,
    sp_after_natural_regen,
)
from games.endfield.calc.damage.engine import DamageContext
from games.endfield.calc.damage.execute import calculate_execute_damage, execute_sp_restore
from games.endfield.calc.damage.healing import HealingContext, calculate_healing, received_heal_efficiency_from_will
from games.endfield.calc.damage.imbalance import (
    accumulation_multiplier_after_fast_break,
    imbalance_cap_for_tier,
    imbalance_duration_for_tier,
    imbalance_node_thresholds,
    scaled_imbalance_gain,
)
from games.endfield.calc.damage.incoming import enemy_burn_tick_damage
from games.endfield.calc.damage.special_damage import life_steal_heal
from games.endfield.calc.multiplicative_zones.final_attack_zone import calculate_final_attack_with_details
from games.endfield.data_loading.enemy_params import resolve_enemy_max_hp


def build_survival_estimate(
    *,
    char_data: dict[str, Any],
    weapon_data: dict[str, Any],
    char_level: int,
    weapon_level: int,
    trust_level: int = 0,
    enemy_tier: str = "普通",
    imbalance_efficiency_bonus: float = 0.0,
    enemy_max_hp: float | None = None,
    enemy_id: str = "",
    base_heal_flat: float = 201.6,
    stat_per_point: float = 0.47,
    heal_efficiency: float = 0.20,
    independent_heal_bonus: float = 0.30,
    imbalance_gain_base: float = 10.0,
    hot_resistance_percent: float = 0.0,
    sp_start: float = 0.0,
    sp_seconds: float = 5.0,
    ult_start: float = 0.0,
    life_steal_rate: float = 0.10,
    weapon_skill_kwargs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """汇总处决、失衡、燃烧、技力、治疗估算结果。"""
    plugin_hp = resolve_enemy_max_hp(enemy_id)
    hp = float(enemy_max_hp if enemy_max_hp is not None else plugin_hp or 6605.0)

    cap = imbalance_cap_for_tier(enemy_tier)
    duration = imbalance_duration_for_tier(enemy_tier)
    nodes_1 = imbalance_node_thresholds(cap, 1)
    nodes_2 = imbalance_node_thresholds(cap, 2)
    gain = scaled_imbalance_gain(
        float(imbalance_gain_base),
        imbalance_efficiency_bonus=float(imbalance_efficiency_bonus),
    )
    gain_pct = min(100.0, gain / cap * 100.0) if cap > 0 else 0.0
    fast_mult = accumulation_multiplier_after_fast_break(
        tier=enemy_tier,
        seconds_since_combat_start=2.0,
        seconds_since_last_imbalance_end=0.5,
        was_fast_break=True,
    )

    burn_tick = enemy_burn_tick_damage(hp, hot_resistance_percent=float(hot_resistance_percent)) if hp > 0 else 0.0

    details = calculate_final_attack_with_details(
        char_data,
        weapon_data,
        char_level=char_level,
        weapon_level=weapon_level,
        trust_level=trust_level,
        **dict(weapon_skill_kwargs or {}),
    )
    exec_ctx = DamageContext(
        final_attack=float(details["final_attack"]),
        skill_multiplier=1.0,
        damage_type="物理",
        skill_type="普通攻击",
        is_unbalanced=True,
    )
    execute_damage, execute_mult = calculate_execute_damage(
        context=exec_ctx,
        normal_attack_multiplier=1.0,
        enemy_tier=enemy_tier,
    )
    sp_restore = execute_sp_restore(enemy_tier)

    sp_after = sp_after_natural_regen(float(sp_start), float(sp_seconds))
    sp_gain = max(0.0, sp_after - float(sp_start))
    ult_after = estimate_ultimate_after_actions(float(ult_start), sp_gains=(sp_gain, DODGE_SP_GAIN))
    life_steal_heal_amount = life_steal_heal(float(execute_damage), life_steal_rate=float(life_steal_rate))

    will_attr = char_data.get("意志", [0.0])
    idx = min(max(0, int(char_level) - 1), len(will_attr) - 1) if will_attr else 0
    will = float(will_attr[idx]) if will_attr else 0.0
    strength_attr = char_data.get("力量", [0.0])
    sidx = min(max(0, int(char_level) - 1), len(strength_attr) - 1) if strength_attr else 0
    strength = float(strength_attr[sidx]) if strength_attr else 0.0
    char_hp = total_max_hp(strength, level=char_level)
    healing = calculate_healing(
        HealingContext(
            base_heal_flat=float(base_heal_flat),
            stat_per_point=float(stat_per_point),
            stat_value=will,
            max_hp=char_hp,
            heal_efficiency=float(heal_efficiency),
            received_heal_efficiency=received_heal_efficiency_from_will(will),
            independent_heal_bonus=float(independent_heal_bonus),
        )
    )

    return {
        "execute_damage": float(execute_damage),
        "execute_multiplier": float(execute_mult),
        "execute_sp_restore": int(sp_restore),
        "imbalance_cap": float(cap),
        "imbalance_duration_sec": float(duration),
        "imbalance_nodes_1": list(nodes_1),
        "imbalance_nodes_2": list(nodes_2),
        "imbalance_gain_effective": float(gain),
        "imbalance_gain_percent": float(gain_pct),
        "fast_break_multiplier": float(fast_mult),
        "burn_tick_per_sec": float(burn_tick),
        "enemy_max_hp": float(hp),
        "sp_after_regen": float(sp_after),
        "sp_regen_per_sec": float(SP_NATURAL_REGEN_PER_SEC),
        "ultimate_charge_after": float(ult_after),
        "ultimate_charge_per_100_sp": float(ULTIMATE_CHARGE_PER_100_SP),
        "dodge_sp_gain": float(DODGE_SP_GAIN),
        "life_steal_heal": float(life_steal_heal_amount),
        "healing_amount": float(healing["治疗量"]),
        "character_max_hp": float(char_hp),
    }
