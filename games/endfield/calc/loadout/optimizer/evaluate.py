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

import logging
import threading
from collections import OrderedDict
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)

from utils.frozen_runtime import use_rust_search_accel

# ── 优先使用 Rust 加速版；打包 exe 永不 import rust_bridge ──
if use_rust_search_accel():
    try:
        from extensions.rust_search.python.rust_bridge import evaluate_search_damage as _rs_eval

        evaluate_search_damage = _rs_eval
    except ImportError:
        from games.endfield.calc.dag_adapter.search_evaluate import evaluate_search_damage
else:
    from games.endfield.calc.dag_adapter.search_evaluate import evaluate_search_damage

from games.endfield.calc.damage.engine import CritMode, DamageContext
from games.endfield.calc.damage.originium_arts import sum_originium_arts_strength
from games.endfield.calc.equipment.affix import aggregate_loadout_modifiers
from games.endfield.calc.equipment.system import build_four_slot_loadout
from games.endfield.calc.loadout.attack_eval import final_attack_details_for_loadout
from games.endfield.calc.search.evaluate.context import SearchEvalContext

from .types import LoadoutScore, RuntimeEvalSnapshot, WeaponCandidate

# ── 装备侧效果缓存（键=四件装备名元组，同一配装不同武器时复用） ──
_loadout_cache: OrderedDict[tuple[str, str, str, str], tuple[list, dict[str, float], float]] = OrderedDict()
_loadout_cache_lock = threading.Lock()
_MAX_LOADOUT_CACHE = 500000  # 增大到 50 万，覆盖所有装备组合

# ── 最终攻击力缓存（键=(武器名, 四件装备名)，避免重复计算 final_attack） ──
_final_attack_cache: OrderedDict[tuple[str, str, str, str, str], float] = OrderedDict()
_MAX_ATTACK_CACHE = 2000000  # 增大到 200 万，覆盖所有组合
_attack_cache_hits = 0
_attack_cache_misses = 0

# ── 单线程模式标志（跳过锁开销） ──
_single_thread_mode = False


def set_single_thread_mode(enabled: bool) -> None:
    """设置单线程模式（跳过锁开销）。"""
    global _single_thread_mode
    _single_thread_mode = enabled
    logger.info("单线程模式: %s", enabled)


def warmup_final_attack_cache(
    *,
    weapons: list[WeaponCandidate],
    equipment_catalog: dict[str, list[dict[str, Any]]],
    search_eval: SearchEvalContext | None = None,
) -> int:
    """预热 final_attack 缓存，消除搜索时的缓存预热开销。

    遍历所有武器+装备组合，预先计算 final_attack 并存入缓存。

    Args:
        weapons: 武器候选列表
        equipment_catalog: 装备目录（按部位分组）
        search_eval: 搜索评估上下文

    Returns:
        预热的缓存条目数
    """
    if search_eval is None:
        return 0

    from games.endfield.calc.equipment.affix import aggregate_loadout_modifiers
    from games.endfield.calc.equipment.system import build_four_slot_loadout

    # 获取装备列表
    chest_list = equipment_catalog.get("chest", [])
    gloves_list = equipment_catalog.get("gloves", [])
    acc_a_list = equipment_catalog.get("accessory_a", [])
    acc_b_list = equipment_catalog.get("accessory_b", [])

    if not chest_list or not gloves_list:
        logger.warning("预热缓存：装备列表为空")
        return 0

    # 限制预热数量（避免内存爆炸）
    max_chest = min(len(chest_list), 100)
    max_gloves = min(len(gloves_list), 100)

    warmed = 0
    for weapon in weapons:
        weapon_data = search_eval.weapon_data_by_name.get(weapon.name)
        if weapon_data is None:
            continue

        for chest in chest_list[:max_chest]:
            for glove in gloves_list[:max_gloves]:
                try:
                    # 构建装备组合
                    loadout = build_four_slot_loadout(
                        chest=chest,
                        gloves=glove,
                        accessory_a=acc_a_list[0] if acc_a_list else {},
                        accessory_b=acc_b_list[0] if acc_b_list else {},
                        allow_duplicate_accessory=True,
                    )
                    _, flat_stats, atk_percent = aggregate_loadout_modifiers(loadout)

                    # 计算 final_attack
                    _ckey = (
                        chest.get("名称", ""),
                        glove.get("名称", ""),
                        acc_a_list[0].get("名称", "") if acc_a_list else "",
                        acc_b_list[0].get("名称", "") if acc_b_list else "",
                    )
                    _akey = (weapon.name, _ckey[0], _ckey[1], _ckey[2], _ckey[3])

                    if _akey not in _final_attack_cache:
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
                        _final_attack_cache[_akey] = float(details["final_attack"])
                        warmed += 1
                except (ValueError, KeyError, TypeError):
                    # 跳过无效的装备组合
                    continue

    logger.info("预热缓存完成: %d 条目", warmed)
    return warmed


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
    2. 调用 DAG 桥接函数计算单段伤害
    3. 返回配装评分

    使用 ``evaluate_search_damage``（DAG 桥接函数）替代原本的本地引擎
    ``calculate_single_hit_damage``，统一走 DAG 框架。

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
    final_damage = evaluate_search_damage(
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
        effects=list(snapshot.effects),
        crit_mode=crit_mode,
    ).final_damage
    return LoadoutScore(
        weapon_name=snapshot.weapon_name,
        final_damage=final_damage,
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
    # 装备侧聚合结果缓存（同一配装不同武器复用，避免重复笛卡尔积级 build+aggregate）
    _ckey = (chest.get("名称", ""), glove.get("名称", ""), acc_a.get("名称", ""), acc_b.get("名称", ""))
    # 单线程模式跳过锁开销
    if _single_thread_mode:
        cached = _loadout_cache.get(_ckey)
        if cached is not None:
            equip_effects, flat_stats, atk_percent = cached
        else:
            loadout = build_four_slot_loadout(
                chest=chest,
                gloves=glove,
                accessory_a=acc_a,
                accessory_b=acc_b,
                allow_duplicate_accessory=True,
            )
            equip_effects, flat_stats, atk_percent = aggregate_loadout_modifiers(loadout)
            if len(_loadout_cache) >= _MAX_LOADOUT_CACHE:
                _loadout_cache.popitem(last=False)
            _loadout_cache[_ckey] = (equip_effects, flat_stats, atk_percent)
    else:
        with _loadout_cache_lock:
            cached = _loadout_cache.get(_ckey)
            if cached is not None:
                equip_effects, flat_stats, atk_percent = cached
            else:
                loadout = build_four_slot_loadout(
                    chest=chest,
                    gloves=glove,
                    accessory_a=acc_a,
                    accessory_b=acc_b,
                    allow_duplicate_accessory=True,
                )
                equip_effects, flat_stats, atk_percent = aggregate_loadout_modifiers(loadout)
                if len(_loadout_cache) >= _MAX_LOADOUT_CACHE:
                    _loadout_cache.popitem(last=False)
                _loadout_cache[_ckey] = (equip_effects, flat_stats, atk_percent)
    effects = list(weapon.effects) + equip_effects
    final_attack = weapon.final_attack
    # 全量搜索时按当前等级曲线重算 final_attack（含装备平铺与攻击%）
    if search_eval is not None:
        global _attack_cache_hits, _attack_cache_misses
        # 检查 final_attack 缓存（键=武器名+四件装备名）
        _akey = (weapon.name, _ckey[0], _ckey[1], _ckey[2], _ckey[3])
        cached_attack = _final_attack_cache.get(_akey)
        if cached_attack is not None:
            final_attack = cached_attack
            _attack_cache_hits += 1
        else:
            _attack_cache_misses += 1
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
                # 缓存结果
                if len(_final_attack_cache) >= _MAX_ATTACK_CACHE:
                    _final_attack_cache.popitem(last=False)
                _final_attack_cache[_akey] = final_attack
        # 每 10000 次输出缓存命中率
        total = _attack_cache_hits + _attack_cache_misses
        if total > 0 and total % 10000 == 0:
            hit_rate = _attack_cache_hits / total * 100
            logger.info("final_attack 缓存命中率: %.1f%% (%d/%d)", hit_rate, _attack_cache_hits, total)
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


OptimizerTask = tuple[WeaponCandidate, tuple[dict, dict, dict, dict]]


def evaluate_task_batch(
    *,
    base_context: DamageContext,
    crit_mode: CritMode,
    search_eval: SearchEvalContext | None = None,
) -> Callable[[list[OptimizerTask]], list[LoadoutScore]]:
    """返回批量化评估闭包（收集 N 个任务 → Rust 批量评估 → 返回 N 个评分）。

    依赖 ``extensions.rust_search.python.rust_bridge.evaluate_search_damage_batch``。
    Rust 扩展不可用时自动降级到逐任务评估；打包 exe 永不走 Rust 批量。
    """
    if not use_rust_search_accel():

        def _py_only_batch(tasks: list[OptimizerTask]) -> list[LoadoutScore]:
            return [
                evaluate_task(
                    base_context=base_context,
                    crit_mode=crit_mode,
                    task=t,
                    search_eval=search_eval,
                )
                for t in tasks
            ]

        return _py_only_batch

    # ── 尝试导入 Rust 批量函数 ──
    try:
        from extensions.rust_search.python.rust_bridge import evaluate_search_damage_batch as _batch_fn
    except ImportError:

        def _fallback_batch(tasks: list[OptimizerTask]) -> list[LoadoutScore]:
            return [
                evaluate_task(
                    base_context=base_context,
                    crit_mode=crit_mode,
                    task=t,
                    search_eval=search_eval,
                )
                for t in tasks
            ]

        return _fallback_batch

    def _batch_eval(tasks: list[OptimizerTask]) -> list[LoadoutScore]:
        """批量处理多个任务：预处理 → Rust 批量 → LoadoutScore。"""
        batch_params: list[dict] = []

        # ── 预处理每个任务（build_runtime_eval_snapshot 带缓存 D） ──
        for task in tasks:
            weapon, (chest, glove, acc_a, acc_b) = task

            # 装备缓存（与 build_runtime_eval_snapshot 一致）
            _ckey = (chest.get("名称", ""), glove.get("名称", ""), acc_a.get("名称", ""), acc_b.get("名称", ""))
            with _loadout_cache_lock:
                cached = _loadout_cache.get(_ckey)
                if cached is not None:
                    equip_effects, flat_stats, atk_percent = cached
                else:
                    loadout = build_four_slot_loadout(
                        chest=chest,
                        gloves=glove,
                        accessory_a=acc_a,
                        accessory_b=acc_b,
                        allow_duplicate_accessory=True,
                    )
                    equip_effects, flat_stats, atk_percent = aggregate_loadout_modifiers(loadout)
                    if len(_loadout_cache) >= _MAX_LOADOUT_CACHE:
                        _loadout_cache.popitem(last=False)
                    _loadout_cache[_ckey] = (equip_effects, flat_stats, atk_percent)

            effects = list(weapon.effects) + equip_effects
            final_attack = weapon.final_attack

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

            batch_params.append(
                {
                    "final_attack": final_attack,
                    "skill_multiplier": base_context.skill_multiplier,
                    "damage_type": base_context.damage_type,
                    "skill_type": base_context.skill_type,
                    "is_unbalanced": base_context.is_unbalanced,
                    "is_true_damage": base_context.is_true_damage,
                    "enemy_defense": base_context.enemy_defense,
                    "enemy_resistance": base_context.enemy_resistance,
                    "ignore_resistance": base_context.ignore_resistance,
                    "imbalance_vulnerability_coeff": base_context.imbalance_vulnerability_coeff,
                    "crit_rate": base_context.crit_rate,
                    "crit_damage": base_context.crit_damage,
                    "damage_type_bonus": base_context.damage_type_bonus,
                    "skill_type_bonus": base_context.skill_type_bonus,
                    "imbalance_damage_bonus": base_context.imbalance_damage_bonus,
                    "other_damage_bonus": base_context.other_damage_bonus,
                    "combo_stacks": base_context.combo_stacks,
                    "break_defense_stacks": base_context.break_defense_stacks,
                    "base_damage_bonus": base_context.base_damage_bonus,
                    "effects": list(effects),
                    "crit_mode": crit_mode,
                    "damage_pipeline": "normal",
                }
            )

        # ── Rust 批量评估 ──
        rs_results = _batch_fn(batch_params)

        # ── 构建 LoadoutScore 结果 ──
        scores: list[LoadoutScore] = []
        for task, fd in zip(tasks, rs_results):
            weapon, (chest, glove, acc_a, acc_b) = task
            scores.append(
                LoadoutScore(
                    weapon_name=weapon.name,
                    final_damage=fd.final_damage if hasattr(fd, "final_damage") else fd,
                    loadout_names={
                        "chest": chest.get("名称", ""),
                        "gloves": glove.get("名称", ""),
                        "accessory_a": acc_a.get("名称", ""),
                        "accessory_b": acc_b.get("名称", ""),
                    },
                )
            )
        return scores

    return _batch_eval
