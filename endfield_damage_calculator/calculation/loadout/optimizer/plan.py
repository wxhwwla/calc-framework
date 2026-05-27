#!/usr/bin/env python3
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

from calculation.equipment.prune import sort_equipment_catalog_by_priority
from calculation.loadout.slot_search import (
    count_loadout_combinations_for_selection,
)

from .catalog import (
    _apply_equipment_filter,
    _is_equipment_beneficial,
    _resolve_config_fixed_loadout,
)
from .types import OptimizerConfig, OptimizerSearchPlan, WeaponCandidate


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
    if config.warn_on_unfiltered and not config.candidate_weapon_names and not config.candidate_equipment_names:
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

    if config.sort_equipment_by_priority and (config.main_attr or config.sub_attr or config.priority_skill_types):
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
