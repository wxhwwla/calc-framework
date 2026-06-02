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

from __future__ import annotationsfrom collections.abc import Iteratorfrom games.endfield.calc.loadout.slot_search import (    FixedLoadoutSelection,    count_loadout_combinations_for_selection,    iter_loadout_combinations_for_selection,    selection_from_legacy_slot_count,)from .types import OptimizerConfigdef _is_equipment_beneficial(item: dict) -> bool:
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


def _apply_equipment_filter(items: list[dict], candidate_names: set[str] | None) -> list[dict]:
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
    selection: FixedLoadoutSelection | None = None,
    varying_slot_count: int | None = None,
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
