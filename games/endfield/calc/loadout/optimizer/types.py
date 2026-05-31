#!/usr/bin/env python3
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

from __future__ import annotationsfrom dataclasses import dataclass, fieldfrom games.endfield.calc.damage.engine import CritMode, DamageEffectfrom games.endfield.calc.loadout.slot_search import (    FixedLoadoutSelection,)@dataclass(frozen=True)
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
    candidate_weapon_names: set[str] | None = None
    candidate_equipment_names: set[str] | None = None
    warn_on_unfiltered: bool = True
    fixed_loadout: FixedLoadoutSelection = field(default_factory=FixedLoadoutSelection)
    varying_slot_count: int | None = None


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
    segment_breakdown: dict[str, float] | None = None


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
