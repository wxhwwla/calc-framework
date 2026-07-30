#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""全量遍历结果报告文案（无 CustomTkinter）。"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from calc_framework.ui.i18n import tr

from games.endfield.calc.loadout.optimizer import LoadoutScore
from games.endfield.calc.manual_buff.physical import (
    abnormal_weighted_total,
    format_abnormal_breakdown_lines,
    split_damage_breakdown,
)
from games.endfield.calc.manual_buff.spell import (
    format_spell_abnormal_breakdown_lines,
    is_spell_abnormal_key,
    spell_abnormal_weighted_total,
)
from games.endfield.calc.skills.segments import format_segment_breakdown_lines


def _format_top_result_line(
    rank: int,
    score: LoadoutScore,
    *,
    damage_metric: str | None = None,
    segment_counts: dict[str, int] | None = None,
    abnormal_counts: dict[str, int] | None = None,
    spell_abnormal_counts: dict[str, int] | None = None,
) -> list[str]:
    loadout = score.loadout_names
    metric = damage_metric if damage_metric is not None else tr("desktop.endfield.damageMetric")

    lines = [
        tr(
            "desktop.endfield.searchReportRankHeader",
            rank=rank,
            weapon=score.weapon_name,
            metric=metric,
            damage=f"{score.final_damage:.1f}",
        ),
        tr(
            "desktop.endfield.searchReportLoadoutLine",
            chest=loadout.get("chest", ""),
            gloves=loadout.get("gloves", ""),
            acc_a=loadout.get("accessory_a", ""),
            acc_b=loadout.get("accessory_b", ""),
        ),
    ]

    if score.segment_breakdown:
        base_skill_breakdown, physical_abnormal_breakdown = split_damage_breakdown(score.segment_breakdown)

        spell_abnormal_breakdown: dict[str, float] = {}

        skill_breakdown: dict[str, float] = {}

        for key, value in base_skill_breakdown.items():
            if is_spell_abnormal_key(key):
                spell_abnormal_breakdown[key] = value

            else:
                skill_breakdown[key] = value

    else:
        skill_breakdown, physical_abnormal_breakdown, spell_abnormal_breakdown = {}, {}, {}

    if skill_breakdown and segment_counts:
        lines.extend(
            format_segment_breakdown_lines(
                skill_breakdown,
                segment_counts,
                indent="       ",
            )
        )

    if physical_abnormal_breakdown and abnormal_counts:
        lines.extend(
            format_abnormal_breakdown_lines(
                physical_abnormal_breakdown,
                abnormal_counts,
                indent="       ",
            )
        )

        abnormal_total = abnormal_weighted_total(physical_abnormal_breakdown, abnormal_counts)

        if abnormal_total > 0:
            lines.append(
                tr(
                    "desktop.endfield.searchReportPhysicalAbnormalTotal",
                    total=f"{abnormal_total:.1f}",
                )
            )

    if spell_abnormal_breakdown and spell_abnormal_counts:
        lines.extend(
            format_spell_abnormal_breakdown_lines(
                spell_abnormal_breakdown,
                spell_abnormal_counts,
                indent="       ",
            )
        )

        spell_total = spell_abnormal_weighted_total(spell_abnormal_breakdown, spell_abnormal_counts)

        if spell_total > 0:
            lines.append(
                tr(
                    "desktop.endfield.searchReportSpellAbnormalTotal",
                    total=f"{spell_total:.1f}",
                )
            )

    """format top result line。"""
    return lines


def build_search_results_report_lines(
    *,
    mode_label: str,
    skill_label: str,
    scope_labels: tuple[str, str] = ("", ""),
    processed_combinations: int,
    total_combinations: int,
    top_results: Sequence[LoadoutScore],
    export_paths: dict[str, str] | None = None,
    cancelled: bool = False,
    damage_metric: str | None = None,
    segment_counts: dict[str, int] | None = None,
    abnormal_counts: dict[str, int] | None = None,
    spell_abnormal_counts: dict[str, int] | None = None,
) -> list[str]:
    """生成全量遍历结果报告（供弹窗与测试使用）。"""

    weapon_scope, equip_scope = scope_labels
    metric = damage_metric if damage_metric is not None else tr("desktop.endfield.damageMetric")

    lines = [
        f"=== {mode_label} ===",
        tr("desktop.endfield.previewSkillLabel", label=skill_label),
    ]

    if weapon_scope:
        lines.append(tr("desktop.endfield.searchReportWeaponScope", scope=weapon_scope))

    if equip_scope:
        lines.append(tr("desktop.endfield.previewEquipmentScope", scope=equip_scope))

    if cancelled:
        lines.append(
            tr(
                "desktop.endfield.searchReportProgressCancelled",
                processed=processed_combinations,
                total=total_combinations,
            )
        )
    else:
        lines.append(
            tr(
                "desktop.endfield.searchReportProgress",
                processed=processed_combinations,
                total=total_combinations,
            )
        )

    lines.append("")

    if not top_results:
        lines.append(tr("desktop.endfield.searchReportNoTop"))

    else:
        lines.append(tr("desktop.endfield.searchReportTopHeader"))

        for idx, score in enumerate(top_results, start=1):
            lines.extend(
                _format_top_result_line(
                    idx,
                    score,
                    damage_metric=metric,
                    segment_counts=segment_counts,
                    abnormal_counts=abnormal_counts,
                    spell_abnormal_counts=spell_abnormal_counts,
                )
            )

    if export_paths:
        lines.append("")

        lines.append(tr("desktop.endfield.searchReportExportHeader"))

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
