# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""
敌方参数面板数据模型（纯 Python）。

从 qt_enemy_panel.py 提取，不依赖 PySide6，可被 Web/CLI/测试复用。
提供一次性解析所有敌方参数的便捷函数。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from games.endfield.data_loading.enemy_params import (
    DEFAULT_ATTACHED_EFFECT_MULTIPLIER,
    DEFAULT_BREAK_DEFENSE_STACKS,
    DEFAULT_COMBO_STACKS,
    DEFAULT_CORROSION_DURATION_SEC,
    DEFAULT_ENEMY_DEFENSE,
    DEFAULT_ENEMY_RESISTANCE,
    DEFAULT_ENEMY_TIER,
    DEFAULT_IGNORE_RESISTANCE,
    DEFAULT_IMBALANCE_EFFICIENCY_BONUS,
    DEFAULT_IMBALANCE_VULNERABILITY,
    DEFAULT_IS_TRUE_DAMAGE,
    DEFAULT_IS_UNBALANCED,
    resolve_enemy_defense,
    resolve_enemy_resistance,
    resolve_enemy_tier,
    resolve_ignore_resistance,
    resolve_imbalance_vulnerability,
    resolve_is_unbalanced,
)


@dataclass
class EnemyResolvedParams:
    """一次性解析的敌方参数集合。"""

    enemy_defense: float
    enemy_resistance: float
    ignore_resistance: float
    imbalance_vulnerability_coeff: float
    is_unbalanced: bool
    is_true_damage: bool
    enemy_tier: str

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式（兼容 GUI get_params 返回值）。"""
        return {
            "enemy_defense": self.enemy_defense,
            "enemy_resistance": self.enemy_resistance,
            "ignore_resistance": self.ignore_resistance,
            "imbalance_vulnerability_coeff": self.imbalance_vulnerability_coeff,
            "is_unbalanced": self.is_unbalanced,
            "is_true_damage": self.is_true_damage,
            "enemy_tier": self.enemy_tier,
        }


def resolve_enemy_params(enemy_id: str) -> EnemyResolvedParams:
    """根据敌人 ID 一次性解析所有敌方参数。

    Args:
        enemy_id: 敌人标识符（空字符串使用默认值）

    Returns:
        EnemyResolvedParams 包含所有已解析的敌方参数。
    """
    return EnemyResolvedParams(
        enemy_defense=resolve_enemy_defense(enemy_id),
        enemy_resistance=resolve_enemy_resistance(enemy_id),
        ignore_resistance=resolve_ignore_resistance(enemy_id),
        imbalance_vulnerability_coeff=resolve_imbalance_vulnerability(enemy_id),
        is_unbalanced=resolve_is_unbalanced(enemy_id),
        is_true_damage=DEFAULT_IS_TRUE_DAMAGE,
        enemy_tier=resolve_enemy_tier(enemy_id),
    )


def default_enemy_params() -> dict[str, Any]:
    """返回默认敌方参数字典。"""
    return {
        "enemy_defense": DEFAULT_ENEMY_DEFENSE,
        "enemy_resistance": DEFAULT_ENEMY_RESISTANCE,
        "ignore_resistance": DEFAULT_IGNORE_RESISTANCE,
        "imbalance_vulnerability_coeff": DEFAULT_IMBALANCE_VULNERABILITY,
        "is_unbalanced": DEFAULT_IS_UNBALANCED,
        "is_true_damage": DEFAULT_IS_TRUE_DAMAGE,
        "enemy_tier": DEFAULT_ENEMY_TIER,
        "combo_stacks": DEFAULT_COMBO_STACKS,
        "attached_effect_multiplier": DEFAULT_ATTACHED_EFFECT_MULTIPLIER,
        "corrosion_duration_seconds": DEFAULT_CORROSION_DURATION_SEC,
        "imbalance_efficiency_bonus": DEFAULT_IMBALANCE_EFFICIENCY_BONUS,
        "break_defense_stacks": DEFAULT_BREAK_DEFENSE_STACKS,
    }
