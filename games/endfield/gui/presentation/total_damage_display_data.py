# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""
总伤面板数据处理逻辑（纯 Python）。

从 total_damage_panel.py 提取，不依赖 PySide6，可被 Web/CLI/测试复用。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from games.endfield.calc.skills.segments import parse_segment_key

_SKILL_TYPE_ORDER: tuple[str, ...] = ("战技", "连携技", "终结技")


@dataclass
class SegmentDisplayRow:
    """单个技能段的显示数据。"""

    key: str
    single: float
    count: int
    total: float
    share: float
    seg_index: str = ""

    def __post_init__(self) -> None:
        if not self.seg_index:
            parts = self.key.split(":")
            self.seg_index = parts[1] if len(parts) > 1 else self.key


@dataclass
class SkillTypeGroup:
    """一个技能类型的分组数据。"""

    skill_type: str
    label: str
    total: float
    percentage: float
    segments: list[SegmentDisplayRow] = field(default_factory=list)


@dataclass
class TotalDamageDisplayData:
    """总伤面板的完整显示数据。"""

    weighted_total: float
    selected_label: str
    has_data: bool
    groups: list[SkillTypeGroup] = field(default_factory=list)
    fallback_rows: list[SegmentDisplayRow] = field(default_factory=list)


def build_total_damage_display(
    seg_damage: dict[str, float],
    seg_counts: dict[str, int],
    seg_totals: dict[str, float],
    skill_type_totals: dict[str, float],
    weighted_total: float,
    rotation_share: dict[str, float],
    selected_label: str,
) -> TotalDamageDisplayData:
    """从快照数据构建总伤面板显示数据。

    Args:
        seg_damage: 各段单次伤害
        seg_counts: 各段次数
        seg_totals: 各段总伤害
        skill_type_totals: 各技能类型总伤害
        weighted_total: 加权总伤
        rotation_share: 各段占比百分比
        selected_label: 当前选中技能标签

    Returns:
        TotalDamageDisplayData 包含所有分组和行数据。
    """
    has_data = weighted_total > 0

    # 按技能类型分组
    segments_by_type: dict[str, list[SegmentDisplayRow]] = {}
    for key in seg_damage:
        stype, _ = parse_segment_key(key)
        if stype not in segments_by_type:
            segments_by_type[stype] = []
        segments_by_type[stype].append(
            SegmentDisplayRow(
                key=key,
                single=seg_damage.get(key, 0.0),
                count=seg_counts.get(key, 0),
                total=seg_totals.get(key, 0.0),
                share=rotation_share.get(key, 0.0),
            )
        )

    # 确定可见类型（按固定顺序）
    visible_types = [t for t in _SKILL_TYPE_ORDER if t in segments_by_type or t in skill_type_totals]

    groups: list[SkillTypeGroup] = []
    for skill_type in visible_types:
        st_total = skill_type_totals.get(skill_type, 0.0)
        st_pct = (st_total / weighted_total * 100.0) if has_data and weighted_total > 0 else 0.0

        label = f"{skill_type}"
        if st_pct > 0:
            label += f" ({st_pct:.1f}%)"

        segments = segments_by_type.get(skill_type, [])
        segments.sort(key=lambda x: x.single, reverse=True)

        groups.append(
            SkillTypeGroup(
                skill_type=skill_type,
                label=label,
                total=st_total,
                percentage=st_pct,
                segments=segments,
            )
        )

    # 无可见类型时的回退行
    fallback_rows: list[SegmentDisplayRow] = []
    if not visible_types and has_data:
        for key, single in seg_damage.items():
            count = seg_counts.get(key, 0)
            if count > 0:
                fallback_rows.append(
                    SegmentDisplayRow(
                        key=key,
                        single=single,
                        count=count,
                        total=seg_totals.get(key, 0.0),
                        share=0.0,
                    )
                )

    return TotalDamageDisplayData(
        weighted_total=weighted_total,
        selected_label=selected_label,
        has_data=has_data,
        groups=groups,
        fallback_rows=fallback_rows,
    )
