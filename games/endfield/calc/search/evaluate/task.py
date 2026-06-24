#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""按搜索作业选择单技能或多技能加权评估器。"""

from __future__ import annotations

from collections.abc import Callable

from games.endfield.calc.damage.engine import CritMode, DamageContext
from games.endfield.calc.loadout.optimizer import (
    LoadoutScore,
    OptimizerTask,
    build_runtime_eval_snapshot,
    evaluate_task,
)
from games.endfield.calc.manual_buff.physical import (
    PhysicalAbnormalProfile,
    compose_damage_total,
    evaluate_physical_abnormal_total,
    extract_equipment_crit_bonus,
    extract_weapon_crit_bonus,
)
from games.endfield.calc.manual_buff.spell import evaluate_spell_abnormal_total
from games.endfield.calc.multi_skill.optimizer import evaluate_multi_skill_task

from ..plan.job import SingleSkillSearchJob
from .context import SearchEvalContext


def _context_with_expected_crit(
    base: DamageContext,
    *,
    crit_rate: float,
    crit_damage: float,
) -> DamageContext:
    """创建暴击期望模式下的伤害上下文（覆盖暴击率/伤害）。"""
    return DamageContext(
        final_attack=base.final_attack,
        skill_multiplier=base.skill_multiplier,
        damage_type=base.damage_type,
        skill_type=base.skill_type,
        is_unbalanced=base.is_unbalanced,
        is_true_damage=base.is_true_damage,
        enemy_defense=base.enemy_defense,
        enemy_resistance=base.enemy_resistance,
        ignore_resistance=base.ignore_resistance,
        imbalance_vulnerability_coeff=base.imbalance_vulnerability_coeff,
        crit_rate=float(crit_rate),
        crit_damage=float(crit_damage),
        damage_type_bonus=base.damage_type_bonus,
        skill_type_bonus=base.skill_type_bonus,
        imbalance_damage_bonus=base.imbalance_damage_bonus,
        other_damage_bonus=base.other_damage_bonus,
        combo_stacks=base.combo_stacks,
        break_defense_stacks=base.break_defense_stacks,
    )


def _build_profile(
    job: SingleSkillSearchJob,
    search_eval: SearchEvalContext | None,
) -> PhysicalAbnormalProfile:
    """从作业或搜索上下文构建物理异常 Profile。"""
    if search_eval is None:
        return PhysicalAbnormalProfile(
            damage_component_mode=job.damage_component_mode,
            use_expected_crit=job.use_expected_crit,
            include_conditional_equipment_crit=job.include_conditional_equipment_crit,
            extra_crit_rate=job.extra_crit_rate,
            extra_crit_damage=job.extra_crit_damage,
            counts=dict(job.physical_abnormal_counts or {}),
        )
    return PhysicalAbnormalProfile(
        damage_component_mode=search_eval.damage_component_mode or job.damage_component_mode,
        use_expected_crit=bool(search_eval.use_expected_crit or job.use_expected_crit),
        include_conditional_equipment_crit=bool(
            search_eval.include_conditional_equipment_crit or job.include_conditional_equipment_crit
        ),
        extra_crit_rate=float(search_eval.extra_crit_rate or job.extra_crit_rate),
        extra_crit_damage=float(search_eval.extra_crit_damage or job.extra_crit_damage),
        counts=dict(search_eval.physical_abnormal_counts or job.physical_abnormal_counts or {}),
    )


def _expected_crit_context(
    *,
    job: SingleSkillSearchJob,
    task: OptimizerTask,
    profile: PhysicalAbnormalProfile,
    search_eval: SearchEvalContext | None,
) -> tuple[float, float]:
    """计算期望暴击模式下的暴击率和暴击伤害（含装备和武器暴击加成）。"""
    if not profile.use_expected_crit:
        return job.base_context.crit_rate, job.base_context.crit_damage
    rate = float(job.base_context.crit_rate) + float(profile.extra_crit_rate)
    dmg = float(job.base_context.crit_damage) + float(profile.extra_crit_damage)
    weapon, _ = task
    if search_eval is not None:
        weapon_data = search_eval.weapon_data_by_name.get(weapon.name)
        wr, wd = extract_weapon_crit_bonus(weapon_data, weapon_level=search_eval.weapon_level)
        rate += wr
        dmg += wd
    snapshot = build_runtime_eval_snapshot(task=task, search_eval=search_eval)
    er, ed = extract_equipment_crit_bonus(
        list(snapshot.effects),
        include_conditional=profile.include_conditional_equipment_crit,
    )
    rate += er
    dmg += ed
    return max(0.0, rate), max(0.0, dmg)


def _evaluate_abnormal_damage(
    *,
    job: SingleSkillSearchJob,
    task: OptimizerTask,
    profile: PhysicalAbnormalProfile,
    search_eval: SearchEvalContext | None,
) -> tuple[float, dict[str, float]]:
    """评估物理异常 + 法术异常总伤害。"""
    physical_counts = profile.counts or {}
    spell_counts = (
        dict(search_eval.spell_abnormal_counts or job.spell_abnormal_counts or {})
        if search_eval is not None
        else dict(job.spell_abnormal_counts or {})
    )
    if not any(v > 0 for v in physical_counts.values()) and not any(v > 0 for v in spell_counts.values()):
        return 0.0, {}
    snapshot = build_runtime_eval_snapshot(task=task, search_eval=search_eval)
    char_level = max(1, int(search_eval.char_level)) if search_eval else 1
    crit_rate, crit_damage = _expected_crit_context(
        job=job,
        task=task,
        profile=profile,
        search_eval=search_eval,
    )
    crit_mode: CritMode = "expected" if profile.use_expected_crit else "non_crit"
    physical_total, physical_breakdown = evaluate_physical_abnormal_total(
        context=DamageContext(
            final_attack=float(snapshot.final_attack),
            skill_multiplier=1.0,
            damage_type="物理",
            skill_type="异常",
            is_unbalanced=job.base_context.is_unbalanced,
            is_true_damage=job.base_context.is_true_damage,
            enemy_defense=job.base_context.enemy_defense,
            enemy_resistance=job.base_context.enemy_resistance,
            ignore_resistance=job.base_context.ignore_resistance,
            imbalance_vulnerability_coeff=job.base_context.imbalance_vulnerability_coeff,
            crit_rate=float(crit_rate),
            crit_damage=float(crit_damage),
            damage_type_bonus=job.base_context.damage_type_bonus,
            skill_type_bonus=0.0,
            imbalance_damage_bonus=job.base_context.imbalance_damage_bonus,
            other_damage_bonus=job.base_context.other_damage_bonus,
            combo_stacks=job.base_context.combo_stacks,
            break_defense_stacks=job.base_context.break_defense_stacks,
        ),
        crit_mode=crit_mode,
        effects=list(snapshot.effects),
        counts=physical_counts,
        char_level=char_level,
        originium_arts_strength=float(snapshot.originium_arts_strength),
        attached_effect_multiplier=float(job.attached_effect_multiplier),
    )
    spell_total, spell_breakdown = evaluate_spell_abnormal_total(
        context=DamageContext(
            final_attack=float(snapshot.final_attack),
            skill_multiplier=1.0,
            damage_type="法术-灼热",
            skill_type="异常",
            is_unbalanced=job.base_context.is_unbalanced,
            is_true_damage=job.base_context.is_true_damage,
            enemy_defense=job.base_context.enemy_defense,
            enemy_resistance=job.base_context.enemy_resistance,
            ignore_resistance=job.base_context.ignore_resistance,
            imbalance_vulnerability_coeff=job.base_context.imbalance_vulnerability_coeff,
            crit_rate=float(crit_rate),
            crit_damage=float(crit_damage),
            damage_type_bonus=job.base_context.damage_type_bonus,
            skill_type_bonus=0.0,
            imbalance_damage_bonus=job.base_context.imbalance_damage_bonus,
            other_damage_bonus=job.base_context.other_damage_bonus,
            combo_stacks=job.base_context.combo_stacks,
            break_defense_stacks=job.base_context.break_defense_stacks,
        ),
        crit_mode=crit_mode,
        effects=list(snapshot.effects),
        counts=spell_counts,
        char_level=char_level,
        originium_arts_strength=float(snapshot.originium_arts_strength),
        attached_effect_multiplier=float(job.attached_effect_multiplier),
        corrosion_duration_seconds=float(job.corrosion_duration_seconds),
    )
    merged = dict(physical_breakdown)
    merged.update(spell_breakdown)
    return physical_total + spell_total, merged


def make_loadout_task_evaluator(
    job: SingleSkillSearchJob,
    *,
    crit_mode: CritMode,
    search_eval: SearchEvalContext | None = None,
) -> Callable[[OptimizerTask], LoadoutScore]:
    """根据作业是否含多技能配置返回对应 evaluate 闭包。

    Args:
        job: 单技能搜索作业
        crit_mode: 暴击模式
        search_eval: 搜索评估上下文（可选）

    Returns:
        接收 OptimizerTask 返回 LoadoutScore 的评估函数
    """
    profile = _build_profile(job, search_eval)
    component_mode = profile.damage_component_mode
    multi = job.multi_skill_eval
    if multi is None:

        def _eval_single(task: OptimizerTask) -> LoadoutScore:
            """单技能评估闭包。"""
            eval_context = job.base_context
            eval_crit_mode = crit_mode
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
            base_score = evaluate_task(
                base_context=eval_context,
                crit_mode=eval_crit_mode,
                task=task,
                search_eval=search_eval,
            )
            abnormal_total, abnormal_breakdown = _evaluate_abnormal_damage(
                job=job,
                task=task,
                profile=profile,
                search_eval=search_eval,
            )
            total = compose_damage_total(
                skill_damage=base_score.final_damage,
                abnormal_damage=abnormal_total,
                mode=component_mode,
            )
            breakdown = dict(abnormal_breakdown)
            if base_score.segment_breakdown:
                breakdown.update(base_score.segment_breakdown)
            return LoadoutScore(
                weapon_name=base_score.weapon_name,
                final_damage=total,
                loadout_names=base_score.loadout_names,
                segment_breakdown=breakdown or None,
            )

        return _eval_single
    scenarios = multi.scenarios
    counts = multi.skill_counts

    def _eval_multi(task: OptimizerTask) -> LoadoutScore:
        """多技能加权评估闭包。"""
        eval_context = job.base_context
        eval_crit_mode = crit_mode
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
        base_score = evaluate_multi_skill_task(
            shared_context=eval_context,
            crit_mode=eval_crit_mode,
            task=task,
            scenarios=scenarios,
            skill_counts=counts,
            search_eval=search_eval,
        )
        abnormal_total, abnormal_breakdown = _evaluate_abnormal_damage(
            job=job,
            task=task,
            profile=profile,
            search_eval=search_eval,
        )
        total = compose_damage_total(
            skill_damage=base_score.final_damage,
            abnormal_damage=abnormal_total,
            mode=component_mode,
        )
        merged = dict(base_score.segment_breakdown or {})
        merged.update(abnormal_breakdown)
        return LoadoutScore(
            weapon_name=base_score.weapon_name,
            final_damage=total,
            loadout_names=base_score.loadout_names,
            segment_breakdown=merged or None,
        )

    return _eval_multi
