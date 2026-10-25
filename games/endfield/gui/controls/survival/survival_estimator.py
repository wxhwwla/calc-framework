# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""生存估算服务 — 处决/治疗/失衡/灼烧/资源计算（无 PySide6 依赖）。

从 qt_survival_dialog.py 拆分而来，可被 Web/CLI/测试复用。
"""

from __future__ import annotations

from dataclasses import dataclass
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
from games.endfield.calc.damage.healing import (
    HealingContext,
    calculate_healing,
    received_heal_efficiency_from_will,
)
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


@dataclass(frozen=True)
class ExecuteResult:
    """处决伤害估算结果。"""

    damage: float
    multiplier: float
    sp_restore: int


@dataclass(frozen=True)
class ImbalanceResult:
    """失衡参数估算结果。"""

    cap: float
    duration: float
    nodes_1: list[float]
    nodes_2: list[float]
    gain: float
    gain_pct: float
    fast_break_mult: float


@dataclass(frozen=True)
class ResourceResult:
    """资源估算结果。"""

    sp_after: float
    sp_rate: float
    ult_after: float
    ult_charge: float
    dodge_gain: float
    life_steal_heal: float


@dataclass(frozen=True)
class HealingResult:
    """治疗估算结果。"""

    heal_amount: float


def estimate_execute(
    char_data: dict[str, Any],
    weapon_data: dict[str, Any],
    char_level: int,
    weapon_level: int,
    trust_level: int,
    enemy_tier: str,
    weapon_skill_kwargs: dict[str, Any] | None = None,
) -> ExecuteResult:
    """估算处决伤害。"""
    details = calculate_final_attack_with_details(
        char_data,
        weapon_data,
        char_level=char_level,
        weapon_level=weapon_level,
        trust_level=trust_level,
        **(weapon_skill_kwargs or {}),
    )
    ctx = DamageContext(
        final_attack=float(details["final_attack"]),
        skill_multiplier=1.0,
        damage_type="物理",
        skill_type="普通攻击",
        is_unbalanced=True,
    )
    dmg, mult = calculate_execute_damage(
        context=ctx,
        normal_attack_multiplier=1.0,
        enemy_tier=enemy_tier,
    )
    sp = execute_sp_restore(enemy_tier)
    return ExecuteResult(damage=float(dmg), multiplier=float(mult), sp_restore=sp)


def estimate_imbalance(
    enemy_tier: str,
    gain_base: float = 10.0,
    gain_efficiency: float = 0.0,
) -> ImbalanceResult:
    """估算失衡参数。"""
    cap = imbalance_cap_for_tier(enemy_tier)
    duration = imbalance_duration_for_tier(enemy_tier)
    nodes_1 = list(imbalance_node_thresholds(cap, 1))
    nodes_2 = list(imbalance_node_thresholds(cap, 2))
    gain = scaled_imbalance_gain(gain_base, imbalance_efficiency_bonus=gain_efficiency)
    pct = min(100.0, gain / cap * 100.0) if cap > 0 else 0.0
    mult = accumulation_multiplier_after_fast_break(
        tier=enemy_tier,
        seconds_since_combat_start=2.0,
        seconds_since_last_imbalance_end=0.5,
        was_fast_break=True,
    )
    return ImbalanceResult(
        cap=cap,
        duration=duration,
        nodes_1=nodes_1,
        nodes_2=nodes_2,
        gain=gain,
        gain_pct=pct,
        fast_break_mult=mult,
    )


def estimate_burn(enemy_max_hp: float, hot_resistance_percent: float = 0.0) -> float:
    """估算灼烧 tick 伤害。"""
    if enemy_max_hp <= 0:
        return 0.0
    return enemy_burn_tick_damage(enemy_max_hp, hot_resistance_percent=hot_resistance_percent)


def estimate_resources(
    sp_start: float,
    sp_seconds: float,
    ult_start: float,
    execute_damage: float = 0.0,
    life_steal_rate: float = 0.10,
) -> ResourceResult:
    """估算技力/终极技/生命窃取。"""
    sp = sp_after_natural_regen(sp_start, sp_seconds)
    sp_gain = max(0.0, sp - sp_start)
    ult = estimate_ultimate_after_actions(
        ult_start,
        sp_gains=(sp_gain, DODGE_SP_GAIN),
    )
    heal = life_steal_heal(execute_damage, life_steal_rate=life_steal_rate)
    return ResourceResult(
        sp_after=sp,
        sp_rate=SP_NATURAL_REGEN_PER_SEC,
        ult_after=ult,
        ult_charge=ULTIMATE_CHARGE_PER_100_SP,
        dodge_gain=DODGE_SP_GAIN,
        life_steal_heal=heal,
    )


def estimate_healing(
    base_heal: float,
    stat_per_point: float,
    will: float,
    char_data: dict[str, Any],
    char_level: int,
    heal_efficiency: float,
    independent_heal_bonus: float,
) -> HealingResult:
    """估算治疗量。"""
    strength = float(char_data.get("力量", [0.0])[min(char_level - 1, 89)])
    hp = total_max_hp(strength, level=char_level)
    out = calculate_healing(
        HealingContext(
            base_heal_flat=base_heal,
            stat_per_point=stat_per_point,
            stat_value=will,
            max_hp=hp,
            heal_efficiency=heal_efficiency,
            received_heal_efficiency=received_heal_efficiency_from_will(will),
            independent_heal_bonus=independent_heal_bonus,
        )
    )
    return HealingResult(heal_amount=float(out["治疗量"]))
