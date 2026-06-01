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
        )
