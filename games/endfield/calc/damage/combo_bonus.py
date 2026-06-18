# SPDX-License-Identifier: AGPL-3.0
"""连击增伤层数表（NGA PART 01 §1.14）。"""

from __future__ import annotations

# 层数 1–4 对应总加成（非线性叠层后的面板值）
COMBO_BONUS_BY_STACKS_SKILL: tuple[float, ...] = (0.30, 0.45, 0.60, 0.75)
COMBO_BONUS_BY_STACKS_ULTIMATE: tuple[float, ...] = (0.20, 0.30, 0.40, 0.50)

_SKILL_TYPES_USING_SKILL_TABLE = frozenset({"战技", "连携技", "普攻", "普通攻击"})


def combo_bonus_rate(skill_type: str, stacks: int) -> float:
    """返回连击增伤加成率（小数），非法层数返回 0。"""
    if stacks <= 0:
        return 0.0
    idx = min(int(stacks), 4) - 1
    table = COMBO_BONUS_BY_STACKS_ULTIMATE if skill_type == "终结技" else COMBO_BONUS_BY_STACKS_SKILL
    return float(table[idx])


def combo_zone_multiplier(skill_type: str, stacks: int, *, flat_legacy_bonus: float = 0.0) -> float:
    """连击增伤区乘数。stacks>0 用层数表，否则 1+flat_legacy_bonus。"""
    if stacks > 0:
        return 1.0 + combo_bonus_rate(skill_type, stacks)
    return 1.0 + max(0.0, float(flat_legacy_bonus))
