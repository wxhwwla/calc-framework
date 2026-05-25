#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
当前配装下的伤害快照：供仪表盘与历史记录使用。

- 技能分项：各段单次伤害 × 次数 → 轮转总伤（饼图按段分块）
- 乘区构成：按 15 乘区对数权重估算占比（可视化用）
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Optional

from calculation.damage_engine import ZONE_ORDER, DamageContext, calculate_single_hit_damage
from calculation.multi_skill_search_eval import build_skill_scenarios_from_levels
from calculation.multiplicative_zones.final_attack_zone import calculate_final_attack_with_details
from calculation.skill_segments import (
    aggregate_weighted_damage,
    normalize_manual_segment_counts,
    parse_segment_key,
    scenario_counts_for_eval,
    segment_key,
)


@dataclass(frozen=True)
class DamageSnapshot:
    """一次确认后可复用的伤害摘要。"""

    segment_damage: dict[str, float]
    segment_counts: dict[str, int]
    segment_totals: dict[str, float]
    skill_type_totals: dict[str, float]
    weighted_total_damage: float
    rotation_share_percent: dict[str, float]
    zone_share_percent: dict[str, float]
    selected_skill_label: str

    @property
    def skill_damage(self) -> dict[str, float]:
        """兼容旧接口：段键 → 单次伤害。"""
        return dict(self.segment_damage)

    @property
    def skill_counts(self) -> dict[str, int]:
        """兼容旧接口：段键 → 次数。"""
        return dict(self.segment_counts)


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
    use_manual_counts: bool = True,
    sa1_name: str = "",
    sa1_level: int = 1,
    sa2_name: str = "",
    sa2_level: int = 1,
    sa3_name: str = "",
    sa3_level: int = 0,
    ws_name: str = "",
    ws_level: int = 1,
    ws_stack: int = 1,
    ws2_name: str = "",
    ws2_level: int = 1,
    ws2_stack: int = 1,
    enemy_defense: float = 100.0,
) -> DamageSnapshot:
    """按当前角色/武器与段级次数计算分项伤害（不含装备词条）。"""
    scenarios = build_skill_scenarios_from_levels(
        char_data,
        skill_1_level=skill_levels[0],
        skill_2_level=skill_levels[1],
        skill_3_level=skill_levels[2],
    )
    if not scenarios:
        selected_label = "战技"
        scenarios_list = []
    else:
        scenarios_list = list(scenarios)
        selected_label = scenarios_list[0].resolved_skill_type

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
        ws_stack=ws_stack,
        ws2_name=ws2_name,
        ws2_level=ws2_level,
        ws2_stack=ws2_stack,
    )
    final_attack = float(final["final_attack"])

    segment_damage: dict[str, float] = {}
    for scenario in scenarios_list:
        result = calculate_single_hit_damage(
            DamageContext(
                final_attack=final_attack,
                skill_multiplier=scenario.skill_multiplier,
                skill_type=scenario.resolved_skill_type,
                enemy_defense=enemy_defense,
            ),
            crit_mode="non_crit",
        )
        segment_damage[scenario.scenario_key] = float(result.final_damage)

    if use_manual_counts:
        counts = normalize_manual_segment_counts(skill_counts, scenarios_list)
    else:
        counts = scenario_counts_for_eval(
            skill_counts,
            scenarios_list,
            selected_skill_type=selected_label,
            use_manual=False,
        )
    active_counts = {k: v for k, v in counts.items() if v > 0}
    if not active_counts:
        counts = {segment_key(selected_label, 1): 1}
        active_counts = counts

    weighted, segment_totals, skill_type_totals = aggregate_weighted_damage(
        segment_damage, counts
    )

    rotation_share: dict[str, float] = {}
    if weighted > 0:
        for key, total in segment_totals.items():
            rotation_share[key] = total / weighted * 100.0

    zone_percent: dict[str, float] = {}
    primary_key = next(iter(active_counts), None)
    primary = next(
        (s for s in scenarios_list if s.scenario_key == primary_key),
        scenarios_list[0] if scenarios_list else None,
    )
    if primary is not None:
        zone_result = calculate_single_hit_damage(
            DamageContext(
                final_attack=final_attack,
                skill_multiplier=primary.skill_multiplier,
                skill_type=primary.resolved_skill_type,
                enemy_defense=enemy_defense,
            ),
            crit_mode="non_crit",
        )
        zone_percent = _zone_share_percent(zone_result.zone_values)

    label = selected_label
    if primary_key:
        skill_type, seg = parse_segment_key(primary_key)
        label = f"{skill_type} 第{seg}段"

    return DamageSnapshot(
        segment_damage=segment_damage,
        segment_counts=active_counts,
        segment_totals=segment_totals,
        skill_type_totals=skill_type_totals,
        weighted_total_damage=weighted,
        rotation_share_percent=rotation_share,
        zone_share_percent=zone_percent,
        selected_skill_label=label,
    )


def store_snapshot_on_app(app: Any, snapshot: DamageSnapshot) -> None:
    """将快照挂到 GUI 应用实例供仪表盘读取。"""
    app._last_damage_snapshot = snapshot


def get_snapshot_from_app(app: Any) -> Optional[DamageSnapshot]:
    return getattr(app, "_last_damage_snapshot", None)
