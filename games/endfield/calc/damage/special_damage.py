# SPDX-License-Identifier: AGPL-3.0
"""特殊伤害类型辅助（NGA PART 01 §1.16 等）。"""

from __future__ import annotations

# 游戏内常见特殊伤害标签（引擎侧以 is_true_damage / 乘区归类为主）
SPECIAL_DAMAGE_KINDS: tuple[str, ...] = (
    "真实伤害",
    "生命汲取",
    "纯元素",
    "传导",
    "爆破",
    "附着",
    "异常",
    "其它",
)


def life_steal_heal(final_damage: float, *, life_steal_rate: float) -> float:
    """生命汲取回复量 = 最终伤害 × 汲取率（小数）。"""
    rate = max(0.0, float(life_steal_rate))
    return max(0.0, float(final_damage) * rate)


def effective_defense_multiplier(*, enemy_defense: float, is_true_damage: bool) -> float:
    """防御区乘数；真实伤害恒为 1.0。"""
    if is_true_damage:
        return 1.0
    defense = max(0.0, float(enemy_defense))
    return 100.0 / (100.0 + defense)
