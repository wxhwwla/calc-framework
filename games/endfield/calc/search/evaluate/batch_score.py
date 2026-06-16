#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""Web 浏览器本地搜索 — 批量配装评分（含异常 / compose_damage_total parity）。"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from games.endfield.calc.damage.engine import CritMode
from games.endfield.calc.loadout.optimizer import WeaponCandidate
from games.endfield.calc.search.evaluate.context import SearchEvalContext
from games.endfield.calc.search.evaluate.task import make_loadout_task_evaluator
from games.endfield.calc.search.plan.job import SingleSkillSearchJob

OptimizerTask = tuple[WeaponCandidate, tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]]


def _index_equipment(catalog: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    by_name: dict[str, dict[str, Any]] = {}
    for items in catalog.values():
        for item in items:
            name = str(item.get("名称", ""))
            if name:
                by_name[name] = item
    return by_name


def _equipment_or_stub(by_name: dict[str, dict[str, Any]], name: str) -> dict[str, Any]:
    return by_name.get(name) or {"名称": name, "效果": [], "三件套效果": [], "属性词条": []}


def search_eval_from_job(job: SingleSkillSearchJob) -> SearchEvalContext:
    """从搜索作业构建 SearchEvalContext（与 MVP 续跑路径一致）。"""
    return SearchEvalContext(
        char_data=job.char_data,
        char_level=job.char_level,
        weapon_level=job.weapon_level,
        trust_level=job.trust_level,
        weapon_data_by_name=job.weapon_data_by_name,
        damage_component_mode=job.damage_component_mode,
        use_expected_crit=job.use_expected_crit,
        include_conditional_equipment_crit=job.include_conditional_equipment_crit,
        extra_crit_rate=job.extra_crit_rate,
        extra_crit_damage=job.extra_crit_damage,
        physical_abnormal_counts=dict(job.physical_abnormal_counts or {}),
        spell_abnormal_counts=dict(job.spell_abnormal_counts or {}),
        weapon_normal_levels=tuple(job.weapon_normal_levels),
        weapon_special_states=tuple(dict(s) for s in job.weapon_special_states),
    )


def score_search_loadouts_batch(
    *,
    job: SingleSkillSearchJob,
    loadouts: Sequence[Mapping[str, str]],
    crit_mode: CritMode = "non_crit",
) -> list[float]:
    """对多条配装组合返回与桌面搜索一致的 ``final_damage``。"""
    weapon_by_name = {w.name: w for w in job.weapon_candidates}
    equip_by_name = _index_equipment(dict(job.equipment_catalog))
    search_eval = search_eval_from_job(job)
    evaluator = make_loadout_task_evaluator(job, crit_mode=crit_mode, search_eval=search_eval)
    scores: list[float] = []
    for row in loadouts:
        weapon = weapon_by_name.get(str(row.get("weapon_name", "")))
        if weapon is None:
            scores.append(0.0)
            continue
        task: OptimizerTask = (
            weapon,
            (
                _equipment_or_stub(equip_by_name, str(row.get("chest", ""))),
                _equipment_or_stub(equip_by_name, str(row.get("gloves", ""))),
                _equipment_or_stub(equip_by_name, str(row.get("accessory_a", ""))),
                _equipment_or_stub(equip_by_name, str(row.get("accessory_b", ""))),
            ),
        )
        scores.append(float(evaluator(task).final_damage))
    return scores
