#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
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

from calc_engine.endfield.calc.damage.types import damage_type_matches_context

from .types import KNOWN_EFFECT_TYPES, CritMode, DamageContext, DamageEffect


def _clamp(value: float, lower: float, upper: float | None = None) -> float:
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
    return not (effect.require_unbalanced is not None and ctx.is_unbalanced != effect.require_unbalanced)


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
            warnings.append(f"检测到未识别效果：{effect.effect_type}（来源：{effect.source or '未知来源'}）")
            continue
        if _match_scope(ctx, effect):
            known.append(effect)
    return known, tuple(unknown), tuple(warnings)
