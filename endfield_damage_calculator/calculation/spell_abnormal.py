#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""法术异常骨架（异常/爆发双轨；公式先占位，后续可替换）。"""

from __future__ import annotations

from dataclasses import dataclass

from calculation.damage_engine import CritMode, DamageContext, DamageEffect, calculate_single_hit_damage
from calculation.spell_abnormal_params import SPELL_ABNORMAL_PARAM_ROWS


@dataclass(frozen=True)
class SpellAbnormalDef:
    """法术异常/爆发条目定义。"""

    key: str
    damage_type: str
    event_kind: str  # 异常 / 爆发
    level_coeffs: tuple[float, float, float, float, float]  # 对应 UI Lv0~Lv4 的占位系数


_SPELL_DEFS: tuple[SpellAbnormalDef, ...] = (
    *(
        SpellAbnormalDef(
            key=str(row["key"]),
            damage_type=str(row["damage_type"]),
            event_kind=str(row["event_kind"]),
            level_coeffs=tuple(row["level_coeffs"]),
        )
        for row in SPELL_ABNORMAL_PARAM_ROWS
    ),
)

SPELL_ABNORMAL_TYPES: tuple[str, ...] = tuple(item.key for item in _SPELL_DEFS)
SPELL_ABNORMAL_LEVELS: tuple[int, ...] = (0, 1, 2, 3, 4)
_SPELL_DEF_BY_KEY: dict[str, SpellAbnormalDef] = {item.key: item for item in _SPELL_DEFS}


def normalize_spell_abnormal_counts(counts: dict[str, int] | None) -> dict[str, int]:
    normalized: dict[str, int] = {}
    for abnormal in SPELL_ABNORMAL_TYPES:
        for level in SPELL_ABNORMAL_LEVELS:
            key = f"{abnormal}:{level}"
            raw = 0 if counts is None else int(counts.get(key, 0))
            normalized[key] = max(0, raw)
    return normalized


def is_spell_abnormal_key(key: str) -> bool:
    if ":" not in str(key):
        return False
    name, level = str(key).split(":", 1)
    if name not in SPELL_ABNORMAL_TYPES:
        return False
    try:
        lv = int(level)
    except (TypeError, ValueError):
        return False
    return lv in SPELL_ABNORMAL_LEVELS


def get_spell_abnormal_param_snapshot() -> dict[str, dict[str, object]]:
    """返回当前法术异常参数快照（供测试/校验）。"""
    return {
        item.key: {
            "damage_type": item.damage_type,
            "event_kind": item.event_kind,
            "level_coeffs": tuple(item.level_coeffs),
        }
        for item in _SPELL_DEFS
    }


def _def_multiplier(defn: SpellAbnormalDef, ui_level: int) -> float:
    # 占位倍率：后续可按「异常/爆发」分别替换为正式公式
    idx = max(0, min(int(ui_level), len(defn.level_coeffs) - 1))
    return float(defn.level_coeffs[idx])


def evaluate_spell_abnormal_total(
    *,
    context: DamageContext,
    crit_mode: CritMode,
    effects: list[DamageEffect],
    counts: dict[str, int] | None,
) -> tuple[float, dict[str, float]]:
    """计算法术异常总伤与单次分项（首版占位）。"""
    normalized = normalize_spell_abnormal_counts(counts)
    total = 0.0
    breakdown: dict[str, float] = {}
    for abnormal in SPELL_ABNORMAL_TYPES:
        defn = _SPELL_DEF_BY_KEY.get(abnormal)
        if defn is None:
            continue
        for ui_level in SPELL_ABNORMAL_LEVELS:
            count = normalized.get(f"{abnormal}:{ui_level}", 0)
            if count <= 0:
                continue
            multiplier = _def_multiplier(defn, ui_level)
            if multiplier <= 0:
                continue
            result = calculate_single_hit_damage(
                DamageContext(
                    final_attack=float(context.final_attack),
                    skill_multiplier=multiplier,
                    damage_type=defn.damage_type,
                    skill_type="异常",
                    is_unbalanced=context.is_unbalanced,
                    is_true_damage=context.is_true_damage,
                    enemy_defense=context.enemy_defense,
                    enemy_resistance=context.enemy_resistance,
                    ignore_resistance=context.ignore_resistance,
                    imbalance_vulnerability_coeff=context.imbalance_vulnerability_coeff,
                    crit_rate=context.crit_rate,
                    crit_damage=context.crit_damage,
                    damage_type_bonus=context.damage_type_bonus,
                    # 异常不吃技能增伤
                    skill_type_bonus=0.0,
                    imbalance_damage_bonus=context.imbalance_damage_bonus,
                    other_damage_bonus=context.other_damage_bonus,
                ),
                effects=effects,
                crit_mode=crit_mode,
            )
            key = f"{abnormal}:{ui_level}"
            single_hit = float(result.final_damage)
            breakdown[key] = single_hit
            total += single_hit * float(count)
    return total, breakdown


def format_spell_abnormal_breakdown_lines(
    single_hit_breakdown: dict[str, float] | None,
    counts: dict[str, int] | None,
    *,
    indent: str = "  ",
) -> list[str]:
    lines: list[str] = []
    normalized = normalize_spell_abnormal_counts(counts)
    for abnormal in SPELL_ABNORMAL_TYPES:
        defn = _SPELL_DEF_BY_KEY.get(abnormal)
        if defn is None:
            continue
        for level in SPELL_ABNORMAL_LEVELS:
            key = f"{abnormal}:{level}"
            count = normalized.get(key, 0)
            if count <= 0:
                continue
            single = float((single_hit_breakdown or {}).get(key, 0.0))
            total = single * float(count)
            lines.append(
                f"{indent}{abnormal}({defn.event_kind}) Lv{level}: 单次 {single:.1f} ×{count} = {total:.1f}"
            )
    return lines


def spell_abnormal_weighted_total(
    single_hit_breakdown: dict[str, float] | None,
    counts: dict[str, int] | None,
) -> float:
    """按法术异常次数累加总伤（单次伤害 × 次数）。"""
    totals = 0.0
    normalized = normalize_spell_abnormal_counts(counts)
    for key, single in (single_hit_breakdown or {}).items():
        count = normalized.get(key, 0)
        if count <= 0:
            continue
        totals += float(single) * float(count)
    return totals
