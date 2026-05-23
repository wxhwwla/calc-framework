#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""多技能加权总伤遍历。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from calculation.damage_engine import DamageContext, DamageEffect, calculate_single_hit_damage
from calculation.loadout_optimizer import (
    OptimizerConfig,
    WeaponCandidate,
    enumerate_optimizer_tasks,
)
from calculation.equipment_system import build_four_slot_loadout, collect_loadout_effects


@dataclass(frozen=True)
class SkillScenario:
    """单个技能场景定义。"""

    skill_name: str
    skill_multiplier: float
    skill_type: str = ""
    external_effects: tuple[DamageEffect, ...] = ()


@dataclass(frozen=True)
class MultiSkillConfig:
    """多技能加权配置。"""

    top_n: int = 10
    selected_skill: str = "战技"
    weights: Optional[dict[str, float]] = None
    crit_mode: str = "non_crit"


@dataclass(frozen=True)
class MultiSkillScore:
    """单条多技能评分。"""

    weapon_name: str
    loadout_names: dict[str, str]
    skill_breakdown: dict[str, float]
    weighted_total_damage: float


@dataclass(frozen=True)
class MultiSkillResult:
    """多技能搜索结果。"""

    top_results: tuple[MultiSkillScore, ...]
    weight_map: dict[str, float]
    total_combinations: int


def _resolve_weights(scenarios: list[SkillScenario], config: MultiSkillConfig) -> dict[str, float]:
    if config.weights is not None:
        weights = {s.skill_name: float(config.weights.get(s.skill_name, 0.0)) for s in scenarios}
    else:
        weights = {
            s.skill_name: (1.0 if s.skill_name == config.selected_skill else 0.0) for s in scenarios
        }
    if all(v == 0.0 for v in weights.values()):
        raise ValueError("技能权重不能全为 0。")
    return weights


def optimize_multi_skill_loadouts(
    *,
    base_context: DamageContext,
    weapons: list[WeaponCandidate],
    equipment_catalog: dict[str, list[dict]],
    scenarios: list[SkillScenario],
    config: MultiSkillConfig = MultiSkillConfig(),
) -> MultiSkillResult:
    """按多技能加权总伤进行搜索。"""
    if not scenarios:
        return MultiSkillResult(top_results=(), weight_map={}, total_combinations=0)
    weight_map = _resolve_weights(scenarios, config)
    tasks, total_combinations, _pruned, _warnings = enumerate_optimizer_tasks(
        base_context=base_context,
        weapons=weapons,
        equipment_catalog=equipment_catalog,
        config=OptimizerConfig(
            top_n=config.top_n,
            crit_mode=config.crit_mode,  # type: ignore[arg-type]
            allow_duplicate_accessory=True,
            prune_non_beneficial=False,
            warn_on_unfiltered=False,
        ),
    )
    scores: list[MultiSkillScore] = []
    for weapon, (chest, gloves, acc_a, acc_b) in tasks:
        loadout = build_four_slot_loadout(
            chest=chest,
            gloves=gloves,
            accessory_a=acc_a,
            accessory_b=acc_b,
            allow_duplicate_accessory=True,
        )
        base_effects = list(weapon.effects) + collect_loadout_effects(loadout)
        breakdown: dict[str, float] = {}
        weighted_total = 0.0
        for scenario in scenarios:
            ctx = DamageContext(
                final_attack=weapon.final_attack,
                skill_multiplier=scenario.skill_multiplier,
                damage_type=base_context.damage_type,
                skill_type=scenario.skill_type or base_context.skill_type,
                is_unbalanced=base_context.is_unbalanced,
                is_true_damage=base_context.is_true_damage,
                enemy_defense=base_context.enemy_defense,
                enemy_resistance=base_context.enemy_resistance,
                ignore_resistance=base_context.ignore_resistance,
                imbalance_vulnerability_coeff=base_context.imbalance_vulnerability_coeff,
                crit_rate=base_context.crit_rate,
                crit_damage=base_context.crit_damage,
                damage_type_bonus=base_context.damage_type_bonus,
                skill_type_bonus=base_context.skill_type_bonus,
                imbalance_damage_bonus=base_context.imbalance_damage_bonus,
                other_damage_bonus=base_context.other_damage_bonus,
            )
            dmg = calculate_single_hit_damage(
                ctx,
                effects=base_effects + list(scenario.external_effects),
                crit_mode=config.crit_mode,  # type: ignore[arg-type]
            ).final_damage
            breakdown[scenario.skill_name] = dmg
            weighted_total += dmg * weight_map.get(scenario.skill_name, 0.0)
        scores.append(
            MultiSkillScore(
                weapon_name=weapon.name,
                loadout_names={
                    "chest": chest.get("名称", ""),
                    "gloves": gloves.get("名称", ""),
                    "accessory_a": acc_a.get("名称", ""),
                    "accessory_b": acc_b.get("名称", ""),
                },
                skill_breakdown=breakdown,
                weighted_total_damage=weighted_total,
            )
        )
    top = tuple(
        sorted(scores, key=lambda s: s.weighted_total_damage, reverse=True)[: max(1, config.top_n)]
    )
    return MultiSkillResult(top_results=top, weight_map=weight_map, total_combinations=total_combinations)
