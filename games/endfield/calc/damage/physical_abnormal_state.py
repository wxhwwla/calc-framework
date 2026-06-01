# SPDX-License-Identifier: AGPL-3.0
"""物理异常与破防状态区分（NGA PART 02）。

破防 debuff 与碎甲/猛击等物理异常独立叠层；计算器按次数矩阵估算异常伤，
本模块仅提供破防层消耗与物理异常键识别，供后续完整状态机扩展。
"""

from __future__ import annotations

PHYSICAL_ABNORMAL_TYPES: tuple[str, ...] = ("倒地", "击飞", "碎甲", "猛击")


def parse_abnormal_base_name(key: str) -> str:
    """``猛击:2`` → ``猛击``；``强制:灼热异常:1`` 保留前缀段。"""
    text = str(key or "").strip()
    if ":" not in text:
        return text
    head, _rest = text.split(":", 1)
    if head == "强制" and ":" in _rest:
        return f"强制:{_rest.split(':', 1)[0]}"
    return head


def is_physical_abnormal_key(key: str) -> bool:
    """是否为四类物理异常键（不含破防）。"""
    return parse_abnormal_base_name(key) in PHYSICAL_ABNORMAL_TYPES


def consume_break_defense_stacks(
    stacks: int,
    *,
    consuming_hits: int = 1,
    layers_per_hit: int = 1,
) -> int:
    """消耗型攻击后剩余破防层数（默认每 hit 耗 1 层）。"""
    hits = max(0, int(consuming_hits))
    per_hit = max(0, int(layers_per_hit))
    return max(0, int(stacks) - hits * per_hit)


def break_defense_after_rotation_hits(
    initial_stacks: int,
    skill_counts: dict[str, int],
    *,
    layers_per_skill_hit: int = 1,
) -> int:
    """按技能段总 hit 数递减破防层（物理异常次数不计入）。"""
    total_hits = sum(max(0, int(v)) for k, v in skill_counts.items() if not is_physical_abnormal_key(k))
    return consume_break_defense_stacks(
        initial_stacks,
        consuming_hits=total_hits,
        layers_per_hit=layers_per_skill_hit,
    )


def format_break_defense_rotation_note(
    initial_stacks: int,
    skill_counts: dict[str, int],
) -> str | None:
    """轮转后破防剩余层数说明；无破防时返回 None。"""
    if int(initial_stacks) <= 0:
        return None
    remaining = break_defense_after_rotation_hits(initial_stacks, skill_counts)
    return f"破防层数: 初始 {initial_stacks} → 轮转后约 {remaining}（按技能段次数消耗，不含物理异常）"
