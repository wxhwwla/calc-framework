#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单段伤害引擎（15 乘区链）。

核心设计：
- 严格遵循《明日方舟：终末地》游戏内伤害计算公式
- 15 个乘区按固定顺序连乘，顺序与游戏文档完全一致
- 支持三种暴击模式：非暴击、期望暴击、必定暴击
- 支持伤害类型、技能类型、失衡状态的效果作用域过滤

流程概要：
1. ``DamageContext`` 提供最终攻击力、技能倍率、敌防/抗性、各类加成基数等输入参数；
2. ``DamageEffect`` 列表（武器特殊能力、装备词条、套装效果）经 ``_collect_effects`` 过滤到当前伤害/技能类型；
3. 各效果累加到对应乘区（见 ``ZONE_ORDER``），最后连乘得到 ``final_damage``；
4. 返回 ``DamageResult``，包含最终伤害值、15 个乘区的明细值、警告信息和未识别效果。

搜索场景下 ``evaluate_task`` 会把装备平铺四维与攻击力% 并入 ``final_attack`` 后再调用本模块。

乘区说明（按结算顺序）：
1. 基础伤害区 = 最终攻击力 × 技能倍率
2. 暴击区 = 1.0（非暴击）/ 1.0+暴击伤害（必定暴击）/ 1.0+暴击率×暴击伤害（期望）
3. 伤害加成区 = 1.0 + 伤害类型加成 + 技能类型加成 + 失衡加成 + 其他加成
4. 伤害减免区 = 连乘(1.0 - 伤害减免值)
5. 增幅区 = 1.0 + 所有增幅值之和
6. 虚弱区 = 连乘(1.0 - 虚弱值)
7. 庇护区 = 1.0 - max(所有庇护值)
8. 脆弱区 = 1.0 + 所有脆弱值之和
9. 易伤区 = 1.0 + 所有易伤值之和
10. 防御区 = 100 / (100 + 敌方防御)（真实伤害时为 1.0）
11. 失衡易伤区 = 失衡易伤系数（失衡时）/ 1.0（非失衡时）
12. 抗性区 = 1.0 - 抗性/100 + 无视抗性/100
13. 非主控减伤区 = 连乘(1.0 - 非主控减伤值)
14. 连击增伤区 = 1.0 + 所有连击增伤值之和
15. 特殊乘区 = 连乘所有特殊乘区值
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

from calculation.damage.types import damage_type_matches_context

CritMode = Literal["non_crit", "expected", "always_crit"]
"""暴击模式类型：
- non_crit: 非暴击模式，暴击区固定为 1.0
- expected: 期望模式，暴击区 = 1.0 + 暴击率 × 暴击伤害
- always_crit: 必定暴击模式，暴击区 = 1.0 + 暴击伤害
"""

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
"""已知效果类型集合，用于验证和分类 DamageEffect"""


@dataclass(frozen=True)
class DamageContext:
    """单段伤害计算的输入上下文。

    包含计算单段伤害所需的所有基础参数，由外部调用方（如搜索优化器）预先计算好传入。

    Attributes:
        final_attack: 最终攻击力，已包含基础攻击、属性加成、武器攻击加成等所有攻击力来源
        skill_multiplier: 技能倍率，由技能等级和类型决定
        damage_type: 伤害类型（物理/元素/真实等），用于过滤效果作用域
        skill_type: 技能类型（普攻/战技/终结技等），用于过滤效果作用域
        is_unbalanced: 是否为失衡状态，影响失衡易伤区和相关效果
        is_true_damage: 是否为真实伤害，真实伤害无视防御区
        enemy_defense: 敌方防御力基础值
        enemy_resistance: 敌方对应伤害类型的抗性基础值（百分比）
        ignore_resistance: 无视抗性百分比
        imbalance_vulnerability_coeff: 失衡易伤系数，默认 1.3（30% 额外伤害）
        crit_rate: 暴击率（0.0-1.0）
        crit_damage: 暴击伤害倍率（如 0.5 表示 50% 额外伤害）
        damage_type_bonus: 伤害类型加成（如物理伤害加成）
        skill_type_bonus: 技能类型加成（如战技伤害加成）
        imbalance_damage_bonus: 失衡状态下的额外伤害加成
        other_damage_bonus: 其他伤害加成（无法归类到上述类别的加成）
    """

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
    """统一的伤害效果输入结构。

    用于表示武器特殊能力、装备词条、套装效果等各类伤害相关效果。

    Attributes:
        effect_type: 效果类型，必须是 KNOWN_EFFECT_TYPES 中的一种
        value: 效果数值
        stack_rule: 叠加规则，默认为 "add"（加法叠加）
        damage_types: 适用的伤害类型列表，为空则不限制
        skill_types: 适用的技能类型列表，为空则不限制
        require_unbalanced: 是否要求失衡状态，None 表示不限制
        source: 效果来源（如武器名、装备名），用于日志和调试
        raw_text: 原始文本描述，用于展示和调试
    """

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
    """单段伤害计算的输出结果。

    包含最终伤害值、各乘区明细、警告信息和未识别效果。

    Attributes:
        final_damage: 最终计算得到的单段伤害值
        zone_values: 15 个乘区的具体数值，按 ZONE_ORDER 顺序排列
        crit_mode: 使用的暴击模式
        warnings: 计算过程中产生的警告信息（如未识别效果）
        unknown_effects: 未识别的效果列表，包含效果类型、来源和原始文本
    """

    final_damage: float
    zone_values: dict[str, float]
    crit_mode: CritMode
    warnings: tuple[str, ...]
    unknown_effects: tuple[dict[str, str], ...]


def _clamp(value: float, lower: float, upper: Optional[float] = None) -> float:
    """将值限制在指定范围内。

    Args:
        value: 要限制的值
        lower: 下限
        upper: 上限（可选）

    Returns:
        限制后的值，确保 >= lower 且（如果指定了 upper）<= upper
    """
    value = max(lower, value)
    if upper is not None:
        value = min(upper, value)
    return value


def _resolve_crit_zone(ctx: DamageContext, mode: CritMode) -> float:
    """根据暴击模式计算暴击区的值。

    Args:
        ctx: 伤害上下文，包含暴击率和暴击伤害
        mode: 暴击模式

    Returns:
        暴击区的计算结果：
        - non_crit: 1.0（不暴击）
        - expected: 1.0 + 暴击率 × 暴击伤害（期望伤害）
        - always_crit: 1.0 + 暴击伤害（必定暴击）
    """
    crit_rate = _clamp(float(ctx.crit_rate), 0.0, 1.0)
    crit_damage = _clamp(float(ctx.crit_damage), 0.0)
    if mode == "always_crit":
        return 1.0 + crit_damage
    if mode == "expected":
        return 1.0 + crit_rate * crit_damage
    return 1.0


def _match_scope(ctx: DamageContext, effect: DamageEffect) -> bool:
    """检查效果是否适用于当前伤害上下文。

    根据伤害类型、技能类型和失衡状态判断效果是否应该生效。

    Args:
        ctx: 伤害上下文
        effect: 要检查的效果

    Returns:
        True 如果效果适用于当前上下文，否则 False
    """
    if effect.damage_types and not damage_type_matches_context(ctx.damage_type, effect.damage_types):
        return False
    if effect.skill_types and ctx.skill_type not in effect.skill_types:
        return False
    if effect.require_unbalanced is not None and ctx.is_unbalanced != effect.require_unbalanced:
        return False
    return True


def _collect_effects(
    ctx: DamageContext, effects: list[DamageEffect]
) -> tuple[list[DamageEffect], tuple[dict[str, str], ...], tuple[str, ...]]:
    """收集并分类效果，过滤掉不适用和未识别的效果。

    Args:
        ctx: 伤害上下文，用于过滤效果作用域
        effects: 所有待处理的效果列表

    Returns:
        三元组：
        - 适用的已知效果列表
        - 未识别效果列表（包含类型、来源、原始文本）
        - 警告信息列表
    """
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
    """计算单段伤害并返回 15 乘区明细。

    核心伤害计算函数，严格按照 15 乘区顺序连乘计算最终伤害。

    Args:
        context: 伤害上下文，包含攻击力、技能倍率、敌方属性等所有基础参数
        effects: 伤害效果列表（可选），包含武器特殊能力、装备词条、套装效果等
        crit_mode: 暴击模式，默认为非暴击模式

    Returns:
        DamageResult 对象，包含最终伤害值、各乘区明细、警告信息和未识别效果
    """
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
