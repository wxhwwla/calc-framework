#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按搜索作业选择单技能或多技能加权评估器。"""

from __future__ import annotations

from typing import Callable, Optional

from calculation.damage_engine import CritMode
from calculation.loadout_optimizer import LoadoutScore, OptimizerTask, evaluate_task
from calculation.multi_skill_optimizer import evaluate_multi_skill_task
from calculation.search_eval_context import SearchEvalContext
from calculation.single_skill_search_job import SingleSkillSearchJob


def make_loadout_task_evaluator(
    job: SingleSkillSearchJob,
    *,
    crit_mode: CritMode,
    search_eval: Optional[SearchEvalContext] = None,
) -> Callable[[OptimizerTask], LoadoutScore]:
    """根据作业是否含多技能配置返回对应 evaluate 闭包。"""
    multi = job.multi_skill_eval
    if multi is None:
        return lambda task: evaluate_task(
            base_context=job.base_context,
            crit_mode=crit_mode,
            task=task,
            search_eval=search_eval,
        )
    scenarios = multi.scenarios
    counts = multi.skill_counts
    return lambda task: evaluate_multi_skill_task(
        shared_context=job.base_context,
        crit_mode=crit_mode,
        task=task,
        scenarios=scenarios,
        skill_counts=counts,
        search_eval=search_eval,
    )
