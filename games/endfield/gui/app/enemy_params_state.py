# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""EnemyParamsState — 敌方参数纯数据状态（无 PySide6 依赖）。

从 endfield_app.py / endfield_actions.py 提取的 13 个敌方参数字段，
封装为 dataclass，提供 to_dict() / from_dict() 序列化。
可被 GUI / Web / CLI / 测试直接复用。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class EnemyParamsState:
    """敌方参数状态容器。

    属性：
        enemy_defense: 敌方防御力
        enemy_resistance: 敌方抗性（百分比）
        ignore_resistance: 无视抗性（百分比）
        imbalance_vulnerability_coeff: 失衡易伤系数
        is_unbalanced: 是否处于失衡状态
        is_true_damage: 是否为真实伤害
        enemy_tier: 敌方等阶（"普通" / "精英" / "首领"）
        combo_stacks: 连击层数（0-4）
        attached_effect_multiplier: 附着效果乘数
        corrosion_duration_seconds: 腐蚀持续时间（秒）
        imbalance_efficiency_bonus: 失衡效率加成
        break_defense_stacks: 破防层数（0-4）
    """

    enemy_defense: float = 100.0
    enemy_resistance: float = 0.0
    ignore_resistance: float = 0.0
    imbalance_vulnerability_coeff: float = 1.3
    is_unbalanced: bool = False
    is_true_damage: bool = False
    enemy_tier: str = "普通"
    combo_stacks: int = 0
    attached_effect_multiplier: float = 1.0
    corrosion_duration_seconds: float = 15.0
    imbalance_efficiency_bonus: float = 0.0
    break_defense_stacks: int = 0

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典（键名与 _apply_enemy_params 的 params 键一致）。"""
        return {
            "enemy_defense": self.enemy_defense,
            "enemy_resistance": self.enemy_resistance,
            "ignore_resistance": self.ignore_resistance,
            "imbalance_vulnerability_coeff": self.imbalance_vulnerability_coeff,
            "is_unbalanced": self.is_unbalanced,
            "is_true_damage": self.is_true_damage,
            "enemy_tier": self.enemy_tier,
            "combo_stacks": self.combo_stacks,
            "attached_effect_multiplier": self.attached_effect_multiplier,
            "corrosion_duration_seconds": self.corrosion_duration_seconds,
            "imbalance_efficiency_bonus": self.imbalance_efficiency_bonus,
            "break_defense_stacks": self.break_defense_stacks,
        }

    @classmethod
    def from_dict(cls, params: dict[str, Any]) -> EnemyParamsState:
        """从字典反序列化（兼容 _apply_enemy_params 的输入格式）。

        缺失键使用默认值，combo_stacks / break_defense_stacks 限制在 0-4。
        """
        return cls(
            enemy_defense=float(params.get("enemy_defense", 100.0)),
            enemy_resistance=float(params.get("enemy_resistance", 0.0)),
            ignore_resistance=float(params.get("ignore_resistance", 0.0)),
            imbalance_vulnerability_coeff=float(params.get("imbalance_vulnerability_coeff", 1.3)),
            is_unbalanced=bool(params.get("is_unbalanced", False)),
            is_true_damage=bool(params.get("is_true_damage", False)),
            enemy_tier=str(params.get("enemy_tier", "普通")),
            combo_stacks=max(0, min(4, int(params.get("combo_stacks", 0)))),
            attached_effect_multiplier=float(params.get("attached_effect_multiplier", 1.0)),
            corrosion_duration_seconds=float(params.get("corrosion_duration_seconds", 15.0)),
            imbalance_efficiency_bonus=float(params.get("imbalance_efficiency_bonus", 0.0)),
            break_defense_stacks=max(0, min(4, int(params.get("break_defense_stacks", 0)))),
        )
