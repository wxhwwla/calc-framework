#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""单技能最优配装搜索（V1）。"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Callable, Iterator, Optional

from calculation.top_n_tracker import TopNTracker

from calculation.damage_engine import CritMode, DamageContext, DamageEffect, calculate_single_hit_damage
from calculation.equipment_affix import aggregate_loadout_modifiers
from calculation.equipment_system import build_four_slot_loadout, collect_loadout_effects
from calculation.multiplicative_zones.final_attack_zone import calculate_final_attack_with_details
from calculation.search_eval_context import SearchEvalContext


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


OptimizerTask = tuple[WeaponCandidate, tuple[dict, dict, dict, dict]]


@dataclass(frozen=True)
class OptimizerSearchPlan:
    """过滤后的搜索计划（不含物化任务列表）。"""

    weapons: tuple[WeaponCandidate, ...]
    equipment_catalog: dict[str, list[dict]]
    total_combinations: int
    pruned_weapon_count: int
    warnings: tuple[str, ...]


def count_loadout_combinations(
    equipment_catalog: dict[str, list[dict]],
    *,
    allow_duplicate_accessory: bool = True,
) -> int:
    """统计四格配装组合数（与 _iter_loadout_combinations 一致）。"""
    chests = equipment_catalog.get("chest", [])
    gloves = equipment_catalog.get("gloves", [])
    accessories = equipment_catalog.get("accessories", [])
    if not chests or not gloves or not accessories:
        return 0
    if allow_duplicate_accessory:
        accessory_pairs = len(accessories) * len(accessories)
    else:
        accessory_pairs = sum(
            1
            for acc_a in accessories
            for acc_b in accessories
            if acc_a.get("名称") != acc_b.get("名称")
        )
    return len(chests) * len(gloves) * accessory_pairs


def _iter_loadout_combinations(
    equipment_catalog: dict[str, list[dict]],
    *,
    allow_duplicate_accessory: bool,
) -> Iterator[tuple[dict, dict, dict, dict]]:
    chests = equipment_catalog.get("chest", [])
    gloves = equipment_catalog.get("gloves", [])
    accessories = equipment_catalog.get("accessories", [])
    for chest, glove, acc_a, acc_b in product(chests, gloves, accessories, accessories):
        if not allow_duplicate_accessory and acc_a.get("名称") == acc_b.get("名称"):
            continue
        yield (chest, glove, acc_a, acc_b)


def build_optimizer_search_plan(
    *,
    weapons: list[WeaponCandidate],
    equipment_catalog: dict[str, list[dict]],
    config: OptimizerConfig,
) -> OptimizerSearchPlan:
    """构建搜索计划并计算组合总数（不物化任务）。"""
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

    loadout_count = count_loadout_combinations(
        filtered_catalog,
        allow_duplicate_accessory=config.allow_duplicate_accessory,
    )
    weapon_count = len(filtered_weapons)
    return OptimizerSearchPlan(
        weapons=tuple(filtered_weapons),
        equipment_catalog=filtered_catalog,
        total_combinations=weapon_count * loadout_count,
        pruned_weapon_count=pruned_weapon_count,
        warnings=tuple(warnings),
    )


def iter_optimizer_tasks(
    plan: OptimizerSearchPlan,
    *,
    allow_duplicate_accessory: bool,
) -> Iterator[OptimizerTask]:
    """按武器 × 配装流式生成任务。"""
    for weapon in plan.weapons:
        for loadout in _iter_loadout_combinations(
            plan.equipment_catalog,
            allow_duplicate_accessory=allow_duplicate_accessory,
        ):
            yield (weapon, loadout)


def enumerate_optimizer_tasks(
    *,
    base_context: DamageContext,
    weapons: list[WeaponCandidate],
    equipment_catalog: dict[str, list[dict]],
    config: OptimizerConfig,
) -> tuple[Iterator[OptimizerTask], int, int, tuple[str, ...]]:
    """生成搜索任务迭代器与总数（不物化全部任务）。"""
    _ = base_context
    plan = build_optimizer_search_plan(
        weapons=weapons,
        equipment_catalog=equipment_catalog,
        config=config,
    )
    return (
        iter_optimizer_tasks(plan, allow_duplicate_accessory=config.allow_duplicate_accessory),
        plan.total_combinations,
        plan.pruned_weapon_count,
        plan.warnings,
    )


def evaluate_task(
    *,
    base_context: DamageContext,
    crit_mode: CritMode,
    task: tuple[WeaponCandidate, tuple[dict, dict, dict, dict]],
    search_eval: Optional[SearchEvalContext] = None,
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
    equip_effects, flat_stats, atk_percent = aggregate_loadout_modifiers(loadout)
    effects = list(weapon.effects) + equip_effects
    final_attack = weapon.final_attack
    if search_eval is not None:
        weapon_data = search_eval.weapon_data_by_name.get(weapon.name)
        if weapon_data is not None:
            details = calculate_final_attack_with_details(
                character=search_eval.char_data,
                weapon=weapon_data,
                char_level=search_eval.char_level,
                weapon_level=search_eval.weapon_level,
                trust_level=search_eval.trust_level,
                equipment_stat_bonus=flat_stats,
                equipment_attack_percent=atk_percent,
            )
            final_attack = float(details["final_attack"])
    ctx = DamageContext(
        final_attack=final_attack,
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

    tracker = TopNTracker(config.top_n, key_fn=lambda score: score.final_damage)
    searched = 0
    for task in tasks:
        tracker.offer(evaluator(task))
        searched += 1
    return OptimizerResult(
        top_results=tracker.results(),
        total_combinations=total_combinations,
        searched_combinations=searched,
        pruned_weapon_count=pruned_weapon_count,
        warnings=warnings,
    )
