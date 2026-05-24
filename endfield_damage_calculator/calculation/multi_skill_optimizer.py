#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多技能加权总伤：快速预览与全量遍历（手动次数）共用评分语义。

总伤 = Σ(单技能单次伤害 × GUI 填写的释放次数)。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from calculation.damage_engine import CritMode, DamageContext, DamageEffect, calculate_single_hit_damage
from calculation.equipment_affix import aggregate_loadout_modifiers
from calculation.loadout_optimizer import (
    LoadoutScore,
    OptimizerConfig,
    OptimizerTask,
    WeaponCandidate,
    enumerate_optimizer_tasks,
)
from calculation.multiplicative_zones.final_attack_zone import calculate_final_attack_with_details
from calculation.search_eval_context import SearchEvalContext
from calculation.equipment_prune import character_ability_attrs
from calculation.equipment_system import build_four_slot_loadout, collect_loadout_effects


@dataclass(frozen=True)
class SkillScenario:
    """单个技能段场景定义。"""

    skill_name: str
    skill_multiplier: float
    skill_type: str = ""
    segment_index: int = 1
    external_effects: tuple[DamageEffect, ...] = ()

    @property
    def scenario_key(self) -> str:
        """段级键（与次数 dict、breakdown 一致）。"""
        if ":" in self.skill_name:
            return self.skill_name
        skill = self.skill_type or self.skill_name
        return f"{skill}:{self.segment_index}"

    @property
    def resolved_skill_type(self) -> str:
        """装备加成与伤害上下文用的技能类型。"""
        if ":" in self.skill_name:
            return self.skill_name.split(":", 1)[0]
        return self.skill_type or self.skill_name

    @property
    def resolved_segment_index(self) -> int:
        if ":" in self.skill_name:
            try:
                return max(1, int(self.skill_name.split(":", 1)[1]))
            except ValueError:
                return 1
        return max(1, self.segment_index)


@dataclass(frozen=True)
class MultiSkillConfig:
    """多技能次数加权配置（总伤 = Σ 单次伤害 × 释放次数）。"""

    top_n: int = 10
    selected_skill: str = "战技"
    skill_counts: Optional[dict[str, int]] = None
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
    skill_count_map: dict[str, int]
    total_combinations: int

    @property
    def weight_map(self) -> dict[str, float]:
        """兼容旧测试/调用方（次数以 float 暴露）。"""
        return {name: float(count) for name, count in self.skill_count_map.items()}


def _resolve_skill_counts(
    scenarios: list[SkillScenario],
    config: MultiSkillConfig,
) -> dict[str, int]:
    if config.skill_counts is not None:
        from calculation.skill_segments import normalize_manual_segment_counts

        normalized = normalize_manual_segment_counts(config.skill_counts, scenarios)
        counts = {s.scenario_key: normalized.get(s.scenario_key, 0) for s in scenarios}
    else:
        counts = {s.scenario_key: 0 for s in scenarios}
        for s in scenarios:
            if (
                s.resolved_skill_type == config.selected_skill
                and s.resolved_segment_index == 1
            ):
                counts[s.scenario_key] = 1
                break
        else:
            if scenarios:
                counts[scenarios[0].scenario_key] = 1
    if all(v == 0 for v in counts.values()):
        raise ValueError("技能次数不能全为 0。")
    return counts


def optimize_multi_skill_loadouts(
    *,
    base_context: DamageContext,
    weapons: list[WeaponCandidate],
    equipment_catalog: dict[str, list[dict]],
    scenarios: list[SkillScenario],
    config: MultiSkillConfig = MultiSkillConfig(),
    character: Optional[dict] = None,
) -> MultiSkillResult:
    """按多技能加权总伤进行搜索。"""
    if not scenarios:
        return MultiSkillResult(top_results=(), skill_count_map={}, total_combinations=0)
    count_map = _resolve_skill_counts(scenarios, config)
    skill_types = tuple(
        dict.fromkeys(
            (
                s.resolved_skill_type
                for s in scenarios
                if count_map.get(s.scenario_key, 0) > 0
            )
        )
    )
    main_attr, sub_attr = character_ability_attrs(character or {})
    tasks, total_combinations, _pruned, _warnings = enumerate_optimizer_tasks(
        base_context=base_context,
        weapons=weapons,
        equipment_catalog=equipment_catalog,
        config=OptimizerConfig(
            top_n=config.top_n,
            crit_mode=config.crit_mode,  # type: ignore[arg-type]
            allow_duplicate_accessory=True,
            prune_non_beneficial=True,
            warn_on_unfiltered=False,
            main_attr=main_attr,
            sub_attr=sub_attr,
            priority_skill_types=skill_types,
            sort_equipment_by_priority=bool(main_attr or sub_attr or skill_types),
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
                skill_type=scenario.resolved_skill_type or base_context.skill_type,
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
            breakdown[scenario.scenario_key] = dmg
            weighted_total += dmg * count_map.get(scenario.scenario_key, 0)
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
    return MultiSkillResult(
        top_results=top,
        skill_count_map=count_map,
        total_combinations=total_combinations,
    )


def evaluate_multi_skill_task(
    *,
    shared_context: DamageContext,
    crit_mode: CritMode,
    task: OptimizerTask,
    scenarios: tuple[SkillScenario, ...],
    skill_counts: dict[str, int],
    search_eval: Optional[SearchEvalContext] = None,
) -> LoadoutScore:
    """
    评估单条配装的多技能加权总伤（供全量并行/续跑搜索）。

    ``LoadoutScore.final_damage`` 为 Σ(单段伤害 × 次数)。
    """
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

    from calculation.skill_segments import normalize_manual_segment_counts

    normalized_counts = normalize_manual_segment_counts(skill_counts, list(scenarios))
    weighted_total = 0.0
    segment_breakdown: dict[str, float] = {}
    for scenario in scenarios:
        key = scenario.scenario_key
        count = normalized_counts.get(key, 0)
        if count <= 0:
            continue
        ctx = DamageContext(
            final_attack=final_attack,
            skill_multiplier=scenario.skill_multiplier,
            damage_type=shared_context.damage_type,
            skill_type=scenario.resolved_skill_type or shared_context.skill_type,
            is_unbalanced=shared_context.is_unbalanced,
            is_true_damage=shared_context.is_true_damage,
            enemy_defense=shared_context.enemy_defense,
            enemy_resistance=shared_context.enemy_resistance,
            ignore_resistance=shared_context.ignore_resistance,
            imbalance_vulnerability_coeff=shared_context.imbalance_vulnerability_coeff,
            crit_rate=shared_context.crit_rate,
            crit_damage=shared_context.crit_damage,
            damage_type_bonus=shared_context.damage_type_bonus,
            skill_type_bonus=shared_context.skill_type_bonus,
            imbalance_damage_bonus=shared_context.imbalance_damage_bonus,
            other_damage_bonus=shared_context.other_damage_bonus,
        )
        dmg = calculate_single_hit_damage(
            ctx,
            effects=effects + list(scenario.external_effects),
            crit_mode=crit_mode,
        ).final_damage
        segment_breakdown[key] = dmg
        weighted_total += dmg * count

    return LoadoutScore(
        weapon_name=weapon.name,
        final_damage=weighted_total,
        loadout_names={
            "chest": chest.get("名称", ""),
            "gloves": glove.get("名称", ""),
            "accessory_a": acc_a.get("名称", ""),
            "accessory_b": acc_b.get("名称", ""),
        },
        segment_breakdown=segment_breakdown or None,
    )
