# SPDX-License-Identifier: AGPL-3.0
"""明日方舟 DAG 表达式自定义函数。"""

from __future__ import annotations


def clamp(value: float, min_val: float, max_val: float) -> float:
    """将值限制到 [min_val, max_val] 区间。"""
    return max(min_val, min(value, max_val))


def min_val(a: float, b: float) -> float:
    """返回较小的值。"""
    return a if a < b else b


def physical_damage(
    *,
    atk: float,
    skill_multiplier: float,
    def_: float,
    def_penetration: float = 0.0,
    final_increase: float = 0.0,
) -> float:
    """物理伤害公式：ATK×倍率 - (DEF - 减防)，最小为 最终增伤后结果的 5%。

    参数:
        atk: 最终攻击力
        skill_multiplier: 技能倍率
        def_: 敌方防御力
        def_penetration: 固定减防值
        final_increase: 最终增伤乘区（加算）
    """
    effective_def = max(0.0, def_ - def_penetration)
    raw = atk * skill_multiplier - effective_def
    min_dmg = atk * skill_multiplier * 0.05
    return max(min_dmg, raw) * (1.0 + final_increase)


def magical_damage(
    *,
    atk: float,
    skill_multiplier: float,
    res: float,
    res_penetration_percent: float = 0.0,
    final_increase: float = 0.0,
) -> float:
    """法术伤害公式：ATK×倍率×(1 - min(RES - 减抗百分比×RES, 0))。

    参数:
        atk: 最终攻击力
        skill_multiplier: 技能倍率
        res: 敌方法术抗性
        res_penetration_percent: 减抗百分比（如 0.15 = 减 15%）
        final_increase: 最终增伤乘区（加算）
    """
    effective_res = max(0.0, res * (1.0 - res_penetration_percent))
    return atk * skill_multiplier * (1.0 - effective_res / 100.0) * (1.0 + final_increase)


def true_damage(
    *,
    atk: float,
    skill_multiplier: float,
    final_increase: float = 0.0,
) -> float:
    """真伤公式：ATK×倍率×(1+最终增伤)。"""
    return atk * skill_multiplier * (1.0 + final_increase)
