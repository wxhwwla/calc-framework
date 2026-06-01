# SPDX-License-Identifier: AGPL-3.0
"""敌方参数 → DamageContext 字段的统一接缝（预览/搜索/快照共用）。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EnemyEvalParams:
    """敌方面板/LoadoutState 中与伤害计算相关的字段。"""

    enemy_defense: float = 100.0
    enemy_resistance: float = 0.0
    ignore_resistance: float = 0.0
    imbalance_vulnerability_coeff: float = 1.3
    is_unbalanced: bool = False
    is_true_damage: bool = False
    combo_stacks: int = 0
    break_defense_stacks: int = 0
    attached_effect_multiplier: float = 1.0
    corrosion_duration_seconds: float = 15.0

    @classmethod
    def from_loadout(cls, loadout: Any) -> EnemyEvalParams:
        return cls(
            enemy_defense=float(getattr(loadout, "enemy_defense", 100.0)),
            enemy_resistance=float(getattr(loadout, "enemy_resistance", 0.0)),
            ignore_resistance=float(getattr(loadout, "ignore_resistance", 0.0)),
            imbalance_vulnerability_coeff=float(
                getattr(loadout, "imbalance_vulnerability_coeff", 1.3)
            ),
            is_unbalanced=bool(getattr(loadout, "is_unbalanced", False)),
            is_true_damage=bool(getattr(loadout, "is_true_damage", False)),
            combo_stacks=max(0, min(4, int(getattr(loadout, "combo_stacks", 0)))),
            break_defense_stacks=max(
                0, min(4, int(getattr(loadout, "break_defense_stacks", 0)))
            ),
            attached_effect_multiplier=float(
                getattr(loadout, "attached_effect_multiplier", 1.0)
            ),
            corrosion_duration_seconds=float(
                getattr(loadout, "corrosion_duration_seconds", 15.0)
            ),
        )

    @classmethod
    def from_request(cls, req: Any) -> EnemyEvalParams:
        """Web/API 请求体或任意带敌参属性的对象。"""
        return cls(
            enemy_defense=float(getattr(req, "enemy_defense", 100.0)),
            enemy_resistance=float(getattr(req, "enemy_resistance", 0.0)),
            ignore_resistance=float(getattr(req, "ignore_resistance", 0.0)),
            imbalance_vulnerability_coeff=float(
                getattr(req, "imbalance_vulnerability_coeff", 1.3)
            ),
            is_unbalanced=bool(getattr(req, "is_unbalanced", False)),
            is_true_damage=bool(getattr(req, "is_true_damage", False)),
            combo_stacks=max(0, min(4, int(getattr(req, "combo_stacks", 0)))),
            break_defense_stacks=max(
                0, min(4, int(getattr(req, "break_defense_stacks", 0)))
            ),
            attached_effect_multiplier=float(
                getattr(req, "attached_effect_multiplier", 1.0)
            ),
            corrosion_duration_seconds=float(
                getattr(req, "corrosion_duration_seconds", 15.0)
            ),
        )

    @classmethod
    def from_defense_only(cls, enemy_defense: float) -> EnemyEvalParams:
        """兼容仅传敌防的旧调用方。"""
        return cls(enemy_defense=float(enemy_defense))

    def damage_context_fields(
        self,
        *,
        final_attack: float = 0.0,
        skill_multiplier: float = 1.0,
        damage_type: str = "物理",
        skill_type: str = "战技",
        crit_rate: float = 0.05,
        crit_damage: float = 0.5,
    ) -> dict[str, Any]:
        """供 ``DamageContext(**fields)`` 使用的关键字参数字典。"""
        return {
            "final_attack": float(final_attack),
            "skill_multiplier": float(skill_multiplier),
            "damage_type": str(damage_type),
            "skill_type": str(skill_type),
            "enemy_defense": float(self.enemy_defense),
            "enemy_resistance": float(self.enemy_resistance),
            "ignore_resistance": float(self.ignore_resistance),
            "imbalance_vulnerability_coeff": float(self.imbalance_vulnerability_coeff),
            "is_unbalanced": bool(self.is_unbalanced),
            "is_true_damage": bool(self.is_true_damage),
            "combo_stacks": int(self.combo_stacks),
            "break_defense_stacks": int(self.break_defense_stacks),
            "crit_rate": float(crit_rate),
            "crit_damage": float(crit_damage),
        }

    def preview_cache_token(self) -> tuple[Any, ...]:
        """供 preview_cache 依赖签名扩展。"""
        return (
            float(self.enemy_defense),
            float(self.enemy_resistance),
            float(self.ignore_resistance),
            float(self.imbalance_vulnerability_coeff),
            bool(self.is_unbalanced),
            bool(self.is_true_damage),
            int(self.combo_stacks),
            int(self.break_defense_stacks),
            float(self.attached_effect_multiplier),
            float(self.corrosion_duration_seconds),
        )

    def search_job_kwargs(self) -> dict[str, Any]:
        """供 ``SearchJobInputs`` 使用的敌参关键字。"""
        return {
            "enemy_defense": float(self.enemy_defense),
            "enemy_resistance": float(self.enemy_resistance),
            "ignore_resistance": float(self.ignore_resistance),
            "imbalance_vulnerability_coeff": float(self.imbalance_vulnerability_coeff),
            "is_unbalanced": bool(self.is_unbalanced),
            "is_true_damage": bool(self.is_true_damage),
            "combo_stacks": int(self.combo_stacks),
            "break_defense_stacks": int(self.break_defense_stacks),
            "attached_effect_multiplier": float(self.attached_effect_multiplier),
            "corrosion_duration_seconds": float(self.corrosion_duration_seconds),
        }

    def abnormal_eval_kwargs(self) -> dict[str, float]:
        """物理/法术异常分项的附带效果与腐蚀参数。"""
        return {
            "attached_effect_multiplier": float(self.attached_effect_multiplier),
            "corrosion_duration_seconds": float(self.corrosion_duration_seconds),
        }


def build_search_job_inputs_from_request(
    req: Any,
    *,
    fixed_loadout: Any,
) -> Any:
    """Web 搜索/预估请求 → ``SearchJobInputs``（延迟导入避免 GUI 环依赖）。"""
    from games.endfield.calc.search.plan.controller import SearchJobInputs

    enemy = EnemyEvalParams.from_request(req)
    return SearchJobInputs(
        char_data=req.char_data,
        char_level=int(req.char_level),
        weapon_level=int(req.weapon_level),
        trust_level=int(req.trust_level),
        skill_name=str(req.skill_name),
        skill_type=str(req.skill_type),
        skill_multiplier=float(req.skill_multiplier),
        damage_type=str(req.damage_type),
        weapon_scope_label=str(req.weapon_scope_label),
        equipment_scope_label=str(req.equipment_scope_label),
        all_weapons=list(req.all_weapons),
        current_weapon=dict(req.current_weapon),
        equipment_catalog=dict(req.equipment_catalog),
        fixed_loadout=fixed_loadout,
        use_manual_multi_skill_counts=bool(
            getattr(req, "use_manual_multi_skill_counts", False)
        ),
        skill_1_level=int(getattr(req, "skill_1_level", 0)),
        skill_2_level=int(getattr(req, "skill_2_level", 0)),
        skill_3_level=int(getattr(req, "skill_3_level", 0)),
        manual_counts=getattr(req, "manual_counts", None),
        physical_abnormal_counts=getattr(req, "physical_abnormal_counts", None),
        spell_abnormal_counts=getattr(req, "spell_abnormal_counts", None),
        damage_component_mode=str(getattr(req, "damage_component_mode", "skill_and_abnormal")),
        use_expected_crit=bool(getattr(req, "use_expected_crit", False)),
        include_conditional_equipment_crit=bool(
            getattr(req, "include_conditional_equipment_crit", False)
        ),
        extra_crit_rate=float(getattr(req, "extra_crit_rate", 0.0)),
        extra_crit_damage=float(getattr(req, "extra_crit_damage", 0.0)),
        **enemy.search_job_kwargs(),
    )
