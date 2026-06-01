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

from dataclasses import dataclass
from typing import Literal

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
        base_damage_bonus: 基础伤害提升值（与攻击力×倍率相加，NGA §1.1）
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
    base_damage_bonus: float = 0.0


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
    require_unbalanced: bool | None = None
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
