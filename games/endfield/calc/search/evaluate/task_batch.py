#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""search_job 路径 Rust 批量评估（摊销 FFI，与 make_loadout_task_evaluator 单技能 parity）。"""

from __future__ import annotations

import importlib.util
from collections.abc import Callable

from utils.frozen_runtime import frozen_use_search_job_batch, use_rust_search_accel

from games.endfield.calc.damage.engine import CritMode
from games.endfield.calc.loadout.optimizer import LoadoutScore, OptimizerTask, build_runtime_eval_snapshot
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
) -> dict:
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
    }


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

    def _batch_eval(tasks: list[OptimizerTask]) -> list[LoadoutScore]:
        if not tasks:
            return []
        params = [
            _skill_damage_param(
                job=job,
                task=task,
                profile=profile,
                search_eval=search_eval,
                crit_mode=crit_mode,
            )
            for task in tasks
        ]
        rs_results = evaluate_search_batch_soa(params)
        scores: list[LoadoutScore] = []
        for task, rs in zip(tasks, rs_results):
            skill_damage = float(rs.final_damage if hasattr(rs, "final_damage") else rs)
            weapon, _slots = task
            abnormal_total, abnormal_breakdown = _evaluate_abnormal_damage(
                job=job,
                task=task,
                profile=profile,
                search_eval=search_eval,
            )
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
