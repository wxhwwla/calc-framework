#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单段伤害引擎（15 乘区链）。

流程概要：
1. ``DamageContext`` 提供最终攻击力、技能倍率、敌防/抗性、各类加成基数等；
2. ``DamageEffect`` 列表（武器特殊能力、装备词条、套装效果）经 ``_collect_effects`` 过滤到当前伤害/技能类型；
3. 各效果累加到对应乘区（见 ``ZONE_ORDER``），最后连乘得到 ``final_damage``。

搜索场景下 ``evaluate_task`` 会把装备平铺四维与攻击力% 并入 ``final_attack`` 后再调用本模块。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

CritMode = Literal["non_crit", "expected", "always_crit"]

# 乘区连乘顺序（与游戏文档一致；展示与结算均按此顺序）
ZONE_ORDER = (
    "基础伤害区",
    "暴击区",
    "伤害加成区",
    "伤害减免区",
    "增幅区",
    "虚弱区",
    "庇护区",
    "脆弱区",
    "易伤区",
    "防御区",
    "失衡易伤区",
    "抗性区",
    "非主控减伤区",
    "连击增伤区",
    "特殊乘区",
)

KNOWN_EFFECT_TYPES = frozenset(
    {
        "伤害减免",
        "增幅",
        "虚弱",
        "庇护",
        "脆弱",
        "易伤",
        "连击增伤",
        "伤害类型伤害加成",
        "技能类型伤害加成",
        "失衡伤害加成",
        "其他伤害加成",
        "无视抗性",
        "抗性",
        "防御",
        "失衡易伤系数",
        "非主控减伤",
        "特殊乘区",
    }
)


@dataclass(frozen=True)
class DamageContext:
    """单段伤害输入。"""

    final_attack: float
    skill_multiplier: float = 1.0
    damage_type: str = "物理"
    skill_type: str = "战技"
    is_unbalanced: bool = False
    is_true_damage: bool = False
    enemy_defense: float = 100.0
    enemy_resistance: float = 0.0
    ignore_resistance: float = 0.0
    imbalance_vulnerability_coeff: float = 1.3
    crit_rate: float = 0.05
    crit_damage: float = 0.5
    damage_type_bonus: float = 0.0
    skill_type_bonus: float = 0.0
    imbalance_damage_bonus: float = 0.0
    other_damage_bonus: float = 0.0


@dataclass(frozen=True)
class DamageEffect:
    """统一效果输入结构。"""

    effect_type: str
    value: float
    stack_rule: str = "add"
    damage_types: tuple[str, ...] = ()
    skill_types: tuple[str, ...] = ()
    require_unbalanced: Optional[bool] = None
    source: str = ""
    raw_text: str = ""


@dataclass(frozen=True)
class DamageResult:
    """单段伤害输出。"""

    final_damage: float
    zone_values: dict[str, float]
    crit_mode: CritMode
    warnings: tuple[str, ...]
    unknown_effects: tuple[dict[str, str], ...]


def _clamp(value: float, lower: float, upper: Optional[float] = None) -> float:
    value = max(lower, value)
    if upper is not None:
        value = min(upper, value)
    return value


def _resolve_crit_zone(ctx: DamageContext, mode: CritMode) -> float:
    crit_rate = _clamp(float(ctx.crit_rate), 0.0, 1.0)
    crit_damage = _clamp(float(ctx.crit_damage), 0.0)
    if mode == "always_crit":
        return 1.0 + crit_damage
    if mode == "expected":
        return 1.0 + crit_rate * crit_damage
    return 1.0


def _match_scope(ctx: DamageContext, effect: DamageEffect) -> bool:
    if effect.damage_types and ctx.damage_type not in effect.damage_types:
        return False
    if effect.skill_types and ctx.skill_type not in effect.skill_types:
        return False
    if effect.require_unbalanced is not None and ctx.is_unbalanced != effect.require_unbalanced:
        return False
    return True


def _collect_effects(
    ctx: DamageContext, effects: list[DamageEffect]
) -> tuple[list[DamageEffect], tuple[dict[str, str], ...], tuple[str, ...]]:
    known: list[DamageEffect] = []
    unknown: list[dict[str, str]] = []
    warnings: list[str] = []
    for effect in effects:
        if effect.effect_type not in KNOWN_EFFECT_TYPES:
            unknown_item = {
                "effect_type": effect.effect_type,
                "source": effect.source,
                "raw_text": effect.raw_text,
            }
            unknown.append(unknown_item)
            warnings.append(
                f"检测到未识别效果：{effect.effect_type}（来源：{effect.source or '未知来源'}）"
            )
            continue
        if _match_scope(ctx, effect):
            known.append(effect)
    return known, tuple(unknown), tuple(warnings)


def calculate_single_hit_damage(
    context: DamageContext,
    *,
    effects: Optional[list[DamageEffect]] = None,
    crit_mode: CritMode = "non_crit",
) -> DamageResult:
    """计算单段伤害并返回 15 乘区明细。"""
    all_effects = effects or []
    known_effects, unknown_effects, warnings = _collect_effects(context, all_effects)

    damage_bonus = (
        1.0
        + float(context.damage_type_bonus)
        + float(context.skill_type_bonus)
        + float(context.imbalance_damage_bonus)
        + float(context.other_damage_bonus)
    )
    damage_reduction = 1.0
    amplification = 1.0
    weakness = 1.0
    shelter_values: list[float] = []
    fragile = 1.0
    vulnerability = 1.0
    combo_bonus = 1.0
    non_control_reduction = 1.0
    special_zone = 1.0
    resistance_extra = 0.0
    resistance_change = 0.0
    defense_change = 0.0
    imbalance_coeff_override: Optional[float] = None

    for effect in known_effects:
        value = float(effect.value)
        if effect.effect_type == "伤害减免":
            damage_reduction *= 1.0 - value
        elif effect.effect_type == "增幅":
            amplification += value
        elif effect.effect_type == "虚弱":
            weakness *= 1.0 - value
        elif effect.effect_type == "庇护":
            shelter_values.append(value)
        elif effect.effect_type == "脆弱":
            fragile += value
        elif effect.effect_type == "易伤":
            vulnerability += value
        elif effect.effect_type == "连击增伤":
            combo_bonus += value
        elif effect.effect_type == "伤害类型伤害加成":
            damage_bonus += value
        elif effect.effect_type == "技能类型伤害加成":
            damage_bonus += value
        elif effect.effect_type == "失衡伤害加成":
            damage_bonus += value
        elif effect.effect_type == "其他伤害加成":
            damage_bonus += value
        elif effect.effect_type == "无视抗性":
            resistance_extra += value
        elif effect.effect_type == "抗性":
            resistance_change += value
        elif effect.effect_type == "防御":
            defense_change += value
        elif effect.effect_type == "失衡易伤系数":
            imbalance_coeff_override = value
        elif effect.effect_type == "非主控减伤":
            non_control_reduction *= 1.0 - value
        elif effect.effect_type == "特殊乘区":
            special_zone *= value

    shelter = 1.0 - max(shelter_values, default=0.0)

    if context.is_true_damage:
        defense_zone = 1.0
    else:
        effective_defense = max(0.0, float(context.enemy_defense) + defense_change)
        defense_zone = 100.0 / (effective_defense + 100.0)

    resistance = float(context.enemy_resistance) + resistance_change
    ignore_res = float(context.ignore_resistance) + resistance_extra
    resistance_zone = 1.0 - resistance / 100.0 + ignore_res / 100.0

    imbalance_coeff = (
        float(imbalance_coeff_override)
        if imbalance_coeff_override is not None
        else float(context.imbalance_vulnerability_coeff)
    )
    imbalance_zone = imbalance_coeff if context.is_unbalanced else 1.0

    zone_values = {
        "基础伤害区": float(context.final_attack) * float(context.skill_multiplier),
        "暴击区": _resolve_crit_zone(context, crit_mode),
        "伤害加成区": damage_bonus,
        "伤害减免区": damage_reduction,
        "增幅区": amplification,
        "虚弱区": weakness,
        "庇护区": shelter,
        "脆弱区": fragile,
        "易伤区": vulnerability,
        "防御区": defense_zone,
        "失衡易伤区": imbalance_zone,
        "抗性区": resistance_zone,
        "非主控减伤区": non_control_reduction,
        "连击增伤区": combo_bonus,
        "特殊乘区": special_zone,
    }
    ordered_zone_values = {name: zone_values[name] for name in ZONE_ORDER}

    final_damage = 1.0
    for value in ordered_zone_values.values():
        final_damage *= float(value)

    return DamageResult(
        final_damage=final_damage,
        zone_values=ordered_zone_values,
        crit_mode=crit_mode,
        warnings=warnings,
        unknown_effects=unknown_effects,
    )
