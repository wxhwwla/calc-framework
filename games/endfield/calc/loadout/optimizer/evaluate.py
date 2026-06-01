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

from __future__ import annotations

from games.endfield.calc.damage.engine import CritMode, DamageContext, calculate_single_hit_damage
from games.endfield.calc.damage.originium_arts import sum_originium_arts_strength
from games.endfield.calc.equipment.affix import aggregate_loadout_modifiers
from games.endfield.calc.equipment.system import build_four_slot_loadout
from games.endfield.calc.loadout.attack_eval import final_attack_details_for_loadout
from games.endfield.calc.search.evaluate.context import SearchEvalContext

from .types import LoadoutScore, RuntimeEvalSnapshot, WeaponCandidate


def evaluate_task(
    *,
    base_context: DamageContext,
    crit_mode: CritMode,
    task: tuple[WeaponCandidate, tuple[dict, dict, dict, dict]],
    search_eval: SearchEvalContext | None = None,
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
        combo_stacks=base_context.combo_stacks,
        break_defense_stacks=base_context.break_defense_stacks,
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
    search_eval: SearchEvalContext | None = None,
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
            details = final_attack_details_for_loadout(
                character=search_eval.char_data,
                weapon=weapon_data,
                char_level=search_eval.char_level,
                weapon_level=search_eval.weapon_level,
                trust_level=search_eval.trust_level,
                weapon_normal_levels=list(search_eval.weapon_normal_levels),
                weapon_special_states=list(search_eval.weapon_special_states),
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
        originium_arts_strength=sum_originium_arts_strength(flat_stats),
    )
