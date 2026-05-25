#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""配装最终攻击力求值：GUI 乘区快照与全量搜索共用 seam。"""

from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence

from calculation.multiplicative_zones.final_attack_zone import calculate_final_attack_with_details
from calculation.weapon_skill_selection import WeaponSkillSelection


def final_attack_details_for_loadout(
    *,
    character: Mapping[str, Any],
    weapon: Optional[Mapping[str, Any]],
    char_level: int,
    weapon_level: int,
    trust_level: int = 0,
    weapon_skills: WeaponSkillSelection | None = None,
    weapon_normal_levels: Sequence[int] | None = None,
    weapon_special_states: Sequence[Mapping[str, int]] | None = None,
    skill_calculation_kwargs: Mapping[str, Any] | None = None,
    equipment_stat_bonus: Optional[Mapping[str, float]] = None,
    equipment_attack_percent: float = 0.0,
) -> dict[str, float]:
    """
    统一最终攻击力链入口（右侧乘区与搜索重算共用）。

    ``weapon_skills`` 与 ``weapon_normal_levels``/``weapon_special_states`` 二选一；
    后者会在给定 ``weapon`` 时按 schema 映射为选用状态。
    """
    skill_kwargs: dict[str, Any] = {}
    if skill_calculation_kwargs:
        skill_kwargs = dict(skill_calculation_kwargs)
    elif weapon_skills is not None:
        skill_kwargs = weapon_skills.calculation_kwargs()
    elif weapon is not None and (
        weapon_normal_levels is not None or weapon_special_states is not None
    ):
        skill_kwargs = WeaponSkillSelection.from_preset_view(
            weapon,
            weapon_normal_levels=list(weapon_normal_levels or ()),
            weapon_special_states=list(weapon_special_states or ()),
        ).calculation_kwargs()

    return calculate_final_attack_with_details(
        character=dict(character),
        weapon=dict(weapon) if weapon is not None else None,
        char_level=int(char_level),
        weapon_level=int(weapon_level),
        trust_level=int(trust_level),
        equipment_stat_bonus=dict(equipment_stat_bonus or {}),
        equipment_attack_percent=float(equipment_attack_percent),
        **skill_kwargs,
    )
