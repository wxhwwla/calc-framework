# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""搜索结果数据处理 — 纯 Python，无 PySide6 依赖。

从 qt_actions.py 的 _build_tree_items 提取而来。
提供结构化的搜索结果树节点，GUI 层只需转换为 QTreeWidgetItem。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from games.endfield.calc.loadout.optimizer.types import LoadoutScore
from games.endfield.calc.manual_buff.physical import (
    format_abnormal_breakdown_lines,
    split_damage_breakdown,
)
from games.endfield.calc.manual_buff.spell import (
    format_spell_abnormal_breakdown_lines,
    is_spell_abnormal_key,
)
from games.endfield.calc.skills.segments import (
    aggregate_weighted_damage,
    format_segment_breakdown_lines,
)


@dataclass
class SearchResultItem:
    """搜索结果树节点（纯数据，无 Qt 依赖）。"""

    text: str
    children: list[SearchResultItem] = field(default_factory=list)
    color: str | None = None
    expanded: bool = False


def build_result_header(score: LoadoutScore, idx: int, *, damage_metric: str = "伤害") -> str:
    """为单个搜索结果构建头部文本。"""
    loadout = score.loadout_names
    return (
        f"第{idx}名: {score.weapon_name}  |  "
        f"{damage_metric} {score.final_damage:.1f}  |  "
        f"护甲 {loadout.get('chest', '')}  |  "
        f"护手 {loadout.get('gloves', '')}  |  "
        f"配件A {loadout.get('accessory_a', '')}  |  "
        f"配件B {loadout.get('accessory_b', '')}"
    )


def build_search_result_items(
    top_results: list[LoadoutScore] | None,
    *,
    damage_metric: str = "伤害",
    segment_counts: dict[str, int] | None = None,
    abnormal_counts: dict[str, int] | None = None,
    spell_abnormal_counts: dict[str, int] | None = None,
) -> list[SearchResultItem]:
    """将搜索结果转换为结构化树节点。

    Returns:
        SearchResultItem 列表。GUI 层遍历此列表创建 QTreeWidgetItem。
    """
    if not top_results:
        return []

    nodes: list[SearchResultItem] = []

    for idx, score in enumerate(top_results, start=1):
        header_text = build_result_header(score, idx, damage_metric=damage_metric)
        root = SearchResultItem(text=header_text, expanded=(idx <= 3))

        if score.segment_breakdown and (segment_counts or abnormal_counts):
            _add_breakdown_children(
                root,
                score,
                segment_counts,
                abnormal_counts,
                spell_abnormal_counts,
            )

        nodes.append(root)

    return nodes


def _add_breakdown_children(
    parent: SearchResultItem,
    score: LoadoutScore,
    segment_counts: dict[str, int] | None,
    abnormal_counts: dict[str, int] | None,
    spell_abnormal_counts: dict[str, int] | None,
) -> None:
    """为单个结果节点添加伤害明细子节点。"""
    base_skill_breakdown, physical_abnormal_breakdown = split_damage_breakdown(
        score.segment_breakdown,
    )

    spell_abnormal_breakdown: dict[str, float] = {}
    skill_breakdown: dict[str, float] = {}

    for key, value in base_skill_breakdown.items():
        if is_spell_abnormal_key(key):
            spell_abnormal_breakdown[key] = value
        else:
            skill_breakdown[key] = value

    if skill_breakdown and segment_counts:
        breakdown_lines = format_segment_breakdown_lines(skill_breakdown, segment_counts, indent="")
        for line in breakdown_lines:
            parent.children.append(SearchResultItem(text=line, color="segment"))

        weighted_total, _, skill_type_totals = aggregate_weighted_damage(skill_breakdown, segment_counts)
        if len(skill_type_totals) > 1:
            parts = [f"{k} {v:.1f}" for k, v in skill_type_totals.items()]
            total_text = f"加权合计: {weighted_total:.1f}（{' + '.join(parts)}）"
        else:
            total_text = f"加权合计: {weighted_total:.1f}"
        parent.children.append(SearchResultItem(text=total_text))

    if physical_abnormal_breakdown and abnormal_counts:
        ab_lines = format_abnormal_breakdown_lines(physical_abnormal_breakdown, abnormal_counts, indent="")
        for line in ab_lines:
            parent.children.append(SearchResultItem(text=line, color="abnormal"))

    if spell_abnormal_breakdown and spell_abnormal_counts:
        sp_lines = format_spell_abnormal_breakdown_lines(spell_abnormal_breakdown, spell_abnormal_counts, indent="")
        for line in sp_lines:
            parent.children.append(SearchResultItem(text=line, color="abnormal"))


def format_search_result_summary(top_results: list[LoadoutScore] | None) -> str:
    """格式化搜索结果摘要文本。"""
    if not top_results:
        return ""
    count = len(top_results)
    expanded = min(3, count)
    return f"共 {count} 个结果  |  前 {expanded} 项已展开"


def format_search_progress(
    prefix: str,
    processed: int,
    total: int,
    eta_seconds: float,
    estimated_total_seconds: float,
) -> str:
    """格式化搜索进度文本（纯逻辑包装）。"""
    from games.endfield.gui.controls.search.search_settings import format_search_progress_text

    return format_search_progress_text(
        prefix=prefix,
        processed=processed,
        total=total,
        eta_seconds=eta_seconds,
        estimated_total_seconds=estimated_total_seconds,
    )
