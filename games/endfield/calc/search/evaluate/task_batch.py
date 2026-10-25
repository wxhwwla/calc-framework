#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""search_job 路径 Rust 批量评估（摊销 FFI，与 make_loadout_task_evaluator 单技能 parity）。"""

from __future__ import annotations

import importlib.util
from collections.abc import Callable

from utils.frozen_runtime import frozen_use_search_job_batch, use_rust_search_accel

from games.endfield.calc.damage.engine import CritMode
from games.endfield.calc.loadout.optimizer import (
    LoadoutScore,
    OptimizerTask,
    RuntimeEvalSnapshot,
    build_runtime_eval_snapshot,
)
from games.endfield.calc.manual_buff.physical import PhysicalAbnormalProfile, compose_damage_total

from ..plan.job import SingleSkillSearchJob
from .context import SearchEvalContext
from .task import (
    _build_profile,
    _context_with_expected_crit,
    _evaluate_abnormal_damage,
    _expected_crit_context,
    make_loadout_task_evaluator,
)


def _rust_search_importable() -> bool:
    """Rust 扩展是否可导入（不触发 unused import）。"""
    return importlib.util.find_spec("rust_search") is not None


def can_batch_search_job_eval(job: SingleSkillSearchJob) -> bool:
    """是否可对 search_job 单技能路径启用 Rust 批量。"""
    if job.multi_skill_eval is not None:
        return False
    if not frozen_use_search_job_batch() or not use_rust_search_accel():
        return False
    return _rust_search_importable()


def _skill_damage_param(
    *,
    job: SingleSkillSearchJob,
    task: OptimizerTask,
    profile: PhysicalAbnormalProfile,
    search_eval: SearchEvalContext | None,
    crit_mode: CritMode,
) -> tuple[dict, RuntimeEvalSnapshot]:
    """构建与 evaluate_task 一致的单段 Rust 批量参数字典。"""
    eval_context = job.base_context
    eval_crit_mode: CritMode = crit_mode
    if profile.use_expected_crit:
        rate, dmg = _expected_crit_context(
            job=job,
            task=task,
            profile=profile,
            search_eval=search_eval,
        )
        eval_context = _context_with_expected_crit(
            job.base_context,
            crit_rate=rate,
            crit_damage=dmg,
        )
        eval_crit_mode = "expected"
    snapshot = build_runtime_eval_snapshot(task=task, search_eval=search_eval)
    return {
        "final_attack": snapshot.final_attack,
        "skill_multiplier": eval_context.skill_multiplier,
        "damage_type": eval_context.damage_type,
        "skill_type": eval_context.skill_type,
        "is_unbalanced": eval_context.is_unbalanced,
        "is_true_damage": eval_context.is_true_damage,
        "enemy_defense": eval_context.enemy_defense,
        "enemy_resistance": eval_context.enemy_resistance,
        "ignore_resistance": eval_context.ignore_resistance,
        "imbalance_vulnerability_coeff": eval_context.imbalance_vulnerability_coeff,
        "crit_rate": eval_context.crit_rate,
        "crit_damage": eval_context.crit_damage,
        "damage_type_bonus": eval_context.damage_type_bonus,
        "skill_type_bonus": eval_context.skill_type_bonus,
        "imbalance_damage_bonus": eval_context.imbalance_damage_bonus,
        "other_damage_bonus": eval_context.other_damage_bonus,
        "combo_stacks": eval_context.combo_stacks,
        "break_defense_stacks": eval_context.break_defense_stacks,
        "base_damage_bonus": eval_context.base_damage_bonus,
        "effects": list(snapshot.effects),
        "crit_mode": eval_crit_mode,
        "damage_pipeline": "normal",
    }, snapshot


def _build_batch_params(
    *,
    job: SingleSkillSearchJob,
    tasks: list[OptimizerTask],
    profile: PhysicalAbnormalProfile,
    search_eval: SearchEvalContext | None,
    crit_mode: CritMode,
    # 装备效果缓存（跨批次复用）
    equip_effects_cache: dict[tuple[str, str, str, str], tuple] | None = None,
) -> tuple[list[dict], list[RuntimeEvalSnapshot]]:
    """批量构建所有任务的参数和快照。

    优化：
    - 内联 snapshot 构建（减少函数调用开销）
    - 装备效果缓存（相同装备组合直接复用，避免重复 aggregate）
    - 最终攻击力缓存（由 build_runtime_eval_snapshot 内部的 _final_attack_cache 提供）
    """
    from games.endfield.calc.equipment.affix import aggregate_loadout_modifiers
    from games.endfield.calc.equipment.system import build_four_slot_loadout
    from games.endfield.calc.loadout.attack_eval import final_attack_details_for_loadout
    from games.endfield.calc.loadout.optimizer.evaluate import (
        _final_attack_cache,
        _loadout_cache,
        _loadout_cache_lock,
        _single_thread_mode,
    )

    base_context = job.base_context
    use_expected_crit = profile.use_expected_crit
    n = len(tasks)

    # 预计算公共字符串参数（避免每个任务重复构建）
    ctx_damage_type = base_context.damage_type
    ctx_skill_type = base_context.skill_type
    ctx_is_unbalanced = base_context.is_unbalanced
    ctx_is_true_damage = base_context.is_true_damage
    ctx_enemy_defense = base_context.enemy_defense
    ctx_enemy_resistance = base_context.enemy_resistance
    ctx_ignore_resistance = base_context.ignore_resistance
    ctx_imbalance_vulnerability_coeff = base_context.imbalance_vulnerability_coeff
    ctx_crit_rate = base_context.crit_rate
    ctx_crit_damage = base_context.crit_damage
    ctx_damage_type_bonus = base_context.damage_type_bonus
    ctx_skill_type_bonus = base_context.skill_type_bonus
    ctx_imbalance_damage_bonus = base_context.imbalance_damage_bonus
    ctx_other_damage_bonus = base_context.other_damage_bonus
    ctx_combo_stacks = base_context.combo_stacks
    ctx_break_defense_stacks = base_context.break_defense_stacks
    ctx_base_damage_bonus = base_context.base_damage_bonus

    # 预分配列表
    params_list: list[dict] = [None] * n  # type: ignore[list-item]
    snapshots_list: list[RuntimeEvalSnapshot] = [None] * n  # type: ignore[list-item]

    for i, task in enumerate(tasks):
        weapon, (chest, glove, acc_a, acc_b) = task

        # ── 装备侧缓存（与 build_runtime_eval_snapshot 一致，但内联避免函数调用） ──
        _ckey = (chest.get("名称", ""), glove.get("名称", ""), acc_a.get("名称", ""), acc_b.get("名称", ""))

        # 先查装备效果缓存（跨批次复用）
        if equip_effects_cache is not None:
            cached_equip = equip_effects_cache.get(_ckey)
        else:
            cached_equip = None

        if cached_equip is not None:
            equip_effects, flat_stats, atk_percent = cached_equip
            # equip_effects 已经是 tuple（来自缓存）
        else:
            # 查全局缓存
            if _single_thread_mode:
                cached = _loadout_cache.get(_ckey)
            else:
                with _loadout_cache_lock:
                    cached = _loadout_cache.get(_ckey)

            if cached is not None:
                equip_effects_raw, flat_stats, atk_percent = cached
            else:
                loadout = build_four_slot_loadout(
                    chest=chest,
                    gloves=glove,
                    accessory_a=acc_a,
                    accessory_b=acc_b,
                    allow_duplicate_accessory=True,
                )
                equip_effects_raw, flat_stats, atk_percent = aggregate_loadout_modifiers(loadout)
                if _single_thread_mode:
                    if len(_loadout_cache) >= 500000:
                        _loadout_cache.popitem(last=False)
                    _loadout_cache[_ckey] = (equip_effects_raw, flat_stats, atk_percent)
                else:
                    with _loadout_cache_lock:
                        if len(_loadout_cache) >= 500000:
                            _loadout_cache.popitem(last=False)
                        _loadout_cache[_ckey] = (equip_effects_raw, flat_stats, atk_percent)

            # 转为 tuple 以支持拼接（原始缓存保持 list 兼容性）
            equip_effects = tuple(equip_effects_raw) if isinstance(equip_effects_raw, list) else equip_effects_raw

            # 写入装备效果缓存
            if equip_effects_cache is not None:
                equip_effects_cache[_ckey] = (equip_effects, flat_stats, atk_percent)

        # ── 最终攻击力（使用全局缓存） ──
        final_attack = weapon.final_attack
        if search_eval is not None:
            _akey = (weapon.name, _ckey[0], _ckey[1], _ckey[2], _ckey[3])
            cached_attack = _final_attack_cache.get(_akey)
            if cached_attack is not None:
                final_attack = cached_attack
            else:
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
                    if len(_final_attack_cache) >= 2000000:
                        _final_attack_cache.popitem(last=False)
                    _final_attack_cache[_akey] = final_attack

        # ── 构建 effects 元组 ──
        effects = tuple(weapon.effects) + equip_effects

        # ── 创建快照（轻量级，只存储必要数据） ──
        snapshot = RuntimeEvalSnapshot(
            weapon_name=weapon.name,
            final_attack=final_attack,
            effects=effects,
            loadout_names={
                "chest": _ckey[0],
                "gloves": _ckey[1],
                "accessory_a": _ckey[2],
                "accessory_b": _ckey[3],
            },
            originium_arts_strength=0.0,  # 搜索路径不使用此字段
        )
        snapshots_list[i] = snapshot

        # ── 确定评估上下文 ──
        eval_crit_mode: CritMode = crit_mode
        if use_expected_crit:
            rate, dmg = _expected_crit_context(
                job=job,
                task=task,
                profile=profile,
                search_eval=search_eval,
            )
            cr = rate
            cd = dmg
            eval_crit_mode = "expected"
        else:
            cr = ctx_crit_rate
            cd = ctx_crit_damage

        # ── 构建参数字典 ──
        params_list[i] = {
            "final_attack": final_attack,
            "skill_multiplier": base_context.skill_multiplier,
            "damage_type": ctx_damage_type,
            "skill_type": ctx_skill_type,
            "is_unbalanced": ctx_is_unbalanced,
            "is_true_damage": ctx_is_true_damage,
            "enemy_defense": ctx_enemy_defense,
            "enemy_resistance": ctx_enemy_resistance,
            "ignore_resistance": ctx_ignore_resistance,
            "imbalance_vulnerability_coeff": ctx_imbalance_vulnerability_coeff,
            "crit_rate": cr,
            "crit_damage": cd,
            "damage_type_bonus": ctx_damage_type_bonus,
            "skill_type_bonus": ctx_skill_type_bonus,
            "imbalance_damage_bonus": ctx_imbalance_damage_bonus,
            "other_damage_bonus": ctx_other_damage_bonus,
            "combo_stacks": ctx_combo_stacks,
            "break_defense_stacks": ctx_break_defense_stacks,
            "base_damage_bonus": ctx_base_damage_bonus,
            "effects": list(effects),
            "crit_mode": eval_crit_mode,
            "damage_pipeline": "normal",
        }

    return params_list, snapshots_list


def _loadout_names(task: OptimizerTask) -> dict[str, str]:
    _weapon, (chest, glove, acc_a, acc_b) = task
    return {
        "chest": chest.get("名称", ""),
        "gloves": glove.get("名称", ""),
        "accessory_a": acc_a.get("名称", ""),
        "accessory_b": acc_b.get("名称", ""),
    }


def make_loadout_task_evaluator_batch(
    job: SingleSkillSearchJob,
    *,
    crit_mode: CritMode,
    search_eval: SearchEvalContext | None = None,
) -> Callable[[list[OptimizerTask]], list[LoadoutScore]]:
    """返回批量评估闭包；多技能或 Rust 不可用时回退逐条 evaluate。"""
    profile = _build_profile(job, search_eval)
    component_mode = profile.damage_component_mode
    single_eval = make_loadout_task_evaluator(job, crit_mode=crit_mode, search_eval=search_eval)

    if not can_batch_search_job_eval(job):

        def _fallback(tasks: list[OptimizerTask]) -> list[LoadoutScore]:
            return [single_eval(t) for t in tasks]

        return _fallback

    from extensions.rust_search.python.rust_bridge import evaluate_search_batch_soa

    # 预检查：是否有任何异常次数 > 0
    physical_counts = profile.counts or {}
    spell_counts = (
        dict(search_eval.spell_abnormal_counts or job.spell_abnormal_counts or {})
        if search_eval is not None
        else dict(job.spell_abnormal_counts or {})
    )
    has_abnormal = any(v > 0 for v in physical_counts.values()) or any(v > 0 for v in spell_counts.values())

    # 装备效果缓存（跨批次复用，避免重复 aggregate_loadout_modifiers）
    equip_effects_cache: dict[tuple[str, str, str, str], tuple] = {}

    def _batch_eval(tasks: list[OptimizerTask]) -> list[LoadoutScore]:
        if not tasks:
            return []
        # 批量构建参数和快照（内联 snapshot + 装备效果缓存）
        params, snapshots = _build_batch_params(
            job=job,
            tasks=tasks,
            profile=profile,
            search_eval=search_eval,
            crit_mode=crit_mode,
            equip_effects_cache=equip_effects_cache,
        )
        rs_results = evaluate_search_batch_soa(params)
        scores: list[LoadoutScore] = []
        for task, snapshot, rs in zip(tasks, snapshots, rs_results):
            skill_damage = float(rs.final_damage if hasattr(rs, "final_damage") else rs)
            weapon, _slots = task
            # 只在有异常次数时才计算异常伤害
            if has_abnormal:
                abnormal_total, abnormal_breakdown = _evaluate_abnormal_damage(
                    job=job,
                    task=task,
                    profile=profile,
                    search_eval=search_eval,
                    snapshot=snapshot,
                )
            else:
                abnormal_total, abnormal_breakdown = 0.0, {}
            total = compose_damage_total(
                skill_damage=skill_damage,
                abnormal_damage=abnormal_total,
                mode=component_mode,
            )
            scores.append(
                LoadoutScore(
                    weapon_name=weapon.name,
                    final_damage=total,
                    loadout_names=_loadout_names(task),
                    segment_breakdown=abnormal_breakdown or None,
                )
            )
        return scores

    return _batch_eval
