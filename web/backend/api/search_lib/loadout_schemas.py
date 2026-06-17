# SPDX-License-Identifier: AGPL-3.0
"""Web 配装请求体（预览/快照/预设共用）。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator


class EnemyParamsBody(BaseModel):
    """敌方参数子模型。"""

    enemy_defense: float = Field(default=100.0, description="敌方防御力")
    enemy_resistance: float = Field(default=0.0, description="敌方抗性")
    ignore_resistance: float = Field(default=0.0, description="忽略抗性")
    imbalance_vulnerability_coeff: float = Field(default=1.3, description="失衡易伤系数")
    is_unbalanced: bool = Field(default=False, description="是否失衡")
    is_true_damage: bool = Field(default=False, description="是否真实伤害")
    enemy_tier: str = Field(default="普通", description="敌方等级")
    combo_stacks: int = Field(default=0, description="连击层数")
    break_defense_stacks: int = Field(default=0, description="破防层数")
    attached_effect_multiplier: float = Field(default=1.0, description="附着效果倍率")
    corrosion_duration_seconds: float = Field(default=15.0, description="侵蚀持续时间（秒）")
    imbalance_efficiency_bonus: float = Field(default=0.0, description="失衡效率加成")


class WebLoadoutBody(BaseModel):
    """Web 配装请求体基类（预览 / 快照 / 预设共用）。"""

    char_data: dict[str, Any] = Field(description="角色数据")
    weapon_data: dict[str, Any] = Field(description="武器数据")
    char_level: int = Field(default=90, description="角色等级")
    weapon_level: int = Field(default=90, description="武器等级")
    trust_level: int = Field(default=0, description="信赖等级")
    skill_1_level: int = Field(default=8, description="技能 1 等级")
    skill_2_level: int = Field(default=8, description="技能 2 等级")
    skill_3_level: int = Field(default=8, description="技能 3 等级")
    weapon_scope_label: str = Field(default="当前武器", description="武器搜索范围标签")
    equipment_scope_label: str = Field(default="全部装备", description="装备搜索范围标签")
    weapon_skill_values: dict[str, Any] = Field(default_factory=dict, description="武器技能值")
    use_manual_multi_skill_counts: bool = Field(default=False, description="是否手动指定多段技能计数")
    manual_counts: dict[str, int] = Field(default_factory=dict, description="手动技能计数")
    physical_abnormal_counts: dict[str, int] = Field(default_factory=dict, description="物理异常状态层数")
    spell_abnormal_counts: dict[str, int] = Field(default_factory=dict, description="法术异常状态层数")
    damage_component_mode: str = Field(default="skill_and_abnormal", description="伤害组件模式")
    use_expected_crit: bool = Field(default=False, description="是否使用期望暴击")
    include_conditional_equipment_crit: bool = Field(default=False, description="是否计入条件触发暴击")
    extra_crit_rate: float = Field(default=0.0, description="额外暴击率")
    extra_crit_damage: float = Field(default=0.0, description="额外暴击伤害")
    enemy_params: EnemyParamsBody = Field(default_factory=EnemyParamsBody, description="敌方参数")
    fixed_loadout: dict[str, Any] | None = Field(default=None, description="固定配装字段")
    fixed_equipment_names: dict[str, str | None] = Field(default_factory=dict, description="固定装备名称")
    manual_buffs: dict[str, list[dict[str, str | float]]] = Field(default_factory=dict, description="手动增伤")
    equipment_catalog: dict[str, list[dict[str, Any]]] | None = Field(default=None, description="装备目录")
    calculation_mode: str | None = Field(default=None, description="计算模式（旧字段）")
    calc_mode: str | None = Field(default=None, description="计算模式")

    @model_validator(mode="after")
    def _materialize_curve_entities(self) -> WebLoadoutBody:
        """含 ``成长参数`` 或仅名称的实体在计算前物化。"""
        from api.search_lib.entity_refs import resolve_character_ref, resolve_weapon_ref

        object.__setattr__(
            self,
            "char_data",
            resolve_character_ref(
                self.char_data,
                char_level=int(self.char_level),
                trust_level=int(self.trust_level),
            ),
        )
        object.__setattr__(
            self,
            "weapon_data",
            resolve_weapon_ref(self.weapon_data, weapon_level=int(self.weapon_level)),
        )
        return self

    def to_loadout_dict(self) -> dict[str, Any]:
        """将 enemy_params 展开到顶层，返回 LoadoutState 兼容字典。"""
        data = self.model_dump()
        enemy = data.pop("enemy_params", {})
        data.update(enemy)
        return data


__all__: list[str] = []
