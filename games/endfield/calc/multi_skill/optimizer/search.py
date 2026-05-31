#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""
多技能加权总伤优化模块。

核心功能：支持多技能场景下的配装搜索，按加权总伤害评分。

评分公式：
    总伤 = Σ(单技能单次伤害 × 该技能释放次数)

设计目标：
- 快速预览与全量遍历共用统一的评分语义
- 支持段级（segment-level）技能定义和次数配置
- 支持外部效果注入（如队伍buff、环境效果等）

关键数据结构：
- SkillScenario: 单个技能段场景定义（技能名称、倍率、类型、段索引、外部效果）
- MultiSkillConfig: 多技能配置（Top-N、选中技能、技能次数映射、暴击模式）
- MultiSkillScore: 单条配装的多技能评分（含各段伤害明细）
- MultiSkillResult: 搜索结果汇总

场景键格式："技能类型:段索引"（如 "战技:1"、"普攻:2"）
"""

from __future__ import annotations

from games.endfield.calc.damage.engine import CritMode, DamageContext, calculate_single_hit_damage
from games.endfield.calc.equipment.affix import aggregate_loadout_modifiers
from games.endfield.calc.equipment.prune import character_ability_attrs
from games.endfield.calc.equipment.system import build_four_slot_loadout, collect_loadout_effects
from games.endfield.calc.loadout.optimizer import (
    LoadoutScore,
    OptimizerConfig,
    OptimizerTask,
    WeaponCandidate,
    enumerate_optimizer_tasks,
)
from games.endfield.calc.multiplicative_zones.final_attack_zone import calculate_final_attack_with_details
from games.endfield.calc.search.evaluate.context import SearchEvalContext

from .types import MultiSkillConfig, MultiSkillResult, MultiSkillScore, SkillScenario, resolve_scenario_damage_type


def _resolve_skill_counts(
    scenarios: list[SkillScenario],
    config: MultiSkillConfig,
) -> dict[str, int]:
    """解析技能次数映射。

    优先使用配置中的 skill_counts，若未设置则根据 selected_skill 自动分配。

    Args:
        scenarios: 技能场景列表
        config: 多技能配置

    Returns:
        场景键到次数的映射

    Raises:
        ValueError: 如果所有技能次数都为 0
    """
    if config.skill_counts is not None:
        from games.endfield.calc.skills.segments import normalize_manual_segment_counts

        normalized = normalize_manual_segment_counts(config.skill_counts, scenarios)
        counts = {s.scenario_key: normalized.get(s.scenario_key, 0) for s in scenarios}
    else:
        counts = {s.scenario_key: 0 for s in scenarios}
        for s in scenarios:
            if s.resolved_skill_type == config.selected_skill and s.resolved_segment_index == 1:
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
    character: dict | None = None,
) -> MultiSkillResult:
    """按多技能加权总伤进行搜索（快速预览版）。

    执行流程：
    1. 解析技能次数映射
    2. 生成任务迭代器
    3. 遍历所有配装组合，计算每个组合在各技能场景下的伤害
    4. 计算加权总伤害（Σ 单次伤害 × 次数）
    5. 返回 Top-N 最优结果

    Args:
        base_context: 基础伤害上下文
        weapons: 候选武器列表
        equipment_catalog: 装备目录
        scenarios: 技能场景列表
        config: 多技能配置
        character: 角色数据（用于自动配置装备排序优先级）

    Returns:
        MultiSkillResult 对象，包含 Top-N 最优配装和技能次数映射
    """
    if not scenarios:
        return MultiSkillResult(top_results=(), skill_count_map={}, total_combinations=0)
    count_map = _resolve_skill_counts(scenarios, config)
    skill_types = tuple(dict.fromkeys(s.resolved_skill_type for s in scenarios if count_map.get(s.scenario_key, 0) > 0))
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
                damage_type=resolve_scenario_damage_type(scenario, base_context),
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
    top = tuple(sorted(scores, key=lambda s: s.weighted_total_damage, reverse=True)[: max(1, config.top_n)])
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
    search_eval: SearchEvalContext | None = None,
) -> LoadoutScore:
    """评估单条配装的多技能加权总伤（供全量并行/续跑搜索）。

    与 optimize_multi_skill_loadouts 的区别：
    - 支持 search_eval 上下文，可按等级曲线重算攻击力
    - 返回 LoadoutScore 格式，便于与单技能搜索共用 TopNTracker

    Args:
        shared_context: 共享的伤害上下文
        crit_mode: 暴击模式
        task: 搜索任务（武器候选 + 四格配装）
        scenarios: 技能场景元组
        skill_counts: 技能次数映射
        search_eval: 搜索评估上下文（用于全量搜索时重算攻击力）

    Returns:
        LoadoutScore 对象，其中 final_damage 为加权总伤害（Σ 单次伤害 × 次数）
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

    from games.endfield.calc.skills.segments import normalize_manual_segment_counts

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
            damage_type=resolve_scenario_damage_type(scenario, shared_context),
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
