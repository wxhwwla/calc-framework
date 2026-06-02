# SPDX-License-Identifier: AGPL-3.0
"""终末地适配器 — DAG 表达式自定义函数。

本模块的函数通过 ``meta.json`` 的 ``functions`` 字段自动注册到 DAG 沙箱，
可在任何 ``expr`` 节点的表达式中直接调用。

例如 DAG JSON 中的表达式节点::

    {
      "type": "expr",
      "expr": "clamp(攻击力, 0, 9999)",
      "inputs": { "攻击力": "some_node" }
    }
"""


def clamp(value: float, min_val: float, max_val: float) -> float:
    """将 value 约束在 [min_val, max_val] 区间内。"""
    return max(min_val, min(max_val, value))


def lerp(a: float, b: float, t: float) -> float:
    """线性插值: a + (b - a) * t。"""
    return a + (b - a) * t


def percent_of(value: float, total: float) -> float:
    """计算 value 占总量的比例（0-1），避免除零。"""
    if total == 0:
        return 0.0
    return value / total


def weighted_sum(values: list[float], weights: list[float]) -> float:
    """加权求和: Σ(values[i] * weights[i])。"""
    return sum(v * w for v, w in zip(values, weights))


# ═══════════════════════════════════════════════════════════════
#  终末地 15 乘区伤害公式（DAG 可调用版）
# ═══════════════════════════════════════════════════════════════
# 这些函数与 games/endfield/calc/damage/engine/calculate.py
# 中的 calculate_single_hit_damage() 保持计算一致。
# 迁移阶段：先并行验证 → 切换调用方 → 废弃旧引擎。


def base_damage_zone(
    final_attack: float,
    skill_multiplier: float,
    base_damage_bonus: float = 0.0,
) -> float:
    """基础伤害区: 最终攻击力 × 技能倍率 + 基础伤害提升。"""
    return final_attack * skill_multiplier + base_damage_bonus


def crit_zone(
    crit_rate: float = 0.05,
    crit_damage: float = 0.5,
    crit_mode: str = "non_crit",
) -> float:
    """暴击区。

    参数:
        crit_rate: 暴击率 (0-1)
        crit_damage: 暴击伤害倍率
        crit_mode: non_crit / expected / always_crit
    """
    if crit_mode == "always_crit":
        return 1.0 + crit_damage
    if crit_mode == "expected":
        return 1.0 + crit_rate * crit_damage
    return 1.0


def damage_bonus_zone(
    damage_type_bonus: float = 0.0,
    skill_type_bonus: float = 0.0,
    imbalance_damage_bonus: float = 0.0,
    other_damage_bonus: float = 0.0,
) -> float:
    """伤害加成区: 1.0 + Σ(各类加成)。"""
    return 1.0 + damage_type_bonus + skill_type_bonus + imbalance_damage_bonus + other_damage_bonus


def damage_reduction_zone(damage_reduction: float = 0.0) -> float:
    """伤害减免区: 连乘 (1.0 - 减免值)。"""
    return 1.0 - damage_reduction


def amplification_zone(amplification: float = 0.0) -> float:
    """增幅区: 1.0 + 增幅值。"""
    return 1.0 + amplification


def weakness_zone(weakness: float = 0.0) -> float:
    """虚弱区: 1.0 - 虚弱值。"""
    return 1.0 - weakness


def shelter_zone(shelter: float = 0.0) -> float:
    """庇护区: 1.0 - max(庇护值)。"""
    return 1.0 - shelter


def fragile_zone(fragile: float = 0.0) -> float:
    """脆弱区: 1.0 + 脆弱值。"""
    return 1.0 + fragile


def vulnerability_zone(vulnerability: float = 0.0) -> float:
    """易伤区: 1.0 + 易伤值。"""
    return 1.0 + vulnerability


def defense_zone(
    enemy_defense: float = 100.0,
    defense_change: float = 0.0,
    is_true_damage: bool = False,
) -> float:
    """防御区: 100 / (100 + 防御) 或 1.0（真伤）。"""
    if is_true_damage:
        return 1.0
    effective = max(0.0, enemy_defense + defense_change)
    return 100.0 / (effective + 100.0)


def imbalance_zone(
    imbalance_coeff: float = 1.3,
    is_unbalanced: bool = False,
) -> float:
    """失衡易伤区: 失衡时系数，非失衡时 1.0。"""
    return imbalance_coeff if is_unbalanced else 1.0


def resistance_zone(
    enemy_resistance: float = 0.0,
    ignore_resistance: float = 0.0,
) -> float:
    """抗性区: 1.0 - 抗性/100 + 无视抗性/100。"""
    return 1.0 - enemy_resistance / 100.0 + ignore_resistance / 100.0


def non_control_reduction_zone(non_control_reduction: float = 0.0) -> float:
    """非主控减伤区: 1.0 - 非主控减伤值。"""
    return 1.0 - non_control_reduction


def combo_bonus_zone(combo_bonus: float = 0.0) -> float:
    """连击增伤区: 1.0 + 连击增伤值。"""
    return 1.0 + combo_bonus


def special_zone(special: float = 1.0) -> float:
    """特殊乘区: 连乘值。"""
    return special


def manual_buff_zone(
    *,
    damage_type_bonus: float = 0.0,
    skill_type_bonus: float = 0.0,
    imbalance_damage_bonus: float = 0.0,
    other_damage_bonus: float = 0.0,
    damage_reduction: float = 0.0,
    amplification: float = 0.0,
    weakness: float = 0.0,
    shelter: float = 0.0,
    fragile: float = 0.0,
    vulnerability: float = 0.0,
    defense_change: float = 0.0,
    imbalance_coeff: float | None = None,
    is_unbalanced: bool = False,
    is_true_damage: bool = False,
    enemy_defense: float = 100.0,
    enemy_resistance: float = 0.0,
    ignore_resistance: float = 0.0,
    resistance_change: float = 0.0,
    non_control_reduction: float = 0.0,
    combo_bonus: float = 0.0,
    special: float = 1.0,
) -> dict[str, float]:
    """手动 buff/效果乘区处理：累加各种效果到对应的乘区值。

    与 games/endfield/calc/damage/engine/calculate.calculate_single_hit_damage()
    中 ``_collect_effects`` → 乘区分配的处理逻辑一致。

    返回:
        {乘区名: 乘数} 字典，可直接作为 ``compute_15_zone_damage`` 的输入
    """
    db = 1.0 + damage_type_bonus + skill_type_bonus + imbalance_damage_bonus + other_damage_bonus

    dr = 1.0 - damage_reduction
    amp = 1.0 + amplification
    wk = 1.0 - weakness
    sh = 1.0 - shelter
    fr = 1.0 + fragile
    vu = 1.0 + vulnerability

    if is_true_damage:
        dff = 1.0
    else:
        effective_def = max(0.0, enemy_defense + defense_change)
        dff = 100.0 / (effective_def + 100.0)

    imb = imbalance_coeff if (imbalance_coeff is not None and is_unbalanced) else 1.0
    res = 1.0 - (enemy_resistance + resistance_change) / 100.0 + ignore_resistance / 100.0
    ncr = 1.0 - non_control_reduction
    com = 1.0 + combo_bonus
    sp = special

    return {
        "damage_bonus": db,
        "damage_reduction": dr,
        "amplification": amp,
        "weakness": wk,
        "shelter": sh,
        "fragile": fr,
        "vulnerability": vu,
        "defense_zone": dff,
        "imbalance_zone": imb,
        "resistance_zone": res,
        "non_control_reduction": ncr,
        "combo_bonus": com,
        "special_zone": sp,
    }


def execution_damage(
    final_damage: float,
    enemy_tier: str = "普通",
) -> float:
    """处决伤害: 常规伤害 × 处决承伤系数。

    enemy_tier 可选值: 普通/进阶/精英/头目/领袖
    """
    mults = {"普通": 1.0, "进阶": 1.25, "精英": 1.5, "头目": 1.5, "领袖": 1.75}
    mult = mults.get(str(enemy_tier).strip(), 1.0)
    return final_damage * mult


def compute_15_zone_detail(
    *,
    final_attack: float,
    skill_multiplier: float = 1.0,
    base_damage_bonus: float = 0.0,
    crit_rate: float = 0.05,
    crit_damage: float = 0.5,
    crit_mode: str = "non_crit",
    damage_type_bonus: float = 0.0,
    skill_type_bonus: float = 0.0,
    imbalance_damage_bonus: float = 0.0,
    other_damage_bonus: float = 0.0,
    damage_reduction: float = 0.0,
    amplification: float = 0.0,
    weakness: float = 0.0,
    shelter: float = 0.0,
    fragile: float = 0.0,
    vulnerability: float = 0.0,
    enemy_defense: float = 100.0,
    defense_change: float = 0.0,
    is_true_damage: bool = False,
    imbalance_coeff: float = 1.3,
    is_unbalanced: bool = False,
    enemy_resistance: float = 0.0,
    ignore_resistance: float = 0.0,
    non_control_reduction: float = 0.0,
    combo_bonus: float = 0.0,
    special: float = 1.0,
) -> dict[str, float]:
    """15 乘区各乘区值明细，按 ZONE_ORDER 顺序返回。

    返回:
        {乘区名: 乘数值} 字典，键与 games/endfield/calc/damage/engine/types.ZONE_ORDER 一致
    """
    return {
        "基础伤害区": base_damage_zone(final_attack, skill_multiplier, base_damage_bonus),
        "暴击区": crit_zone(crit_rate, crit_damage, crit_mode),
        "伤害加成区": damage_bonus_zone(damage_type_bonus, skill_type_bonus, imbalance_damage_bonus, other_damage_bonus),
        "伤害减免区": damage_reduction_zone(damage_reduction),
        "增幅区": amplification_zone(amplification),
        "虚弱区": weakness_zone(weakness),
        "庇护区": shelter_zone(shelter),
        "脆弱区": fragile_zone(fragile),
        "易伤区": vulnerability_zone(vulnerability),
        "防御区": defense_zone(enemy_defense, defense_change, is_true_damage),
        "失衡易伤区": imbalance_zone(imbalance_coeff, is_unbalanced),
        "抗性区": resistance_zone(enemy_resistance, ignore_resistance),
        "非主控减伤区": non_control_reduction_zone(non_control_reduction),
        "连击增伤区": combo_bonus_zone(combo_bonus),
        "特殊乘区": special_zone(special),
    }


def compute_15_zone_damage(
    *,
    final_attack: float,
    skill_multiplier: float = 1.0,
    base_damage_bonus: float = 0.0,
    crit_rate: float = 0.05,
    crit_damage: float = 0.5,
    crit_mode: str = "non_crit",
    damage_type_bonus: float = 0.0,
    skill_type_bonus: float = 0.0,
    imbalance_damage_bonus: float = 0.0,
    other_damage_bonus: float = 0.0,
    damage_reduction: float = 0.0,
    amplification: float = 0.0,
    weakness: float = 0.0,
    shelter: float = 0.0,
    fragile: float = 0.0,
    vulnerability: float = 0.0,
    enemy_defense: float = 100.0,
    defense_change: float = 0.0,
    is_true_damage: bool = False,
    imbalance_coeff: float = 1.3,
    is_unbalanced: bool = False,
    enemy_resistance: float = 0.0,
    ignore_resistance: float = 0.0,
    non_control_reduction: float = 0.0,
    combo_bonus: float = 0.0,
    special: float = 1.0,
) -> float:
    """15 乘区连乘计算最终伤害。

    与 games/endfield/calc/damage/engine/calculate.calculate_single_hit_damage()
    的计算逻辑一致。DAG 调用方可直接使用此函数进行完整伤害计算。
    """
    base = base_damage_zone(final_attack, skill_multiplier, base_damage_bonus)
    crit = crit_zone(crit_rate, crit_damage, crit_mode)
    db = damage_bonus_zone(damage_type_bonus, skill_type_bonus, imbalance_damage_bonus, other_damage_bonus)
    dr = damage_reduction_zone(damage_reduction)
    amp = amplification_zone(amplification)
    wk = weakness_zone(weakness)
    sh = shelter_zone(shelter)
    fr = fragile_zone(fragile)
    vu = vulnerability_zone(vulnerability)
    dff = defense_zone(enemy_defense, defense_change, is_true_damage)
    imb = imbalance_zone(imbalance_coeff, is_unbalanced)
    res = resistance_zone(enemy_resistance, ignore_resistance)
    ncr = non_control_reduction_zone(non_control_reduction)
    com = combo_bonus_zone(combo_bonus)
    sp = special_zone(special)
    return base * crit * db * dr * amp * wk * sh * fr * vu * dff * imb * res * ncr * com * sp
