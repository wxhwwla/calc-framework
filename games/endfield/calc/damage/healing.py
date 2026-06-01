# SPDX-License-Identifier: AGPL-3.0
"""治疗量计算（NGA PART 04 §4.1）。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HealingContext:
    """治疗结算输入。"""

    base_heal_flat: float = 0.0
    """治疗基础值（技能固定量）。"""
    stat_per_point: float = 0.0
    """每点属性增加的治疗（如每点意志 +0.47）。"""
    stat_value: float = 0.0
    """用于治疗的属性值（含小数，与游戏一致）。"""
    max_hp: float = 0.0
    hp_heal_ratio: float = 0.0
    """按最大生命值比例（如 0.05 = 5%）。"""
    heal_efficiency: float = 0.0
    """治疗方治疗效率（加算）。"""
    received_heal_efficiency: float = 0.0
    """受治疗方受治疗效率（加算）。"""
    independent_heal_bonus: float = 0.0
    """独立治疗效果提升（乘算区）。"""


def received_heal_efficiency_from_will(will: float) -> float:
    """意志 → 受治疗效率：0.001 × 意志整数部分。"""
    return int(will) * 0.001


def calculate_healing(ctx: HealingContext) -> dict[str, float]:
    """治疗量 = 基础治疗区 × 治疗效率区 × 独立治疗效果区。"""
    base_zone = (
        float(ctx.base_heal_flat)
        + float(ctx.stat_per_point) * float(ctx.stat_value)
        + float(ctx.max_hp) * float(ctx.hp_heal_ratio)
    )
    efficiency_zone = 1.0 + float(ctx.heal_efficiency) + float(ctx.received_heal_efficiency)
    independent_zone = 1.0 + float(ctx.independent_heal_bonus)
    total = base_zone * efficiency_zone * independent_zone
    return {
        "基础治疗区": base_zone,
        "治疗效率区": efficiency_zone,
        "独立治疗效果区": independent_zone,
        "治疗量": total,
    }
