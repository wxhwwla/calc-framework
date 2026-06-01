# SPDX-License-Identifier: AGPL-3.0
"""失衡系统参数（NGA PART 03）。"""

from __future__ import annotations

ENEMY_TIERS: tuple[str, ...] = ("普通", "进阶", "精英", "头目", "领袖")

# 典型失衡值上限（取区间中值便于估算）
IMBALANCE_CAP_TYPICAL: dict[str, float] = {
    "普通": 75.0,
    "进阶": 170.0,
    "精英": 280.0,
    "头目": 280.0,
    "领袖": 400.0,
}

IMBALANCE_DURATION_SEC: dict[str, float] = {
    "普通": 6.0,
    "进阶": 6.0,
    "精英": 9.0,
    "头目": 9.0,
    "领袖": 11.0,
}

# 快速打进失衡后的累积惩罚：窗口秒 → 惩罚持续秒
FAST_BREAK_WINDOW_SEC: dict[str, float] = {
    "普通": 3.0,
    "进阶": 6.0,
    "精英": 10.0,
    "头目": 10.0,
    "领袖": 15.0,
}
FAST_BREAK_PENALTY_DURATION_SEC: dict[str, float] = {
    "普通": 1.0,
    "进阶": 3.0,
    "精英": 5.0,
    "头目": 5.0,
    "领袖": 10.0,
}
FAST_BREAK_ACCUMULATION_MULT = 0.5

# 失衡节点：失衡值上限的比例
IMBALANCE_NODE_FRACTIONS: dict[int, tuple[float, ...]] = {
    1: (0.5,),
    2: (1.0 / 3.0, 2.0 / 3.0),
}

DEFAULT_IMBALANCE_EFFICIENCY_BONUS = 0.0  # 点剑套装 +20%


def imbalance_cap_for_tier(tier: str) -> float:
    return float(IMBALANCE_CAP_TYPICAL.get(str(tier).strip() or "普通", 75.0))


def imbalance_duration_for_tier(tier: str) -> float:
    return float(IMBALANCE_DURATION_SEC.get(str(tier).strip() or "普通", 6.0))


def scaled_imbalance_gain(base_value: float, *, imbalance_efficiency_bonus: float = 0.0) -> float:
    """失衡值累积 = 基础 × (1 + 失衡效率加成)。"""
    return float(base_value) * (1.0 + max(0.0, float(imbalance_efficiency_bonus)))


def accumulation_multiplier_after_fast_break(
    *,
    tier: str,
    seconds_since_combat_start: float,
    seconds_since_last_imbalance_end: float,
    was_fast_break: bool,
) -> float:
    """失衡结束后短时间内再累积时 ×0.5。"""
    if not was_fast_break:
        return 1.0
    window = FAST_BREAK_WINDOW_SEC.get(str(tier).strip() or "普通", 3.0)
    penalty_duration = FAST_BREAK_PENALTY_DURATION_SEC.get(str(tier).strip() or "普通", 1.0)
    if seconds_since_combat_start > window:
        return 1.0
    if seconds_since_last_imbalance_end > penalty_duration:
        return 1.0
    return FAST_BREAK_ACCUMULATION_MULT


def imbalance_node_thresholds(cap: float, node_count: int = 1) -> tuple[float, ...]:
    fracs = IMBALANCE_NODE_FRACTIONS.get(max(1, min(int(node_count), 2)), (0.5,))
    return tuple(float(cap) * f for f in fracs)
