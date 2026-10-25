#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
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

│    ├── evaluate_search_damage: 计算单段伤害 (DAG 桥接)            │

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

from collections.abc import Iterator

from games.endfield.calc.damage.engine import CritMode, DamageContext
from games.endfield.calc.equipment.prune import character_ability_attrs
from games.endfield.calc.loadout.slot_search import (
    FixedLoadoutSelection,
)

from .catalog import _iter_loadout_combinations
from .plan import build_optimizer_search_plan
from .types import OptimizerConfig, OptimizerSearchPlan, WeaponCandidate

OptimizerTask = tuple[WeaponCandidate, tuple[dict, dict, dict, dict]]

"""搜索任务类型：(武器候选, (胸甲, 手套, 饰品A, 饰品B))"""


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
    fixed_loadout: FixedLoadoutSelection | None = None,
    varying_slot_count: int | None = None,
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
