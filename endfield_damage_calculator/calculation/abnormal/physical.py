#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""物理异常（倒地/击飞/碎甲/猛击）加权伤害计算。"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from calculation.damage.engine import CritMode, DamageContext, DamageEffect, calculate_single_hit_damage

PHYSICAL_ABNORMAL_TYPES: tuple[str, ...] = ("倒地", "击飞", "碎甲", "猛击")
PHYSICAL_ABNORMAL_LEVELS: tuple[int, ...] = (0, 1, 2, 3, 4)

_BINARY_ABNORMAL_TYPES = frozenset({"倒地", "击飞"})


def abnormal_levels_for(abnormal: str) -> tuple[int, ...]:
    if abnormal in _BINARY_ABNORMAL_TYPES:
        return (0, 1)
    return (0, 1, 2, 3, 4)

_CRIT_RATE_RE = re.compile(r"暴击率\+?\s*([+-]?\d+(?:\.\d+)?)\s*%")
_CRIT_DAMAGE_RE = re.compile(r"暴击伤害\+?\s*([+-]?\d+(?:\.\d+)?)\s*%")
_CONDITIONAL_HINTS = ("当", "触发", "叠加", "持续", "命中后", "若", "如果")


@dataclass(frozen=True)
class PhysicalAbnormalProfile:
    """物理异常手动次数 + 伤害口径设置。"""

    damage_component_mode: str = "skill_and_abnormal"
    use_expected_crit: bool = False
    include_conditional_equipment_crit: bool = False
    extra_crit_rate: float = 0.0
    extra_crit_damage: float = 0.0
    counts: dict[str, int] | None = None


def _normalized_component_mode(mode: str) -> str:
    text = str(mode or "").strip()
    if text in ("skill_only", "abnormal_only", "skill_and_abnormal"):
        return text
    if text == "仅技能":
        return "skill_only"
    if text == "仅异常":
        return "abnormal_only"
    if text in ("技能+异常", "技能＋异常"):
        return "skill_and_abnormal"
    return "skill_and_abnormal"


def normalize_abnormal_counts(counts: dict[str, int] | None) -> dict[str, int]:
    normalized: dict[str, int] = {}
    for abnormal in PHYSICAL_ABNORMAL_TYPES:
        for level in abnormal_levels_for(abnormal):
            key = f"{abnormal}:{level}"
            raw = 0 if counts is None else int(counts.get(key, 0))
            normalized[key] = max(0, raw)
    return normalized


def is_physical_abnormal_key(key: str) -> bool:
    """是否为物理异常分项键（如 ``猛击:3``）。"""
    if ":" not in str(key):
        return False
    name, level = str(key).split(":", 1)
    if name not in PHYSICAL_ABNORMAL_TYPES:
        return False
    try:
        lv = int(level)
    except (TypeError, ValueError):
        return False
    return lv in abnormal_levels_for(name)


def split_damage_breakdown(
    breakdown: dict[str, float] | None,
) -> tuple[dict[str, float], dict[str, float]]:
    """拆分 ``segment_breakdown`` 为技能分项与异常分项。"""
    src = dict(breakdown or {})
    skill_part: dict[str, float] = {}
    abnormal_part: dict[str, float] = {}
    for key, value in src.items():
        if is_physical_abnormal_key(key):
            abnormal_part[key] = float(value)
        else:
            skill_part[key] = float(value)
    return skill_part, abnormal_part


def abnormal_weighted_total(
    single_hit_breakdown: dict[str, float] | None,
    counts: dict[str, int] | None,
) -> float:
    """按异常次数累加总伤（单次伤害 × 次数）。"""
    totals = 0.0
    normalized = normalize_abnormal_counts(counts)
    for key, single in (single_hit_breakdown or {}).items():
        count = normalized.get(key, 0)
        if count <= 0:
            continue
        totals += float(single) * float(count)
    return totals


def format_abnormal_breakdown_lines(
    single_hit_breakdown: dict[str, float] | None,
    counts: dict[str, int] | None,
    *,
    indent: str = "  ",
) -> list[str]:
    """格式化异常分项展示行。"""
    lines: list[str] = []
    normalized = normalize_abnormal_counts(counts)
    for abnormal in PHYSICAL_ABNORMAL_TYPES:
        for level in abnormal_levels_for(abnormal):
            key = f"{abnormal}:{level}"
            count = normalized.get(key, 0)
            if count <= 0:
                continue
            single = float((single_hit_breakdown or {}).get(key, 0.0))
            total = single * float(count)
            lines.append(f"{indent}{abnormal} Lv{level}: 单次 {single:.1f} ×{count} = {total:.1f}")
    return lines


def _base_multiplier(abnormal: str, calc_level: int) -> float:
    if abnormal in ("倒地", "击飞"):
        return 1.2
    if abnormal == "碎甲":
        return 0.5 * float(calc_level)
    if abnormal == "猛击":
        return 1.5 * float(calc_level)
    return 0.0


def _physical_level_coeff(char_level: int) -> float:
    return 1.0 + (max(1, int(char_level)) - 1.0) / 392.0


def _effect_text(effect: DamageEffect) -> str:
    text = str(effect.raw_text or effect.effect_type or "").strip()
    return text


def _is_conditional_crit_text(text: str) -> bool:
    return any(token in text for token in _CONDITIONAL_HINTS)


def _extract_percent(text: str, pattern: re.Pattern[str]) -> float:
    match = pattern.search(text)
    if not match:
        return 0.0
    try:
        return float(match.group(1)) / 100.0
    except (TypeError, ValueError):
        return 0.0


def extract_equipment_crit_bonus(
    effects: list[DamageEffect],
    *,
    include_conditional: bool,
) -> tuple[float, float]:
    """从装备效果文本抽取暴击率/暴伤加成。"""
    crit_rate = 0.0
    crit_damage = 0.0
    for effect in effects:
        text = _effect_text(effect)
        if not text:
            continue
        if "暴击" not in text:
            continue
        if not include_conditional and _is_conditional_crit_text(text):
            continue
        crit_rate += _extract_percent(text, _CRIT_RATE_RE)
        crit_damage += _extract_percent(text, _CRIT_DAMAGE_RE)
    return crit_rate, crit_damage


def extract_weapon_crit_bonus(weapon_data: Optional[dict], *, weapon_level: int) -> tuple[float, float]:
    """从武器静态字段抽取暴击率/暴伤（不处理条件触发）。"""
    if not weapon_data:
        return 0.0, 0.0
    idx = max(0, int(weapon_level) - 1)

    def _read_percent(key: str) -> float:
        raw = weapon_data.get(key, 0.0)
        if isinstance(raw, list):
            if not raw:
                return 0.0
            pos = max(0, min(idx, len(raw) - 1))
            raw = raw[pos]
        try:
            return float(raw) / 100.0
        except (TypeError, ValueError):
            return 0.0

    return _read_percent("暴击率+"), _read_percent("暴击伤害+")


def evaluate_physical_abnormal_total(
    *,
    context: DamageContext,
    crit_mode: CritMode,
    effects: list[DamageEffect],
    counts: dict[str, int] | None,
    char_level: int,
) -> tuple[float, dict[str, float]]:
    """计算物理异常总伤与单次分项（key 为 '异常:等级'）。"""
    normalized = normalize_abnormal_counts(counts)
    level_coeff = _physical_level_coeff(char_level)
    total = 0.0
    breakdown: dict[str, float] = {}
    for abnormal in PHYSICAL_ABNORMAL_TYPES:
        for ui_level in abnormal_levels_for(abnormal):
            count = normalized.get(f"{abnormal}:{ui_level}", 0)
            if count <= 0:
                continue
            calc_level = ui_level + 1
            multiplier = _base_multiplier(abnormal, calc_level) * level_coeff
            if multiplier <= 0:
                continue
            result = calculate_single_hit_damage(
                DamageContext(
                    final_attack=float(context.final_attack),
                    skill_multiplier=multiplier,
                    damage_type="物理",
                    skill_type="异常",
                    is_unbalanced=context.is_unbalanced,
                    is_true_damage=context.is_true_damage,
                    enemy_defense=context.enemy_defense,
                    enemy_resistance=context.enemy_resistance,
                    ignore_resistance=context.ignore_resistance,
                    imbalance_vulnerability_coeff=context.imbalance_vulnerability_coeff,
                    crit_rate=context.crit_rate,
                    crit_damage=context.crit_damage,
                    # 异常不吃技能增伤，只吃伤害类型/其他等通用加成
                    damage_type_bonus=context.damage_type_bonus,
                    skill_type_bonus=0.0,
                    imbalance_damage_bonus=context.imbalance_damage_bonus,
                    other_damage_bonus=context.other_damage_bonus,
                ),
                effects=effects,
                crit_mode=crit_mode,
            )
            single_hit = float(result.final_damage)
            key = f"{abnormal}:{ui_level}"
            breakdown[key] = single_hit
            total += single_hit * float(count)
    return total, breakdown


def compose_damage_total(
    *,
    skill_damage: float,
    abnormal_damage: float,
    mode: str,
) -> float:
    """按“仅技能/仅异常/技能+异常”拼装最终评分。"""
    normalized = _normalized_component_mode(mode)
    if normalized == "skill_only":
        return skill_damage
    if normalized == "abnormal_only":
        return abnormal_damage
    return skill_damage + abnormal_damage
