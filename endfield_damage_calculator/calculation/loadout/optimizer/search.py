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

from calculation.core.top_n_tracker import TopNTracker

from calculation.damage.engine import CritMode, DamageContext, DamageEffect, calculate_single_hit_damage
from calculation.equipment.affix import aggregate_loadout_modifiers
from calculation.equipment.system import build_four_slot_loadout, collect_loadout_effects
from calculation.loadout.attack_eval import final_attack_details_for_loadout
from calculation.equipment.prune import character_ability_attrs, sort_equipment_catalog_by_priority
from calculation.loadout.slot_search import (
    FixedLoadoutSelection,
    VaryingSlotMask,
    baseline_loadout_from_catalog,
    count_loadout_combinations_for_selection,
    iter_loadout_combinations_for_mask,
    iter_loadout_combinations_for_selection,
    selection_from_legacy_slot_count,
)
from calculation.search.evaluate.context import SearchEvalContext

from .evaluate import evaluate_task
from .plan import build_optimizer_search_plan
from .tasks import OptimizerTask, enumerate_optimizer_tasks, optimizer_config_for_character
from .types import LoadoutScore, OptimizerConfig, OptimizerResult, WeaponCandidate



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
