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

from games.endfield.calc.damage.break_defense import damage_effects_from_break_defense
from games.endfield.calc.damage.combo_bonus import combo_zone_multiplier

from .helpers import _clamp, _collect_effects, _resolve_crit_zone
from .types import ZONE_ORDER, CritMode, DamageContext, DamageEffect, DamageResult

_logger = __import__("logging").getLogger(__name__)

DamagePipeline = str

# 上下文buff字段 → 效果类型名称的映射，用于检测重复叠加
_CONTEXT_BONUS_EFFECT_TYPES: dict[str, str] = {
    "damage_type_bonus": "伤害类型伤害加成",
    "skill_type_bonus": "技能类型伤害加成",
    "imbalance_damage_bonus": "失衡伤害加成",
    "other_damage_bonus": "其他伤害加成",
}

_CONTEXT_BUFF_MAP: dict[str, str] = {
    "暴击率": "crit_rate",
    "暴击伤害": "crit_damage",
    "伤害类型加成": "damage_type_bonus",
    "技能类型加成": "skill_type_bonus",
    "失衡伤害加成": "imbalance_damage_bonus",
    "其他伤害加成": "other_damage_bonus",
}


def _apply_manual_buffs(
    context: DamageContext,
    buffs: list[dict[str, str | float]],
) -> tuple[DamageContext, list[DamageEffect]]:
    extra_effects: list[DamageEffect] = []
    overrides: dict[str, float] = {}
    for entry in buffs:
        effect_type = str(entry.get("effect_type", "")).strip()
        value = float(entry.get("value", 0.0))
        if not effect_type:
            continue
        context_field = _CONTEXT_BUFF_MAP.get(effect_type)
        if context_field:
            overrides[context_field] = overrides.get(context_field, 0.0) + value
        else:
            extra_effects.append(
                DamageEffect(
                    effect_type=effect_type,
                    value=value,
                    source="手动buff",
                    raw_text=f"{effect_type}+{value * 100:.0f}%",
                )
            )
    if overrides:
        context = DamageContext(
            final_attack=context.final_attack,
            skill_multiplier=context.skill_multiplier,
            damage_type=context.damage_type,
            skill_type=context.skill_type,
            is_unbalanced=context.is_unbalanced,
            is_true_damage=context.is_true_damage,
            enemy_defense=context.enemy_defense,
            enemy_resistance=context.enemy_resistance,
            ignore_resistance=context.ignore_resistance,
            imbalance_vulnerability_coeff=context.imbalance_vulnerability_coeff,
            crit_rate=context.crit_rate + overrides.get("crit_rate", 0.0),
            crit_damage=context.crit_damage + overrides.get("crit_damage", 0.0),
            damage_type_bonus=context.damage_type_bonus + overrides.get("damage_type_bonus", 0.0),
            skill_type_bonus=context.skill_type_bonus + overrides.get("skill_type_bonus", 0.0),
            imbalance_damage_bonus=context.imbalance_damage_bonus + overrides.get("imbalance_damage_bonus", 0.0),
            other_damage_bonus=context.other_damage_bonus + overrides.get("other_damage_bonus", 0.0),
            base_damage_bonus=context.base_damage_bonus,
            combo_stacks=context.combo_stacks,
            break_defense_stacks=context.break_defense_stacks,
        )
    """apply manual buffs。"""
    return context, extra_effects


def calculate_single_hit_damage(
    context: DamageContext,
    *,
    effects: list[DamageEffect] | None = None,
    crit_mode: CritMode = "non_crit",
    manual_buffs: list[dict[str, str | float]] | None = None,
    damage_pipeline: DamagePipeline = "normal",
) -> DamageResult:
    """计算单段伤害并返回 15 乘区明细。

    核心伤害计算函数，严格按照 15 乘区顺序连乘计算最终伤害。

    Args:
        context: 伤害上下文，包含攻击力、技能倍率、敌方属性等所有基础参数
        effects: 伤害效果列表（可选），包含武器特殊能力、装备词条、套装效果等
        crit_mode: 暴击模式，默认为非暴击模式
        manual_buffs: 手动场外 buff 列表（可选），每条为 {"effect_type": str, "value": float}
            可选值：暴击率/暴击伤害/伤害类型加成/技能类型加成/失衡伤害加成/其他伤害加成/
            增幅/脆弱/易伤/伤害减免/连击增伤/特殊乘区

    Returns:
        DamageResult 对象，包含最终伤害值、各乘区明细、警告信息和未识别效果
    """
    buffs = manual_buffs or []
    if buffs:
        context, extra = _apply_manual_buffs(context, buffs)
    else:
        extra = []

    all_effects = list(effects or []) + extra + list(damage_effects_from_break_defense(context.break_defense_stacks))
    known_effects, unknown_effects, warnings = _collect_effects(context, all_effects)

    # 四种伤害加成分别追踪，传递给 DAG 时保留类型区分
    damage_type_bonus_total = 1.0 + float(context.damage_type_bonus)
    skill_type_bonus_total = 0.0 + float(context.skill_type_bonus)
    imbalance_damage_bonus_total = 0.0 + float(context.imbalance_damage_bonus)
    other_damage_bonus_total = 0.0 + float(context.other_damage_bonus)

    # ── 检测上下文与 effects 是否重复叠加同类型加成 ──
    _context_nonzero_bonus_fields = {
        ctx_field for ctx_field in _CONTEXT_BONUS_EFFECT_TYPES if getattr(context, ctx_field, 0.0) != 0.0
    }
    _seen_overlap_effect_types: set[str] = set()
    if effects and _context_nonzero_bonus_fields:
        _context_effect_types = {
            eff_type for ctx, eff_type in _CONTEXT_BONUS_EFFECT_TYPES.items() if ctx in _context_nonzero_bonus_fields
        }
        for eff in effects:
            if eff.effect_type in _context_effect_types:
                _seen_overlap_effect_types.add(eff.effect_type)
        if _seen_overlap_effect_types:
            _logger.warning(
                "效果可能与上下文重复叠加: %s（检查是否同源 buff 被传入两次）",
                ", ".join(sorted(_seen_overlap_effect_types)),
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
    imbalance_coeff_override: float | None = None

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
        elif effect.effect_type == "连击增伤" and damage_pipeline != "abnormal":
            combo_bonus += value
        elif effect.effect_type == "伤害类型伤害加成":
            damage_type_bonus_total += value
        elif effect.effect_type == "技能类型伤害加成":
            skill_type_bonus_total += value
        elif effect.effect_type == "失衡伤害加成":
            imbalance_damage_bonus_total += value
        elif effect.effect_type == "其他伤害加成":
            other_damage_bonus_total += value
        elif effect.effect_type == "无视抗性":
            resistance_extra += value
        elif effect.effect_type == "抗性":
            resistance_change += value
        elif effect.effect_type == "防御":
            defense_change += value
        elif effect.effect_type == "失衡易伤系数":
            imbalance_coeff_override = value
        elif effect.effect_type == "非主控减伤" and damage_pipeline != "abnormal":
            non_control_reduction *= 1.0 - value
        elif effect.effect_type == "特殊乘区":
            special_zone *= value

    shelter = 1.0 - max(shelter_values, default=0.0)

    flat_combo_bonus = max(0.0, combo_bonus - 1.0)
    combo_bonus = combo_zone_multiplier(
        context.skill_type,
        int(context.combo_stacks),
        flat_legacy_bonus=flat_combo_bonus,
    )

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

    if damage_pipeline == "abnormal":
        non_control_reduction = 1.0
        combo_bonus = 1.0

    # 汇总 4 种伤害加成用于展示
    damage_bonus_total = (
        damage_type_bonus_total + skill_type_bonus_total + imbalance_damage_bonus_total + other_damage_bonus_total
    )
    zone_values = {
        "基础伤害区": float(context.final_attack) * float(context.skill_multiplier) + float(context.base_damage_bonus),
        "暴击区": _resolve_crit_zone(context, crit_mode),
        "伤害加成区": damage_bonus_total,
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

    # 通过 DAG 公式函数 compute_15_zone_damage 计算最终伤害
    # 消除双计算路径：此函数逐步替换本地手动连乘
    from framework.adapters.endfield.functions import compute_15_zone_damage

    final_damage = compute_15_zone_damage(
        final_attack=float(context.final_attack),
        skill_multiplier=float(context.skill_multiplier),
        base_damage_bonus=float(context.base_damage_bonus),
        crit_rate=_clamp(float(context.crit_rate), 0.0, 1.0),
        crit_damage=float(context.crit_damage),
        crit_mode=crit_mode,
        damage_type_bonus=damage_type_bonus_total - 1.0,
        skill_type_bonus=skill_type_bonus_total,
        imbalance_damage_bonus=imbalance_damage_bonus_total,
        other_damage_bonus=other_damage_bonus_total,
        damage_reduction=1.0 - damage_reduction,
        amplification=amplification - 1.0,
        weakness=1.0 - weakness,
        shelter=1.0 - shelter,
        fragile=fragile - 1.0,
        vulnerability=vulnerability - 1.0,
        enemy_defense=float(context.enemy_defense),
        defense_change=defense_change,
        is_true_damage=bool(context.is_true_damage),
        imbalance_coeff=imbalance_coeff,
        is_unbalanced=bool(context.is_unbalanced),
        enemy_resistance=resistance,
        ignore_resistance=ignore_res,
        non_control_reduction=1.0 - non_control_reduction,
        combo_bonus=max(0.0, combo_bonus - 1.0),
        special=special_zone,
    )

    return DamageResult(
        final_damage=final_damage,
        zone_values=ordered_zone_values,
        crit_mode=crit_mode,
        warnings=warnings,
        unknown_effects=unknown_effects,
    )
