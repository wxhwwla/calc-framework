# SPDX-License-Identifier: AGPL-3.0
"""Web 配装请求体（预览/快照/预设共用）。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class EnemyParamsBody(BaseModel):
    enemy_defense: float = 100.0
    enemy_resistance: float = 0.0
    ignore_resistance: float = 0.0
    imbalance_vulnerability_coeff: float = 1.3
    is_unbalanced: bool = False
    is_true_damage: bool = False
    enemy_tier: str = "普通"
    combo_stacks: int = 0
    break_defense_stacks: int = 0
    attached_effect_multiplier: float = 1.0
    corrosion_duration_seconds: float = 15.0
    imbalance_efficiency_bonus: float = 0.0


class WebLoadoutBody(BaseModel):
    char_data: dict[str, Any]
    weapon_data: dict[str, Any]
    char_level: int = 90
    weapon_level: int = 90
    trust_level: int = 0
    skill_1_level: int = 8
    skill_2_level: int = 8
    skill_3_level: int = 8
    weapon_scope_label: str = "当前武器"
    equipment_scope_label: str = "全部装备"
    weapon_skill_values: dict[str, Any] = Field(default_factory=dict)
    use_manual_multi_skill_counts: bool = False
    manual_counts: dict[str, int] = Field(default_factory=dict)
    physical_abnormal_counts: dict[str, int] = Field(default_factory=dict)
    spell_abnormal_counts: dict[str, int] = Field(default_factory=dict)
    damage_component_mode: str = "skill_and_abnormal"
    use_expected_crit: bool = False
    include_conditional_equipment_crit: bool = False
    extra_crit_rate: float = 0.0
    extra_crit_damage: float = 0.0
    enemy_params: EnemyParamsBody = Field(default_factory=EnemyParamsBody)
    fixed_loadout: dict[str, Any] | None = None
    fixed_equipment_names: dict[str, str | None] = Field(default_factory=dict)
    manual_buffs: dict[str, list[dict[str, str | float]]] = Field(default_factory=dict)
    equipment_catalog: dict[str, list[dict[str, Any]]] | None = None
    calculation_mode: str | None = None
    calc_mode: str | None = None

    def to_loadout_dict(self) -> dict[str, Any]:
        data = self.model_dump()
        enemy = data.pop("enemy_params", {})
        data.update(enemy)
        return data
