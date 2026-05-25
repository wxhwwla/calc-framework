#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单技能最优配装搜索模块。

核心功能：在武器和装备的组合空间中搜索最优配装方案。

搜索流程：
┌─────────────────────────────────────────────────────────────────────┐
│ 1. 构建搜索计划 (build_optimizer_search_plan)                       │
│    ├── 过滤候选武器/装备                                            │
│    ├── 剪枝无益装备（无效果、无属性词条的装备）                       │
│    ├── 按主/副属性排序装备（可选）                                    │
│    ├── 计算组合总数                                                  │
│    └── 返回 OptimizerSearchPlan                                     │
├─────────────────────────────────────────────────────────────────────┤
│ 2. 生成任务迭代器 (enumerate_optimizer_tasks)                        │
│    └── 流式生成 (武器, 四格配装) 任务对                              │
├─────────────────────────────────────────────────────────────────────┤
│ 3. 评估任务 (evaluate_task)                                         │
│    ├── build_runtime_eval_snapshot: 解析配装 → 效果 + 平铺属性        │
│    ├── calculate_final_attack_with_details: 计算最终攻击力            │
│    ├── calculate_single_hit_damage: 计算单段伤害                      │
│    └── 返回 LoadoutScore                                            │
├─────────────────────────────────────────────────────────────────────┤
│ 4. 收集结果 (TopNTracker)                                           │
│    └── 维护 Top-N 结果集                                            │
└─────────────────────────────────────────────────────────────────────┘

组合空间 = 候选武器数 × 四格配装笛卡尔积（由 FixedLoadoutSelection 控制固定/遍历）

关键数据结构：
- WeaponCandidate: 搜索阶段的武器候选（名称、最终攻击力、武器特效）
- OptimizerConfig: 搜索配置（Top-N数量、暴击模式、装备筛选等）
- OptimizerSearchPlan: 过滤后的搜索计划（不含物化任务列表）
- LoadoutScore: 单条配装评分（武器名、最终伤害、配装名称）
- OptimizerResult: 搜索结果汇总
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterator, Optional

from calculation.top_n_tracker import TopNTracker

from calculation.damage_engine import CritMode, DamageContext, DamageEffect, calculate_single_hit_damage
from calculation.equipment_affix import aggregate_loadout_modifiers
from calculation.equipment_system import build_four_slot_loadout, collect_loadout_effects
from calculation.multiplicative_zones.final_attack_zone import calculate_final_attack_with_details
from calculation.equipment_prune import character_ability_attrs, sort_equipment_catalog_by_priority
from calculation.loadout_slot_search import (
    FixedLoadoutSelection,
    VaryingSlotMask,
    baseline_loadout_from_catalog,
    count_loadout_combinations_for_selection,
    iter_loadout_combinations_for_mask,
    iter_loadout_combinations_for_selection,
    selection_from_legacy_slot_count,
)
from calculation.search_eval_context import SearchEvalContext


@dataclass(frozen=True)
class WeaponCandidate:
    """搜索阶段的武器候选。

    包含武器的核心属性，用于构建搜索任务。

    Attributes:
        name: 武器名称
        final_attack: 武器提供的最终攻击力（已计算武器等级加成）
        effects: 武器特殊能力转换后的 DamageEffect 列表
    """

    name: str
    final_attack: float
    effects: tuple[DamageEffect, ...] = ()


@dataclass(frozen=True)
class OptimizerConfig:
    """搜索配置参数。

    控制搜索行为和结果筛选策略。

    Attributes:
        top_n: 返回前 N 个最优结果，默认 10
        crit_mode: 暴击模式（non_crit/expected/always_crit）
        allow_duplicate_accessory: 是否允许两个饰品槽装备相同装备，默认 True
        prune_non_beneficial: 是否剪枝无益装备（无效果无属性词条），默认 True
        sort_equipment_by_priority: 是否按优先级排序装备，默认 False
        main_attr: 主属性（用于装备排序）
        sub_attr: 副属性（用于装备排序）
        priority_skill_types: 优先技能类型（用于装备排序）
        candidate_weapon_names: 候选武器名称集合（为空则不限制）
        candidate_equipment_names: 候选装备名称集合（为空则不限制）
        warn_on_unfiltered: 未筛选时是否警告，默认 True
        fixed_loadout: 固定配装选择（控制哪些槽位固定、哪些遍历）
        varying_slot_count: 可变槽位数（遗留参数，与 fixed_loadout 互斥）
    """

    top_n: int = 10
    crit_mode: CritMode = "non_crit"
    allow_duplicate_accessory: bool = True
    prune_non_beneficial: bool = True
    sort_equipment_by_priority: bool = False
    main_attr: str = ""
    sub_attr: str = ""
    priority_skill_types: tuple[str, ...] = ()
    candidate_weapon_names: Optional[set[str]] = None
    candidate_equipment_names: Optional[set[str]] = None
    warn_on_unfiltered: bool = True
    fixed_loadout: FixedLoadoutSelection = FixedLoadoutSelection()
    varying_slot_count: Optional[int] = None


@dataclass(frozen=True)
class LoadoutScore:
    """单条配装的评分结果。

    包含配装的核心评估指标。

    Attributes:
        weapon_name: 武器名称
        final_damage: 计算得到的最终伤害值
        loadout_names: 四格配装的名称字典（chest/gloves/accessory_a/accessory_b）
        segment_breakdown: 分段伤害明细（多技能模式下使用）
    """

    weapon_name: str
    final_damage: float
    loadout_names: dict[str, str]
    segment_breakdown: Optional[dict[str, float]] = None


@dataclass(frozen=True)
class RuntimeEvalSnapshot:
    """单条任务的运行时快照。

    将武器和配装组合解析为可复用的评估数据结构。

    Attributes:
        weapon_name: 武器名称
        final_attack: 计算后的最终攻击力（含装备加成）
        effects: 所有效果列表（武器特效 + 装备效果）
        loadout_names: 四格配装的名称字典
    """

    weapon_name: str
    final_attack: float
    effects: tuple[DamageEffect, ...]
    loadout_names: dict[str, str]


@dataclass(frozen=True)
class OptimizerResult:
    """搜索结果汇总。

    包含搜索的完整结果和统计信息。

    Attributes:
        top_results: Top-N 最优配装列表
        total_combinations: 理论组合总数
        searched_combinations: 实际搜索的组合数
        pruned_weapon_count: 被剪枝的武器数量
        warnings: 搜索过程中的警告信息
    """

    top_results: tuple[LoadoutScore, ...]
    total_combinations: int
    searched_combinations: int
    pruned_weapon_count: int
    warnings: tuple[str, ...]


def _is_equipment_beneficial(item: dict) -> bool:
    """判断装备是否有益（值得参与搜索）。

    有套装效果、三件套效果，或有属性词条（战技加成、四维等）的装备视为有益。
    无任何效果和属性词条的装备会被剪枝，不参与搜索。

    Args:
        item: 装备数据字典

    Returns:
        True 如果装备有益，False 否则
    """
    if item.get("效果") or item.get("三件套效果"):
        return True
    affixes = item.get("属性词条") or []
    return bool(affixes)


def _apply_equipment_filter(items: list[dict], candidate_names: Optional[set[str]]) -> list[dict]:
    """根据候选名称集合过滤装备列表。

    Args:
        items: 装备列表
        candidate_names: 候选名称集合（为空则不过滤）

    Returns:
        过滤后的装备列表
    """
    if not candidate_names:
        return list(items)
    return [item for item in items if item.get("名称") in candidate_names]


OptimizerTask = tuple[WeaponCandidate, tuple[dict, dict, dict, dict]]
"""搜索任务类型：(武器候选, (胸甲, 手套, 饰品A, 饰品B))"""


@dataclass(frozen=True)
class OptimizerSearchPlan:
    """过滤后的搜索计划（不含物化任务列表）。

    包含搜索所需的所有信息，但不物化任务列表以节省内存。

    Attributes:
        weapons: 候选武器列表
        equipment_catalog: 装备目录（按槽位分类）
        total_combinations: 总组合数
        pruned_weapon_count: 被剪枝的武器数量
        warnings: 警告信息
        fixed_loadout: 固定配装选择配置
    """

    weapons: tuple[WeaponCandidate, ...]
    equipment_catalog: dict[str, list[dict]]
    total_combinations: int
    pruned_weapon_count: int
    warnings: tuple[str, ...]
    fixed_loadout: FixedLoadoutSelection


def _resolve_config_fixed_loadout(
    config: OptimizerConfig,
    equipment_catalog: dict[str, list[dict]],
) -> FixedLoadoutSelection:
    """解析配置中的固定配装选择。

    优先使用 fixed_loadout，若未设置则使用 varying_slot_count 生成。

    Args:
        config: 搜索配置
        equipment_catalog: 装备目录

    Returns:
        FixedLoadoutSelection 对象
    """
    if config.varying_slot_count is not None:
        return selection_from_legacy_slot_count(equipment_catalog, config.varying_slot_count)
    return config.fixed_loadout


def count_loadout_combinations(
    equipment_catalog: dict[str, list[dict]],
    *,
    allow_duplicate_accessory: bool = True,
    selection: Optional[FixedLoadoutSelection] = None,
    varying_slot_count: Optional[int] = None,
) -> int:
    """统计配装组合数。

    计算给定装备目录下的四格配装组合总数，与迭代器生成逻辑一致。

    Args:
        equipment_catalog: 装备目录（chest/gloves/accessories）
        allow_duplicate_accessory: 是否允许两个饰品槽装备相同装备
        selection: 固定配装选择（控制哪些槽位固定）
        varying_slot_count: 可变槽位数（遗留参数）

    Returns:
        组合总数
    """
    if not equipment_catalog.get("chest") or not equipment_catalog.get("gloves"):
        return 0
    if not equipment_catalog.get("accessories"):
        return 0
    if selection is None:
        if varying_slot_count is None:
            varying_slot_count = 4
        selection = selection_from_legacy_slot_count(equipment_catalog, varying_slot_count)
    return count_loadout_combinations_for_selection(
        equipment_catalog,
        selection=selection,
        allow_duplicate_accessory=allow_duplicate_accessory,
    )


def _iter_loadout_combinations(
    equipment_catalog: dict[str, list[dict]],
    *,
    allow_duplicate_accessory: bool,
    fixed_loadout: FixedLoadoutSelection,
) -> Iterator[tuple[dict, dict, dict, dict]]:
    """生成配装组合迭代器。

    根据固定配装选择，生成所有可能的四格配装组合。

    Args:
        equipment_catalog: 装备目录
        allow_duplicate_accessory: 是否允许重复饰品
        fixed_loadout: 固定配装选择

    Yields:
        四格配装元组 (chest, gloves, accessory_a, accessory_b)
    """
    yield from iter_loadout_combinations_for_selection(
        equipment_catalog,
        selection=fixed_loadout,
        allow_duplicate_accessory=allow_duplicate_accessory,
    )


def build_optimizer_search_plan(
    *,
    weapons: list[WeaponCandidate],
    equipment_catalog: dict[str, list[dict]],
    config: OptimizerConfig,
) -> OptimizerSearchPlan:
    """构建搜索计划并计算组合总数（不物化任务列表）。

    执行以下步骤：
    1. 根据候选名称集合过滤武器和装备
    2. 剪枝无益装备（无效果、无属性词条）
    3. 按主/副属性排序装备（可选）
    4. 解析固定配装选择
    5. 计算总组合数

    Args:
        weapons: 候选武器列表
        equipment_catalog: 装备目录
        config: 搜索配置

    Returns:
        OptimizerSearchPlan 对象，包含过滤后的武器、装备目录和组合总数
    """
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

    if config.sort_equipment_by_priority and (
        config.main_attr or config.sub_attr or config.priority_skill_types
    ):
        filtered_catalog = sort_equipment_catalog_by_priority(
            filtered_catalog,
            main_attr=config.main_attr,
            sub_attr=config.sub_attr,
            skill_types=config.priority_skill_types,
        )

    fixed_loadout = _resolve_config_fixed_loadout(config, filtered_catalog)
    loadout_count = 0
    if filtered_catalog.get("chest") and filtered_catalog.get("gloves") and filtered_catalog.get("accessories"):
        loadout_count = count_loadout_combinations_for_selection(
            filtered_catalog,
            selection=fixed_loadout,
            allow_duplicate_accessory=config.allow_duplicate_accessory,
        )
    weapon_count = len(filtered_weapons)
    return OptimizerSearchPlan(
        weapons=tuple(filtered_weapons),
        equipment_catalog=filtered_catalog,
        total_combinations=weapon_count * loadout_count,
        pruned_weapon_count=pruned_weapon_count,
        warnings=tuple(warnings),
        fixed_loadout=fixed_loadout,
    )


def iter_optimizer_tasks(
    plan: OptimizerSearchPlan,
    *,
    allow_duplicate_accessory: bool,
) -> Iterator[OptimizerTask]:
    """按武器 × 配装流式生成任务迭代器。

    流式生成所有 (武器, 四格配装) 任务对，避免一次性物化所有任务导致内存问题。

    Args:
        plan: 搜索计划
        allow_duplicate_accessory: 是否允许重复饰品

    Yields:
        OptimizerTask 元组 (WeaponCandidate, (chest, gloves, accessory_a, accessory_b))
    """
    for weapon in plan.weapons:
        for loadout in _iter_loadout_combinations(
            plan.equipment_catalog,
            allow_duplicate_accessory=allow_duplicate_accessory,
            fixed_loadout=plan.fixed_loadout,
        ):
            yield (weapon, loadout)


def enumerate_optimizer_tasks(
    *,
    base_context: DamageContext,
    weapons: list[WeaponCandidate],
    equipment_catalog: dict[str, list[dict]],
    config: OptimizerConfig,
) -> tuple[Iterator[OptimizerTask], int, int, tuple[str, ...]]:
    """生成搜索任务迭代器与总数（不物化全部任务）。

    Args:
        base_context: 基础伤害上下文
        weapons: 候选武器列表
        equipment_catalog: 装备目录
        config: 搜索配置

    Returns:
        四元组：(任务迭代器, 总组合数, 被剪枝武器数, 警告信息)
    """
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


def optimizer_config_for_character(
    char_data: dict,
    *,
    priority_skill_types: tuple[str, ...],
    fixed_loadout: Optional[FixedLoadoutSelection] = None,
    varying_slot_count: Optional[int] = None,
    top_n: int = 10,
    crit_mode: CritMode = "non_crit",
    allow_duplicate_accessory: bool = True,
    prune_non_beneficial: bool = True,
    warn_on_unfiltered: bool = False,
) -> OptimizerConfig:
    """从角色数据自动生成搜索配置。

    根据角色的主/副属性自动填充配置，启用装备优先级排序。

    Args:
        char_data: 角色数据字典
        priority_skill_types: 优先技能类型
        fixed_loadout: 固定配装选择（可选）
        varying_slot_count: 可变槽位数（可选）
        top_n: 返回前 N 个结果
        crit_mode: 暴击模式
        allow_duplicate_accessory: 是否允许重复饰品
        prune_non_beneficial: 是否剪枝无益装备
        warn_on_unfiltered: 未筛选时是否警告

    Returns:
        OptimizerConfig 对象，已根据角色数据配置好主/副属性
    """
    main_attr, sub_attr = character_ability_attrs(char_data)
    return OptimizerConfig(
        top_n=top_n,
        crit_mode=crit_mode,
        allow_duplicate_accessory=allow_duplicate_accessory,
        prune_non_beneficial=prune_non_beneficial,
        warn_on_unfiltered=warn_on_unfiltered,
        main_attr=main_attr,
        sub_attr=sub_attr,
        priority_skill_types=priority_skill_types,
        sort_equipment_by_priority=True,
        fixed_loadout=fixed_loadout if fixed_loadout is not None else FixedLoadoutSelection(),
        varying_slot_count=varying_slot_count,
    )



def evaluate_task(
    *,
    base_context: DamageContext,
    crit_mode: CritMode,
    task: tuple[WeaponCandidate, tuple[dict, dict, dict, dict]],
    search_eval: Optional[SearchEvalContext] = None,
) -> LoadoutScore:
    """评估单条搜索任务。

    执行流程：
    1. 解析任务 → 构建运行时快照（含最终攻击力和效果）
    2. 构建伤害上下文
    3. 调用伤害引擎计算单段伤害
    4. 返回配装评分

    Args:
        base_context: 基础伤害上下文（技能倍率、敌方属性等）
        crit_mode: 暴击模式
        task: 搜索任务（武器候选 + 四格配装）
        search_eval: 搜索评估上下文（用于全量搜索时重算攻击力）

    Returns:
        LoadoutScore 对象，包含武器名、最终伤害和配装名称
    """
    snapshot = build_runtime_eval_snapshot(
        task=task,
        search_eval=search_eval,
    )
    ctx = DamageContext(
        final_attack=snapshot.final_attack,
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
    result = calculate_single_hit_damage(ctx, effects=list(snapshot.effects), crit_mode=crit_mode)
    return LoadoutScore(
        weapon_name=snapshot.weapon_name,
        final_damage=result.final_damage,
        loadout_names=dict(snapshot.loadout_names),
    )


def build_runtime_eval_snapshot(
    *,
    task: tuple[WeaponCandidate, tuple[dict, dict, dict, dict]],
    search_eval: Optional[SearchEvalContext] = None,
) -> RuntimeEvalSnapshot:
    """将一条任务解析为可复用的运行时快照。

    解析流程：
    1. 从任务中提取武器和四格配装
    2. 构建四格配装运行时结构
    3. 聚合装备词条和套装效果 → DamageEffect + 平铺四维 + 攻击力%
    4. 若提供了 search_eval，按当前等级曲线重算最终攻击力
    5. 返回运行时快照

    Args:
        task: 搜索任务（武器候选 + 四格配装）
        search_eval: 搜索评估上下文（用于全量搜索）

    Returns:
        RuntimeEvalSnapshot 对象
    """
    weapon, (chest, glove, acc_a, acc_b) = task
    # 将 JSON 行转为带解析后效果的运行时四格结构
    loadout = build_four_slot_loadout(
        chest=chest,
        gloves=glove,
        accessory_a=acc_a,
        accessory_b=acc_b,
        allow_duplicate_accessory=True,
    )
    # 属性词条、套装三件套等 → DamageEffect + 平铺四维 + 攻击力%
    equip_effects, flat_stats, atk_percent = aggregate_loadout_modifiers(loadout)
    effects = list(weapon.effects) + equip_effects
    final_attack = weapon.final_attack
    # 全量搜索时按当前等级曲线重算 final_attack（含装备平铺与攻击%）
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
    return RuntimeEvalSnapshot(
        weapon_name=weapon.name,
        final_attack=final_attack,
        effects=tuple(effects),
        loadout_names={
            "chest": chest.get("名称", ""),
            "gloves": glove.get("名称", ""),
            "accessory_a": acc_a.get("名称", ""),
            "accessory_b": acc_b.get("名称", ""),
        },
    )


def _select_top_n(scores: list[LoadoutScore], top_n: int) -> tuple[LoadoutScore, ...]:
    """从评分列表中选择前 N 个最优结果。

    Args:
        scores: 配装评分列表
        top_n: 选择数量

    Returns:
        按伤害降序排列的前 N 个评分元组
    """
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
    """单技能最优配装搜索（串行版）。

    执行完整的搜索流程：
    1. 生成任务迭代器
    2. 遍历所有任务，计算伤害评分
    3. 使用 TopNTracker 维护最优结果
    4. 返回搜索结果汇总

    Args:
        base_context: 基础伤害上下文
        weapons: 候选武器列表
        equipment_catalog: 装备目录
        config: 搜索配置
        task_evaluator: 自定义任务评估器（可选）

    Returns:
        OptimizerResult 对象，包含 Top-N 最优配装和统计信息
    """
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
