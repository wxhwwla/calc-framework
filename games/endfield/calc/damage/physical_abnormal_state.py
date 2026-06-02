# SPDX-License-Identifier: AGPL-3.0
"""物理异常与破防状态区分（NGA PART 02）。

破防 debuff 与碎甲/猛击等物理异常独立叠层；计算器按次数矩阵估算异常伤，
本模块提供破防层消耗、轮转序号与物理异常键识别，供快照/多技能加权与预览说明。
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


def break_defense_stacks_at_hit(
    initial_stacks: int,
    hit_index: int,
    *,
    layers_per_hit: int = 1,
) -> int:
    """第 hit_index 次命中时的剩余破防层（1-based）。"""
    if hit_index <= 0:
        return max(0, int(initial_stacks))
    return consume_break_defense_stacks(
        initial_stacks,
        consuming_hits=max(0, int(hit_index) - 1),
        layers_per_hit=layers_per_hit,
    )


def ordered_rotation_keys(
    skill_counts: dict[str, int],
    *,
    preferred_order: list[str] | None = None,
) -> list[str]:
    """参与破防消耗的技能段键（不含物理异常），按轮转顺序排列。"""
    from games.endfield.calc.skills.segments import SKILL_TYPE_ORDER, parse_segment_key

    active = {
        str(k): max(0, int(v))
        for k, v in skill_counts.items()
        if max(0, int(v)) > 0 and not is_physical_abnormal_key(str(k))
    }
    if not active:
        return []

    def sort_key(key: str) -> tuple[int, int, str]:
        skill_type, seg_idx = parse_segment_key(key)
        try:
            order = SKILL_TYPE_ORDER.index(skill_type)
        except ValueError:
            order = 99
        return (order, seg_idx, key)
        """sort key。"""

    if preferred_order:
        keys = [k for k in preferred_order if k in active]
        for key in sorted(active.keys(), key=sort_key):
            if key not in keys:
                keys.append(key)
        return keys
    return sorted(active.keys(), key=sort_key)


def iter_rotation_hits(
    skill_counts: dict[str, int],
    *,
    preferred_order: list[str] | None = None,
):
    """按轮转顺序产出 (段键, 段内第几次, 全局第几次命中)。"""
    global_hit = 0
    for key in ordered_rotation_keys(skill_counts, preferred_order=preferred_order):
        count = max(0, int(skill_counts.get(key, 0)))
        for occurrence in range(1, count + 1):
            global_hit += 1
            yield key, occurrence, global_hit


def build_rotation_hit_index(
    skill_counts: dict[str, int],
    *,
    preferred_order: list[str] | None = None,
) -> dict[tuple[str, int], int]:
    """(段键, 段内 1-based 次数) → 全局 1-based 命中序号。"""
    return {
        (key, occurrence): global_hit
        for key, occurrence, global_hit in iter_rotation_hits(
            skill_counts, preferred_order=preferred_order
        )
    }
