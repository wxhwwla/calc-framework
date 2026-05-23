#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
当前配装下的伤害快照：供仪表盘与历史记录使用。

- 技能分项：各技能单段伤害 × 次数 → 轮转总伤
- 乘区构成：按 15 乘区对数权重估算占比（可视化用）
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Optional

from calculation.damage_engine import ZONE_ORDER, DamageContext, calculate_single_hit_damage
from calculation.multi_skill_search_eval import build_skill_scenarios_from_levels
from calculation.multiplicative_zones.final_attack_zone import calculate_final_attack_with_details


@dataclass(frozen=True)
class DamageSnapshot:
    """一次确认后可复用的伤害摘要。"""

    skill_damage: dict[str, float]
    skill_counts: dict[str, int]
    weighted_total_damage: float
    rotation_share_percent: dict[str, float]
    zone_share_percent: dict[str, float]
    selected_skill_label: str


def _zone_share_percent(zone_values: dict[str, float]) -> dict[str, float]:
    """将乘区链转为饼图占比（对数权重，仅用于可视化）。"""
    weights = {
        name: abs(math.log(max(float(zone_values.get(name, 1.0)), 1e-9)))
        for name in ZONE_ORDER
    }
    total = sum(weights.values()) or 1.0
    return {name: weights[name] / total * 100.0 for name in ZONE_ORDER if weights[name] > 0}


def build_damage_snapshot(
    *,
    char_data: dict[str, Any],
    weapon_data: dict[str, Any],
    char_level: int,
    weapon_level: int,
    trust_level: int = 0,
    skill_levels: tuple[int, int, int],
    skill_counts: dict[str, int],
    sa1_name: str = "",
    sa1_level: int = 1,
    sa2_name: str = "",
    sa2_level: int = 1,
    sa3_name: str = "",
    sa3_level: int = 0,
    ws_name: str = "",
    ws_level: int = 0,
    ws2_name: str = "",
    ws2_level: int = 0,
    enemy_defense: float = 100.0,
) -> DamageSnapshot:
    """按当前角色/武器与技能次数计算分项伤害（不含装备词条）。"""
    scenarios = build_skill_scenarios_from_levels(
        char_data,
        skill_1_level=skill_levels[0],
        skill_2_level=skill_levels[1],
        skill_3_level=skill_levels[2],
    )
    if not scenarios:
        scenarios_list = []
        selected_label = "战技"
    else:
        scenarios_list = list(scenarios)
        selected_label = scenarios_list[0].skill_name

    final = calculate_final_attack_with_details(
        character=char_data,
        weapon=weapon_data,
        char_level=char_level,
        weapon_level=weapon_level,
        trust_level=trust_level,
        sa1_name=sa1_name,
        sa1_level=sa1_level,
        sa2_name=sa2_name,
        sa2_level=sa2_level,
        sa3_name=sa3_name,
        sa3_level=sa3_level,
        ws_name=ws_name,
        ws_level=ws_level,
        ws2_name=ws2_name,
        ws2_level=ws2_level,
    )
    final_attack = float(final["final_attack"])

    skill_damage: dict[str, float] = {}
    for scenario in scenarios_list:
        result = calculate_single_hit_damage(
            DamageContext(
                final_attack=final_attack,
                skill_multiplier=scenario.skill_multiplier,
                skill_type=scenario.skill_type,
                enemy_defense=enemy_defense,
            ),
            crit_mode="non_crit",
        )
        skill_damage[scenario.skill_name] = float(result.final_damage)

    counts = {
        "战技": max(0, int(skill_counts.get("战技", 0))),
        "连携技": max(0, int(skill_counts.get("连携技", 0))),
        "终结技": max(0, int(skill_counts.get("终结技", 0))),
    }
    if not any(counts.values()):
        counts["战技"] = 1

    weighted = sum(
        skill_damage.get(name, 0.0) * counts.get(name, 0)
        for name in counts
        if counts.get(name, 0) > 0
    )

    rotation_share: dict[str, float] = {}
    if weighted > 0:
        for name, dmg in skill_damage.items():
            c = counts.get(name, 0)
            if c > 0:
                rotation_share[name] = dmg * c / weighted * 100.0

    # 乘区占比取「当前选中技能」对应的一次计算
    zone_percent: dict[str, float] = {}
    primary = scenarios_list[0] if scenarios_list else None
    if primary is not None:
        zone_result = calculate_single_hit_damage(
            DamageContext(
                final_attack=final_attack,
                skill_multiplier=primary.skill_multiplier,
                skill_type=primary.skill_type,
                enemy_defense=enemy_defense,
            ),
            crit_mode="non_crit",
        )
        zone_percent = _zone_share_percent(zone_result.zone_values)

    return DamageSnapshot(
        skill_damage=skill_damage,
        skill_counts=counts,
        weighted_total_damage=weighted,
        rotation_share_percent=rotation_share,
        zone_share_percent=zone_percent,
        selected_skill_label=selected_label,
    )


def store_snapshot_on_app(app: Any, snapshot: DamageSnapshot) -> None:
    """将快照挂到 GUI 应用实例供仪表盘读取。"""
    app._last_damage_snapshot = snapshot


def get_snapshot_from_app(app: Any) -> Optional[DamageSnapshot]:
    return getattr(app, "_last_damage_snapshot", None)
