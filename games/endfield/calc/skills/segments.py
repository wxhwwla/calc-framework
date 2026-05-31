#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""
技能段场景：从角色 JSON 读取各段倍率，并规范化手动次数键。

次数键格式 ``战技:1``、``连携技:2``；兼容旧预设 ``{"战技": 2}`` → ``{"战技:1": 2}``。
"""

from __future__ import annotations

from typing import Any

from games.endfield.calc.damage.types import (
    format_damage_type_display,
    resolve_segment_damage_type,
)
from games.endfield.calc.multi_skill.optimizer import SkillScenario

# 与 display_lines.CHARACTER_SKILL_TYPES 一致：(技能槽名, 倍率字段, 段伤害类型字段)
CHARACTER_SKILL_TYPES: tuple[tuple[str, str, str], ...] = (
    ("战技", "战技倍率", "战技段伤害类型"),
    ("连携技", "连携技倍率", "连携技段伤害类型"),
    ("终结技", "终结技倍率", "终结技段伤害类型"),
)

SKILL_TYPE_ORDER: tuple[str, ...] = ("战技", "连携技", "终结技")


def segment_key(skill_type: str, segment_index: int) -> str:
    """段级次数 / breakdown 的统一键。"""
    return f"{skill_type}:{segment_index}"


def parse_segment_key(key: str) -> tuple[str, int]:
    """解析段键；无法解析时视为第 1 段。"""
    if ":" in key:
        skill_type, index_text = key.split(":", 1)
        try:
            return skill_type, max(1, int(index_text))
        except ValueError:
            return skill_type, 1
    return key, 1


def segment_multiplier_at_level(
    char_data: dict[str, Any],
    field_name: str,
    *,
    skill_level: int,
    segment_index: int,
) -> float | None:
    """读取指定段在指定等级下的倍率（小数）；无有效倍率返回 None。"""
    if skill_level <= 0:
        return None
    segments = char_data.get(field_name)
    if not isinstance(segments, list) or not segments:
        return None
    if not (1 <= segment_index <= len(segments)):
        return None
    segment = segments[segment_index - 1]
    if not isinstance(segment, list) or not segment:
        return None
    idx = skill_level - 1
    if not (0 <= idx < len(segment)):
        return None
    raw = segment[idx]
    if raw is None:
        return None
    return float(raw) / 100.0


def build_segment_scenarios_from_levels(
    char_data: dict[str, Any],
    *,
    skill_1_level: int,
    skill_2_level: int,
    skill_3_level: int,
) -> list[SkillScenario]:
    """按左侧技能等级构建全部有效段场景（每段独立倍率）。"""
    skill_levels = (skill_1_level, skill_2_level, skill_3_level)
    scenarios: list[SkillScenario] = []
    for (skill_type, field_name, _), skill_level in zip(CHARACTER_SKILL_TYPES, skill_levels):
        if skill_level <= 0:
            continue
        segments = char_data.get(field_name)
        if not isinstance(segments, list) or not segments:
            continue
        for segment_index in range(1, len(segments) + 1):
            multiplier = segment_multiplier_at_level(
                char_data,
                field_name,
                skill_level=skill_level,
                segment_index=segment_index,
            )
            if multiplier is None:
                continue
            damage_type, explicit = resolve_segment_damage_type(char_data, field_name, segment_index)
            scenarios.append(
                SkillScenario(
                    skill_name=segment_key(skill_type, segment_index),
                    skill_multiplier=multiplier,
                    skill_type=skill_type,
                    segment_index=segment_index,
                    damage_type=damage_type,
                    damage_type_explicit=explicit,
                )
            )
    return scenarios


def normalize_manual_segment_counts(
    manual_counts: dict[str, int],
    scenarios: list[SkillScenario],
) -> dict[str, int]:
    """
    将手动次数规范为段级键。

    - 已是 ``战技:1`` 形式：原样保留（非负整数）
    - 旧 ``战技`` 形式：映射到该技能第 1 段（若存在）
    - 未出现在 scenarios 中的键丢弃
    """
    valid_keys = {scenario.scenario_key for scenario in scenarios}
    normalized: dict[str, int] = {key: 0 for key in valid_keys}

    for raw_key, raw_value in (manual_counts or {}).items():
        count = max(0, int(raw_value))
        if count <= 0:
            continue
        if ":" in raw_key:
            if raw_key in valid_keys:
                normalized[raw_key] = count
            continue
        # 旧技能类型键 → 第 1 段
        legacy_key = segment_key(raw_key, 1)
        if legacy_key in valid_keys:
            normalized[legacy_key] = count

    return normalized


def resolve_active_segment_counts(
    manual_counts: dict[str, int],
    scenarios: list[SkillScenario],
) -> dict[str, int]:
    """规范化后仅返回次数 > 0 的段。"""
    normalized = normalize_manual_segment_counts(manual_counts, scenarios)
    return {key: value for key, value in normalized.items() if value > 0}


def scenario_counts_for_eval(
    manual_counts: dict[str, int] | None,
    scenarios: list[SkillScenario],
    *,
    selected_skill_type: str = "战技",
    use_manual: bool = False,
) -> dict[str, int]:
    """
    解析用于评分的段级次数。

    未开手动次数：仅 ``selected_skill_type`` 第 1 段计 1 次。
    """
    if use_manual and manual_counts is not None:
        counts = normalize_manual_segment_counts(manual_counts, scenarios)
        if any(v > 0 for v in counts.values()):
            return counts
        raise ValueError("手动次数不能全为 0，请至少设置一项 > 0。")

    first_key = segment_key(selected_skill_type, 1)
    valid = {s.scenario_key for s in scenarios}
    if first_key in valid:
        return {first_key: 1}
    if scenarios:
        return {scenarios[0].scenario_key: 1}
    return {segment_key("战技", 1): 1}


def format_segment_count_label(counts: dict[str, int]) -> str:
    """弹窗/作业用的次数说明（仅 >0 的段）。"""
    parts: list[str] = []
    for skill_type in SKILL_TYPE_ORDER:
        keys = sorted(
            (key for key in counts if parse_segment_key(key)[0] == skill_type and counts[key] > 0),
            key=lambda k: parse_segment_key(k)[1],
        )
        for key in keys:
            _, seg = parse_segment_key(key)
            parts.append(f"{skill_type}第{seg}段×{counts[key]}")
    return " + ".join(parts) if parts else "（无有效次数）"


def segment_display_label(
    scenario_key: str,
    *,
    multiplier_percent: float | None = None,
    damage_type_display: str | None = None,
) -> str:
    """GUI 行标签，如 ``连携技 第2段 (400%) · 灼热``。"""
    skill_type, seg = parse_segment_key(scenario_key)
    if multiplier_percent is None:
        base = f"{skill_type} 第{seg}段"
    else:
        pct = multiplier_percent
        if pct == int(pct):
            pct_text = f"{int(pct)}%"
        else:
            pct_text = f"{format(pct, 'g')}%"
        base = f"{skill_type} 第{seg}段 ({pct_text})"
    if damage_type_display:
        return f"{base} · {damage_type_display}"
    return base


def list_segment_count_specs(
    char_data: dict[str, Any],
    *,
    skill_1_level: int,
    skill_2_level: int,
    skill_3_level: int,
) -> list[dict[str, Any]]:
    """供 GUI 动态行的段规格（键、标签、倍率%）。"""
    specs: list[dict[str, Any]] = []
    skill_levels = (skill_1_level, skill_2_level, skill_3_level)
    for (skill_type, field_name, _), skill_level in zip(CHARACTER_SKILL_TYPES, skill_levels):
        if skill_level <= 0:
            continue
        segments = char_data.get(field_name)
        if not isinstance(segments, list) or not segments:
            continue
        for segment_index in range(1, len(segments) + 1):
            multiplier = segment_multiplier_at_level(
                char_data,
                field_name,
                skill_level=skill_level,
                segment_index=segment_index,
            )
            if multiplier is None:
                continue
            key = segment_key(skill_type, segment_index)
            damage_type, explicit = resolve_segment_damage_type(char_data, field_name, segment_index)
            type_display = format_damage_type_display(damage_type, is_default=not explicit)
            specs.append(
                {
                    "key": key,
                    "label": segment_display_label(
                        key,
                        multiplier_percent=multiplier * 100.0,
                        damage_type_display=type_display,
                    ),
                    "skill_type": skill_type,
                    "segment_index": segment_index,
                    "damage_type": damage_type,
                    "damage_type_display": type_display,
                }
            )
    return specs


def aggregate_weighted_damage(
    segment_breakdown: dict[str, float],
    counts: dict[str, int],
) -> tuple[float, dict[str, float], dict[str, float]]:
    """
    计算加权总伤、各段总伤、各技能类型总伤。

    segment_breakdown：每段单次伤害；counts：段级次数。
    """
    segment_totals: dict[str, float] = {}
    skill_type_totals: dict[str, float] = {name: 0.0 for name in SKILL_TYPE_ORDER}
    weighted_total = 0.0
    for key, single_hit in segment_breakdown.items():
        count = max(0, int(counts.get(key, 0)))
        if count <= 0:
            continue
        seg_total = float(single_hit) * count
        segment_totals[key] = seg_total
        weighted_total += seg_total
        skill_type, _ = parse_segment_key(key)
        skill_type_totals[skill_type] = skill_type_totals.get(skill_type, 0.0) + seg_total
    skill_type_totals = {k: v for k, v in skill_type_totals.items() if v > 0}
    return weighted_total, segment_totals, skill_type_totals


def format_segment_breakdown_lines(
    segment_breakdown: dict[str, float],
    counts: dict[str, int],
    *,
    indent: str = "       ",
) -> list[str]:
    """格式化段级 / 技能级分项文案（用于预览与全量弹窗）。"""
    _, segment_totals, skill_type_totals = aggregate_weighted_damage(segment_breakdown, counts)
    if not segment_totals:
        return []
    lines: list[str] = []
    for skill_type in SKILL_TYPE_ORDER:
        seg_keys = sorted(
            (k for k in segment_totals if parse_segment_key(k)[0] == skill_type),
            key=lambda k: parse_segment_key(k)[1],
        )
        if not seg_keys:
            continue
        for key in seg_keys:
            single = segment_breakdown.get(key, 0.0)
            total = segment_totals[key]
            _, seg = parse_segment_key(key)
            count = counts.get(key, 0)
            lines.append(f"{indent}{skill_type} 第{seg}段: 单次 {single:.1f} ×{count} = {total:.1f}")
        if len(seg_keys) > 1:
            lines.append(f"{indent}{skill_type} 合计: {skill_type_totals[skill_type]:.1f}")
    return lines
