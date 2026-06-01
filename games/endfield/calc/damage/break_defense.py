# SPDX-License-Identifier: AGPL-3.0
"""破防 debuff 与物理异常区分（NGA PART 02）。

破防为独立叠层 debuff（0–4），与碎甲/猛击等物理异常状态机分开。
本模块提供层数→易伤加成估算，供手动 buff 或后续完整状态机引用。
"""

from __future__ import annotations

MAX_BREAK_DEFENSE_STACKS = 4
DEFAULT_VULNERABILITY_PER_STACK = 0.08


def clamp_break_defense_stacks(stacks: int) -> int:
    """破防层数限制在 0–4。"""
    return max(0, min(MAX_BREAK_DEFENSE_STACKS, int(stacks)))


def vulnerability_bonus_from_break_defense(
    stacks: int,
    *,
    per_stack: float = DEFAULT_VULNERABILITY_PER_STACK,
) -> float:
    """破防层数 → 受击易伤加成（小数）。"""
    rate = max(0.0, float(per_stack))
    return rate * clamp_break_defense_stacks(stacks)


def damage_effects_from_break_defense(stacks: int) -> tuple:
    """破防层数 → 易伤区 DamageEffect（供伤害引擎合并）。"""
    from games.endfield.calc.damage.engine.types import DamageEffect

    bonus = vulnerability_bonus_from_break_defense(stacks)
    if bonus <= 0.0:
        return ()
    layer = clamp_break_defense_stacks(stacks)
    return (
        DamageEffect(
            effect_type="易伤",
            value=bonus,
            source="破防",
            raw_text=f"破防×{layer} 易伤+{bonus * 100:.0f}%",
        ),
    )
