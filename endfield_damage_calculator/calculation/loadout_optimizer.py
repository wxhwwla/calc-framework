#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""单技能最优配装搜索（V1）。"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Callable, Optional

from calculation.damage_engine import CritMode, DamageContext, DamageEffect, calculate_single_hit_damage
from calculation.equipment_system import (
    build_four_slot_loadout,
    collect_loadout_effects,
)


@dataclass(frozen=True)
class WeaponCandidate:
    """搜索阶段的武器候选。"""

    name: str
    final_attack: float
    effects: tuple[DamageEffect, ...] = ()


@dataclass(frozen=True)
class OptimizerConfig:
    """搜索配置。"""

    top_n: int = 10
    crit_mode: CritMode = "non_crit"
    allow_duplicate_accessory: bool = True
    prune_non_beneficial: bool = True
    candidate_weapon_names: Optional[set[str]] = None
    candidate_equipment_names: Optional[set[str]] = None
    warn_on_unfiltered: bool = True


@dataclass(frozen=True)
class LoadoutScore:
    """单条配装评分。"""

    weapon_name: str
    final_damage: float
    loadout_names: dict[str, str]


@dataclass(frozen=True)
class OptimizerResult:
    """搜索结果。"""

    top_results: tuple[LoadoutScore, ...]
    total_combinations: int
    searched_combinations: int
    pruned_weapon_count: int
    warnings: tuple[str, ...]


def _is_equipment_beneficial(item: dict) -> bool:
    return bool(item.get("效果") or item.get("三件套效果"))


def _apply_equipment_filter(items: list[dict], candidate_names: Optional[set[str]]) -> list[dict]:
    if not candidate_names:
        return list(items)
    return [item for item in items if item.get("名称") in candidate_names]


def _iter_loadouts(
    equipment_catalog: dict[str, list[dict]],
    *,
    allow_duplicate_accessory: bool,
) -> list[tuple[dict, dict, dict, dict]]:
    chests = equipment_catalog.get("chest", [])
    gloves = equipment_catalog.get("gloves", [])
    accessories = equipment_catalog.get("accessories", [])
    combos: list[tuple[dict, dict, dict, dict]] = []
    for chest, glove, acc_a, acc_b in product(chests, gloves, accessories, accessories):
        if not allow_duplicate_accessory and acc_a.get("名称") == acc_b.get("名称"):
            continue
        combos.append((chest, glove, acc_a, acc_b))
    return combos


def enumerate_optimizer_tasks(
    *,
    base_context: DamageContext,
    weapons: list[WeaponCandidate],
    equipment_catalog: dict[str, list[dict]],
    config: OptimizerConfig,
) -> tuple[list[tuple[WeaponCandidate, tuple[dict, dict, dict, dict]]], int, int, tuple[str, ...]]:
    """生成搜索任务，供串行/并行复用。"""
    warnings: list[str] = []
    if (
        config.warn_on_unfiltered
        and not config.candidate_weapon_names
        and not config.candidate_equipment_names
    ):
        warnings.append("当前未筛选候选武器/装备，可能耗时很长。")

    filtered_weapons = [
        w for w in weapons if not config.candidate_weapon_names or w.name in config.candidate_weapon_names
    ]
    pruned_weapon_count = 0
    if config.prune_non_beneficial:
        kept: list[WeaponCandidate] = []
        for weapon in filtered_weapons:
            if weapon.final_attack <= 0 and not weapon.effects:
                pruned_weapon_count += 1
                continue
            kept.append(weapon)
        filtered_weapons = kept

    filtered_catalog = {
        "chest": _apply_equipment_filter(equipment_catalog.get("chest", []), config.candidate_equipment_names),
        "gloves": _apply_equipment_filter(equipment_catalog.get("gloves", []), config.candidate_equipment_names),
        "accessories": _apply_equipment_filter(
            equipment_catalog.get("accessories", []), config.candidate_equipment_names
        ),
    }
    if config.prune_non_beneficial:
        for key in ("chest", "gloves", "accessories"):
            beneficial = [item for item in filtered_catalog[key] if _is_equipment_beneficial(item)]
            if beneficial:
                filtered_catalog[key] = beneficial

    loadout_combos = _iter_loadouts(
        filtered_catalog, allow_duplicate_accessory=config.allow_duplicate_accessory
    )
    tasks: list[tuple[WeaponCandidate, tuple[dict, dict, dict, dict]]] = [
        (weapon, loadout) for weapon in filtered_weapons for loadout in loadout_combos
    ]
    return tasks, len(tasks), pruned_weapon_count, tuple(warnings)


def evaluate_task(
    *,
    base_context: DamageContext,
    crit_mode: CritMode,
    task: tuple[WeaponCandidate, tuple[dict, dict, dict, dict]],
) -> LoadoutScore:
    """评估单条搜索任务。"""
    weapon, (chest, glove, acc_a, acc_b) = task
    loadout = build_four_slot_loadout(
        chest=chest,
        gloves=glove,
        accessory_a=acc_a,
        accessory_b=acc_b,
        allow_duplicate_accessory=True,
    )
    effects = list(weapon.effects) + collect_loadout_effects(loadout)
    ctx = DamageContext(
        final_attack=weapon.final_attack,
        skill_multiplier=base_context.skill_multiplier,
        damage_type=base_context.damage_type,
        skill_type=base_context.skill_type,
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
    result = calculate_single_hit_damage(ctx, effects=effects, crit_mode=crit_mode)
    return LoadoutScore(
        weapon_name=weapon.name,
        final_damage=result.final_damage,
        loadout_names={
            "chest": chest.get("名称", ""),
            "gloves": glove.get("名称", ""),
            "accessory_a": acc_a.get("名称", ""),
            "accessory_b": acc_b.get("名称", ""),
        },
    )


def _select_top_n(scores: list[LoadoutScore], top_n: int) -> tuple[LoadoutScore, ...]:
    sorted_scores = sorted(scores, key=lambda s: s.final_damage, reverse=True)
    return tuple(sorted_scores[: max(1, top_n)])


def search_best_single_skill_loadouts(
    *,
    base_context: DamageContext,
    weapons: list[WeaponCandidate],
    equipment_catalog: dict[str, list[dict]],
    config: OptimizerConfig = OptimizerConfig(),
    task_evaluator: Optional[
        Callable[[tuple[WeaponCandidate, tuple[dict, dict, dict, dict]]], LoadoutScore]
    ] = None,
) -> OptimizerResult:
    """单技能最优搜索（串行版）。"""
    tasks, total_combinations, pruned_weapon_count, warnings = enumerate_optimizer_tasks(
        base_context=base_context,
        weapons=weapons,
        equipment_catalog=equipment_catalog,
        config=config,
    )
    evaluator = task_evaluator or (
        lambda task: evaluate_task(base_context=base_context, crit_mode=config.crit_mode, task=task)
    )

    scores = [evaluator(task) for task in tasks]
    return OptimizerResult(
        top_results=_select_top_n(scores, config.top_n),
        total_combinations=total_combinations,
        searched_combinations=len(scores),
        pruned_weapon_count=pruned_weapon_count,
        warnings=warnings,
    )
