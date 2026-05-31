#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""
全量遍历搜索编排（无 GUI 依赖）。

统一「组装 job / OptimizerConfig / 预估」接缝，避免 GUI 与 runner 各写一份逻辑。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from games.endfield.calc.loadout.optimizer import OptimizerConfig, optimizer_config_for_character
from games.endfield.calc.loadout.slot_search import FixedLoadoutSelection

from ..evaluate.multi_skill import build_multi_skill_search_eval
from .job import SingleSkillSearchJob, prepare_single_skill_search_job


@dataclass(frozen=True)
class SearchJobInputs:
    """从 GUI 或测试传入的搜索作业输入（不含 Tk）。"""

    char_data: dict[str, Any]
    char_level: int
    weapon_level: int
    trust_level: int
    skill_name: str
    skill_type: str
    skill_multiplier: float
    damage_type: str
    weapon_scope_label: str
    equipment_scope_label: str
    all_weapons: list[dict[str, Any]]
    current_weapon: dict[str, Any]
    equipment_catalog: dict[str, list[dict[str, Any]]]
    fixed_loadout: FixedLoadoutSelection
    enemy_defense: float = 100.0
    use_manual_multi_skill_counts: bool = False
    skill_1_level: int = 0
    skill_2_level: int = 0
    skill_3_level: int = 0
    manual_counts: dict[str, int] | None = None
    physical_abnormal_counts: dict[str, int] | None = None
    spell_abnormal_counts: dict[str, int] | None = None
    damage_component_mode: str = "skill_and_abnormal"
    use_expected_crit: bool = False
    include_conditional_equipment_crit: bool = False
    extra_crit_rate: float = 0.0
    extra_crit_damage: float = 0.0
    weapon_normal_levels: list[int] | None = None
    weapon_special_states: list[dict[str, int]] | None = None


def prepare_search_job(
    inputs: SearchJobInputs,
) -> tuple[SingleSkillSearchJob | None, str | None]:
    """
    组装全量搜索作业（预估与实跑共用）。

    开启手动次数时附带 multi_skill_eval，与确认路径的加权总伤语义一致。
    """
    multi_skill_eval = None
    if inputs.use_manual_multi_skill_counts:
        counts = inputs.manual_counts or {}
        multi_skill_eval, err = build_multi_skill_search_eval(
            inputs.char_data,
            skill_1_level=inputs.skill_1_level,
            skill_2_level=inputs.skill_2_level,
            skill_3_level=inputs.skill_3_level,
            manual_counts=counts,
        )
        if err:
            return None, err

    return prepare_single_skill_search_job(
        char_data=inputs.char_data,
        char_level=inputs.char_level,
        weapon_level=inputs.weapon_level,
        trust_level=inputs.trust_level,
        skill_name=inputs.skill_name,
        skill_type=inputs.skill_type,
        skill_multiplier=inputs.skill_multiplier,
        damage_type=inputs.damage_type,
        weapon_scope_label=inputs.weapon_scope_label,
        equipment_scope_label=inputs.equipment_scope_label,
        all_weapons=inputs.all_weapons,
        current_weapon=inputs.current_weapon,
        equipment_catalog=inputs.equipment_catalog,
        fixed_loadout=inputs.fixed_loadout,
        multi_skill_eval=multi_skill_eval,
        enemy_defense=float(inputs.enemy_defense),
        physical_abnormal_counts=dict(inputs.physical_abnormal_counts or {}),
        spell_abnormal_counts=dict(inputs.spell_abnormal_counts or {}),
        damage_component_mode=inputs.damage_component_mode,
        use_expected_crit=bool(inputs.use_expected_crit),
        include_conditional_equipment_crit=bool(inputs.include_conditional_equipment_crit),
        extra_crit_rate=float(inputs.extra_crit_rate),
        extra_crit_damage=float(inputs.extra_crit_damage),
        weapon_normal_levels=list(inputs.weapon_normal_levels or []),
        weapon_special_states=list(inputs.weapon_special_states or []),
    )


def optimizer_config_for_search_job(
    job: SingleSkillSearchJob,
    *,
    top_n: int,
) -> OptimizerConfig:
    """由已组装的 job 生成与 estimate / MVP / 全量实跑一致的 OptimizerConfig。"""
    if job.multi_skill_eval is not None:
        priority_types = job.multi_skill_eval.priority_skill_types
    else:
        priority_types = (str(job.base_context.skill_type or job.skill_label),)
    crit_mode = "expected" if bool(job.use_expected_crit) else "non_crit"
    return optimizer_config_for_character(
        job.char_data,
        priority_skill_types=priority_types,
        fixed_loadout=job.fixed_loadout,
        top_n=int(top_n),
        crit_mode=crit_mode,  # type: ignore[arg-type]
        allow_duplicate_accessory=True,
        prune_non_beneficial=True,
        warn_on_unfiltered=False,
    )
