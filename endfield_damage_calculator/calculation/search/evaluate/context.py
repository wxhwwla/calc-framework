#!/usr/bin/env python3
"""全量搜索评估上下文（角色/武器/等级，供配装逐条重算面板）。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SearchEvalContext:
    """搜索时按配装重算最终攻击力所需数据。"""

    char_data: dict[str, Any]
    char_level: int
    weapon_level: int
    trust_level: int
    weapon_data_by_name: dict[str, dict[str, Any]]
    damage_component_mode: str = "skill_and_abnormal"
    use_expected_crit: bool = False
    include_conditional_equipment_crit: bool = False
    extra_crit_rate: float = 0.0
    extra_crit_damage: float = 0.0
    physical_abnormal_counts: dict[str, int] | None = None
    spell_abnormal_counts: dict[str, int] | None = None
    weapon_normal_levels: tuple[int, ...] = ()
    weapon_special_states: tuple[dict[str, int], ...] = ()
