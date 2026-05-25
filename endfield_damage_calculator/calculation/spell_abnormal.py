#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""法术异常/爆发伤害计算（导电/腐蚀/燃烧/冻结 + 同属性爆发）。"""

from __future__ import annotations

from dataclasses import dataclass

from calculation.damage_engine import CritMode, DamageContext, DamageEffect, calculate_single_hit_damage
from calculation.spell_abnormal_params import (
    SPELL_ABNORMAL_PARAM_ROWS,
    SPELL_LEVEL_COEFF_DIVISOR,
    SpellFormulaKind,
    base_multiplier_for_formula,
    calc_level_from_ui,
    preview_level_multipliers,
)


@dataclass(frozen=True)
class SpellAbnormalDef:
    """法术异常/爆发条目定义。"""

    key: str
    damage_type: str
    event_kind: str  # 异常 / 爆发
    formula: SpellFormulaKind
    game_name: str


_SPELL_DEFS: tuple[SpellAbnormalDef, ...] = (
    *(
        SpellAbnormalDef(
            key=str(row["key"]),
            damage_type=str(row["damage_type"]),
            event_kind=str(row["event_kind"]),
            formula=row["formula"],
            game_name=str(row["game_name"]),
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


def _spell_level_coeff(char_level: int) -> float:
    """法术异常/爆发等级系数区：1 + (触发者等级 - 1) / 196。"""
    return 1.0 + (max(1, int(char_level)) - 1.0) / SPELL_LEVEL_COEFF_DIVISOR


def _skill_multiplier(defn: SpellAbnormalDef, ui_level: int, *, char_level: int) -> float:
    calc_level = calc_level_from_ui(ui_level)
    base = base_multiplier_for_formula(defn.formula, calc_level=calc_level)
    return base * _spell_level_coeff(char_level)


def get_spell_abnormal_param_snapshot() -> dict[str, dict[str, object]]:
    """返回当前法术异常参数快照（供测试/校验）。"""
    return {
        item.key: {
            "damage_type": item.damage_type,
            "event_kind": item.event_kind,
            "formula": item.formula,
            "game_name": item.game_name,
            "level_multipliers": preview_level_multipliers(item.formula),
        }
        for item in _SPELL_DEFS
    }


def evaluate_spell_abnormal_total(
    *,
    context: DamageContext,
    crit_mode: CritMode,
    effects: list[DamageEffect],
    counts: dict[str, int] | None,
    char_level: int = 1,
) -> tuple[float, dict[str, float]]:
    """计算法术异常总伤与单次分项（key 为 ``异常名:等级``）。"""
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
            multiplier = _skill_multiplier(defn, ui_level, char_level=char_level)
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
            label = defn.game_name
            if defn.event_kind == "爆发":
                label = "爆发"
            lines.append(
                f"{indent}{abnormal}({label}) Lv{level}: 单次 {single:.1f} ×{count} = {total:.1f}"
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
