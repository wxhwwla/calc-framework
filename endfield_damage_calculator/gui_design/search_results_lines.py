#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全量遍历结果报告文案（无 CustomTkinter）。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, Sequence

from calculation.loadout_optimizer import LoadoutScore
from calculation.skill_segments import format_segment_breakdown_lines


def _format_top_result_line(
    rank: int,
    score: LoadoutScore,
    *,
    damage_metric: str = "伤害",
    segment_counts: Optional[dict[str, int]] = None,
) -> list[str]:
    loadout = score.loadout_names
    lines = [
        f"Top{rank}: 武器 {score.weapon_name}  {damage_metric} {score.final_damage:.1f}",
        f"       护甲 {loadout.get('chest', '')}  |  "
        f"护手 {loadout.get('gloves', '')}  |  "
        f"配件A {loadout.get('accessory_a', '')}  |  "
        f"配件B {loadout.get('accessory_b', '')}",
    ]
    if score.segment_breakdown and segment_counts:
        lines.extend(
            format_segment_breakdown_lines(
                score.segment_breakdown,
                segment_counts,
                indent="       ",
            )
        )
    return lines


def build_search_results_report_lines(
    *,
    mode_label: str,
    skill_label: str,
    scope_labels: tuple[str, str] = ("", ""),
    processed_combinations: int,
    total_combinations: int,
    top_results: Sequence[LoadoutScore],
    export_paths: Optional[dict[str, str]] = None,
    cancelled: bool = False,
    damage_metric: str = "伤害",
    segment_counts: Optional[dict[str, int]] = None,
) -> list[str]:
    """生成全量遍历结果报告（供弹窗与测试使用）。"""
    weapon_scope, equip_scope = scope_labels
    lines = [
        f"=== {mode_label} ===",
        f"技能: {skill_label}",
    ]
    if weapon_scope:
        lines.append(f"武器候选: {weapon_scope}")
    if equip_scope:
        lines.append(f"装备范围: {equip_scope}")
    lines.append(
        f"组合进度: {processed_combinations}/{total_combinations}"
        + ("（已取消，以下为目前已完成中的 Top）" if cancelled else "")
    )
    lines.append("")
    if not top_results:
        lines.append("无可用 Top 结果，请检查装备数据或缩小候选范围。")
    else:
        lines.append("—— Top 配装 ——")
        for idx, score in enumerate(top_results, start=1):
            lines.extend(
                _format_top_result_line(
                    idx,
                    score,
                    damage_metric=damage_metric,
                    segment_counts=segment_counts,
                )
            )
    if export_paths:
        lines.append("")
        lines.append("—— 导出文件 ——")
        for label, path in export_paths.items():
            if path:
                lines.append(f"{label}: {path}")
    return lines


def loadout_scores_from_payload(rows: Sequence[dict[str, Any]]) -> tuple[LoadoutScore, ...]:
    """将 MVP 流水线返回的 top_results 字典转回 LoadoutScore。"""
    scores: list[LoadoutScore] = []
    for row in rows:
        scores.append(
            LoadoutScore(
                weapon_name=str(row.get("weapon_name", "")),
                final_damage=float(row.get("final_damage", 0.0)),
                loadout_names=dict(row.get("loadout_names") or {}),
                segment_breakdown=dict(row.get("segment_breakdown") or {}) or None,
            )
        )
    return tuple(scores)


def export_paths_to_strings(exports: dict[str, Any]) -> dict[str, str]:
    """将导出路径对象转为弹窗可读的字符串映射。"""
    mapping: dict[str, str] = {}
    for key, value in exports.items():
        if value is None:
            continue
        mapping[key] = str(Path(value))
    return mapping
