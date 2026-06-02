#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""DAG 桥接函数：搜索评估用 DAG 引擎替代本地引擎计算伤害。

迁移目标：
- ``evaluate_task()`` 原本调用 ``calculate_single_hit_damage``（本地引擎）
- 本桥接函数处理同样的 effect 列表，调用 ``compute_15_zone_damage``（DAG 注册函数）
- 消除双计算路径，统一走 DAG 框架
"""

from __future__ import annotations

from framework.adapters.endfield.functions import compute_15_zone_damage

from games.endfield.calc.damage.combo_bonus import combo_zone_multiplier
from games.endfield.calc.damage.break_defense import damage_effects_from_break_defense
from games.endfield.calc.damage.engine.helpers import _clamp, _collect_effects
from games.endfield.calc.damage.engine.types import CritMode, DamageContext, DamageEffect

__all__ = [
    "evaluate_search_damage",
]


def evaluate_search_damage(
    *,
    final_attack: float,
    skill_multiplier: float,
    damage_type: str,
    skill_type: str,
    is_unbalanced: bool,
    is_true_damage: bool,
    enemy_defense: float,
    enemy_resistance: float,
    ignore_resistance: float,
    imbalance_vulnerability_coeff: float,
    crit_rate: float,
    crit_damage: float,
    damage_type_bonus: float,
    skill_type_bonus: float,
    imbalance_damage_bonus: float,
    other_damage_bonus: float,
    combo_stacks: int = 0,
    break_defense_stacks: int = 0,
    base_damage_bonus: float = 0.0,
    effects: list[DamageEffect] | None = None,
    crit_mode: CritMode = "non_crit",
) -> float:
    """用 DAG 注册函数替代本地引擎计算单段伤害。

    此函数复制了 ``calculate_single_hit_damage`` 的效果处理逻辑
    （_collect_effects → 乘区累加 → combo_bonus → defense → resistance），
    最终调用 ``compute_15_zone_damage``（框架适配器注册的 DAG 函数）。

    参数与 ``DamageContext`` 字段一一对应，方便调用方直接映射。

    Returns:
        最终伤害值（float）
    """
    all_effects = list(effects or []) + list(damage_effects_from_break_defense(break_defense_stacks))

    # 用轻量上下文对象做效果过滤（只需 damage_type / skill_type / is_unbalanced）
    _ctx = DamageContext(
        final_attack=final_attack,
        skill_multiplier=skill_multiplier,
        damage_type=damage_type,
        skill_type=skill_type,
        is_unbalanced=is_unbalanced,
        is_true_damage=is_true_damage,
        enemy_defense=enemy_defense,
        enemy_resistance=enemy_resistance,
        ignore_resistance=ignore_resistance,
        imbalance_vulnerability_coeff=imbalance_vulnerability_coeff,
        crit_rate=crit_rate,
        crit_damage=crit_damage,
        damage_type_bonus=damage_type_bonus,
        skill_type_bonus=skill_type_bonus,
        imbalance_damage_bonus=imbalance_damage_bonus,
        other_damage_bonus=other_damage_bonus,
        combo_stacks=combo_stacks,
        break_defense_stacks=break_defense_stacks,
        base_damage_bonus=base_damage_bonus,
    )
    known_effects, _unknown, _warnings = _collect_effects(_ctx, all_effects)

    # 累加效果到各乘区（与 calculate.py 完全一致）
    dmg_bonus = 1.0 + damage_type_bonus + skill_type_bonus + imbalance_damage_bonus + other_damage_bonus
    dmg_reduction = 1.0
    amplification = 1.0
    weakness = 1.0
    shelter_values: list[float] = []
    fragile = 1.0
    vulnerability = 1.0
    combo_bonus_flat = 0.0
    non_control_reduction = 1.0
    special_zone = 1.0
    resistance_extra = 0.0
    resistance_change = 0.0
    defense_change = 0.0
    imbalance_coeff_override: float | None = None

    for effect in known_effects:
        v = float(effect.value)
        et = effect.effect_type
        if et == "伤害减免":
            dmg_reduction *= 1.0 - v
        elif et == "增幅":
            amplification += v
        elif et == "虚弱":
            weakness *= 1.0 - v
        elif et == "庇护":
            shelter_values.append(v)
        elif et == "脆弱":
            fragile += v
        elif et == "易伤":
            vulnerability += v
        elif et == "连击增伤":
            combo_bonus_flat += v
        elif et in ("伤害类型伤害加成", "技能类型伤害加成", "失衡伤害加成", "其他伤害加成"):
            dmg_bonus += v
        elif et == "无视抗性":
            resistance_extra += v
        elif et == "抗性":
            resistance_change += v
        elif et == "防御":
            defense_change += v
        elif et == "失衡易伤系数":
            imbalance_coeff_override = v
        elif et == "非主控减伤":
            non_control_reduction *= 1.0 - v
        elif et == "特殊乘区":
            special_zone *= v

    shelter = 1.0 - max(shelter_values, default=0.0)

    # 连击增伤 — 委托 combo_zone_multiplier
    combo_bonus = combo_zone_multiplier(
        skill_type, combo_stacks,
        flat_legacy_bonus=max(0.0, combo_bonus_flat),
    )

    # 防御区
    if is_true_damage:
        defense_zone_val = 1.0
    else:
        effective_def = max(0.0, enemy_defense + defense_change)
        defense_zone_val = 100.0 / (effective_def + 100.0)

    # 抗性区
    total_resistance = enemy_resistance + resistance_change
    total_ignore = ignore_resistance + resistance_extra
    resistance_zone_val = 1.0 - total_resistance / 100.0 + total_ignore / 100.0

    # 失衡易伤区
    imb_coeff = imbalance_coeff_override if imbalance_coeff_override is not None else imbalance_vulnerability_coeff
    imbalance_zone_val = imb_coeff if is_unbalanced else 1.0

    # 调用 DAG 注册函数 compute_15_zone_damage
    return compute_15_zone_damage(
        final_attack=final_attack,
        skill_multiplier=skill_multiplier,
        base_damage_bonus=base_damage_bonus,
        crit_rate=_clamp(crit_rate, 0.0, 1.0),
        crit_damage=crit_damage,
        crit_mode=crit_mode,
        damage_type_bonus=dmg_bonus - 1.0,
        damage_reduction=1.0 - dmg_reduction,
        amplification=amplification - 1.0,
        weakness=1.0 - weakness,
        shelter=1.0 - shelter,
        fragile=fragile - 1.0,
        vulnerability=vulnerability - 1.0,
        enemy_defense=enemy_defense,
        defense_change=defense_change,
        is_true_damage=is_true_damage,
        imbalance_coeff=imb_coeff,
        is_unbalanced=is_unbalanced,
        enemy_resistance=total_resistance,
        ignore_resistance=total_ignore,
        non_control_reduction=1.0 - non_control_reduction,
        combo_bonus=max(0.0, combo_bonus - 1.0),
        special=special_zone,
    )
