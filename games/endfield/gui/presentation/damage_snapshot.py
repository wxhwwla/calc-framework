#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""
当前配装下的伤害快照：供仪表盘与历史记录使用。

- 技能分项：各段单次伤害 × 次数 → 轮转总伤（饼图按段分块）
- 乘区构成：按 15 乘区对数权重估算占比（可视化用）
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from games.endfield.calc.damage.engine import ZONE_ORDER, DamageContext, calculate_single_hit_damage
from games.endfield.calc.damage.physical_abnormal_state import (
    break_defense_stacks_at_hit,
    build_rotation_hit_index,
    is_physical_abnormal_key,
)
from games.endfield.calc.multiplicative_zones.final_attack_zone import calculate_final_attack_with_details
from games.endfield.calc.search.evaluate.multi_skill import build_skill_scenarios_from_levels
from games.endfield.calc.skills.segments import (
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
    weights = {name: abs(math.log(max(float(zone_values.get(name, 1.0)), 1e-9))) for name in ZONE_ORDER}
    total = sum(weights.values()) or 1.0
    return {name: weights[name] / total * 100.0 for name in ZONE_ORDER if weights[name] > 0}


_SKILL_TYPE_ORDER = ("战技", "连携技", "终结技")


def _compute_weighted_with_buffs(
    segment_damage: dict[str, float],
    counts: dict[str, int],
    manual_buffs: dict[str, list[dict[str, str | float]]] | None,
    scenarios: list[Any],
    final_attack: float,
    enemy_defense: float,
    enemy_resistance: float = 0.0,
    ignore_resistance: float = 0.0,
    imbalance_vulnerability_coeff: float = 1.3,
    is_unbalanced: bool = False,
    is_true_damage: bool = False,
    combo_stacks: int = 0,
    break_defense_stacks: int = 0,
) -> tuple[float, dict[str, float], dict[str, float]]:
    """按次数加总，对每次出现查找 manual_buffs 注入。"""
    scenario_by_key = {s.scenario_key: s for s in scenarios}
    segment_totals: dict[str, float] = {}
    skill_type_totals: dict[str, float] = {name: 0.0 for name in _SKILL_TYPE_ORDER}
    weighted_total = 0.0
    mb = manual_buffs or {}
    preferred_order = [s.scenario_key for s in scenarios]
    hit_index_map = build_rotation_hit_index(counts, preferred_order=preferred_order)

    for key, seg_count in counts.items():
        if seg_count <= 0 or is_physical_abnormal_key(key):
            continue
        scenario = scenario_by_key.get(key)
        segment_total = 0.0
        for occurrence_idx in range(1, seg_count + 1):
            buff_key = f"{key}:{occurrence_idx}"
            buffs = mb.get(buff_key)
            global_hit = hit_index_map.get((key, occurrence_idx), occurrence_idx)
            stacks_at_hit = break_defense_stacks_at_hit(break_defense_stacks, global_hit)
            if buffs is not None or scenario is not None:
                result = calculate_single_hit_damage(
                    DamageContext(
                        final_attack=final_attack,
                        skill_multiplier=scenario.skill_multiplier if scenario else 1.0,
                        damage_type=scenario.damage_type or "物理" if scenario else "物理",
                        skill_type=scenario.resolved_skill_type if scenario else "战技",
                        enemy_defense=enemy_defense,
                        enemy_resistance=enemy_resistance,
                        ignore_resistance=ignore_resistance,
                        imbalance_vulnerability_coeff=imbalance_vulnerability_coeff,
                        is_unbalanced=is_unbalanced,
                        is_true_damage=is_true_damage,
                        combo_stacks=max(0, min(4, int(combo_stacks))),
                        break_defense_stacks=max(0, min(4, int(stacks_at_hit))),
                    ),
                    crit_mode="non_crit",
                    manual_buffs=buffs,
                )
                single_hit = float(result.final_damage)
            else:
                single_hit = float(segment_damage.get(key, 0.0))
            segment_total += single_hit
        segment_totals[key] = segment_total
        weighted_total += segment_total
        skill_type, _ = parse_segment_key(key)
        if skill_type in skill_type_totals:
            skill_type_totals[skill_type] += segment_total

    skill_type_totals = {k: v for k, v in skill_type_totals.items() if v > 0}
    return weighted_total, segment_totals, skill_type_totals


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
    normal_skill_1_name: str = "",
    normal_skill_1_level: int = 1,
    normal_skill_2_name: str = "",
    normal_skill_2_level: int = 1,
    normal_skill_3_name: str = "",
    normal_skill_3_level: int = 0,
    special_skill_1_name: str = "",
    special_skill_1_level: int = 1,
    special_skill_1_stack: int = 1,
    special_skill_2_name: str = "",
    special_skill_2_level: int = 1,
    special_skill_2_stack: int = 1,
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
    enemy_resistance: float = 0.0,
    ignore_resistance: float = 0.0,
    imbalance_vulnerability_coeff: float = 1.3,
    is_unbalanced: bool = False,
    is_true_damage: bool = False,
    combo_stacks: int = 0,
    break_defense_stacks: int = 0,
    manual_buffs: dict[str, list[dict[str, str | float]]] | None = None,
) -> DamageSnapshot:
    """按当前角色/武器与段级次数计算分项伤害（不含装备词条）。

    manual_buffs: 手动场外 buff，key 为 "段键:次数"（如 "战技:1:2"），值为该次使用的 buff 条目列表。
    """
    has_normal_1 = bool(normal_skill_1_name)
    has_normal_2 = bool(normal_skill_2_name)
    has_normal_3 = bool(normal_skill_3_name)
    has_special_1 = bool(special_skill_1_name)
    has_special_2 = bool(special_skill_2_name)
    normal_skill_1_name = normal_skill_1_name or sa1_name
    normal_skill_1_level = normal_skill_1_level if has_normal_1 else sa1_level
    normal_skill_2_name = normal_skill_2_name or sa2_name
    normal_skill_2_level = normal_skill_2_level if has_normal_2 else sa2_level
    normal_skill_3_name = normal_skill_3_name or sa3_name
    normal_skill_3_level = normal_skill_3_level if has_normal_3 else sa3_level
    special_skill_1_name = special_skill_1_name or ws_name
    special_skill_1_level = special_skill_1_level if has_special_1 else ws_level
    special_skill_1_stack = special_skill_1_stack if has_special_1 else ws_stack
    special_skill_2_name = special_skill_2_name or ws2_name
    special_skill_2_level = special_skill_2_level if has_special_2 else ws2_level
    special_skill_2_stack = special_skill_2_stack if has_special_2 else ws2_stack

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
        normal_skill_1_name=normal_skill_1_name,
        normal_skill_1_level=normal_skill_1_level,
        normal_skill_2_name=normal_skill_2_name,
        normal_skill_2_level=normal_skill_2_level,
        normal_skill_3_name=normal_skill_3_name,
        normal_skill_3_level=normal_skill_3_level,
        special_skill_1_name=special_skill_1_name,
        special_skill_1_level=special_skill_1_level,
        special_skill_1_stack=special_skill_1_stack,
        special_skill_2_name=special_skill_2_name,
        special_skill_2_level=special_skill_2_level,
        special_skill_2_stack=special_skill_2_stack,
    )
    final_attack = float(final["final_attack"])

    segment_damage: dict[str, float] = {}
    for scenario in scenarios_list:
        result = calculate_single_hit_damage(
            DamageContext(
                final_attack=final_attack,
                skill_multiplier=scenario.skill_multiplier,
                damage_type=scenario.damage_type or "物理",
                skill_type=scenario.resolved_skill_type,
                enemy_defense=enemy_defense,
                enemy_resistance=enemy_resistance,
                ignore_resistance=ignore_resistance,
                imbalance_vulnerability_coeff=imbalance_vulnerability_coeff,
                is_unbalanced=is_unbalanced,
                is_true_damage=is_true_damage,
                combo_stacks=max(0, min(4, int(combo_stacks))),
                break_defense_stacks=max(0, min(4, int(break_defense_stacks))),
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

    weighted, segment_totals, skill_type_totals = _compute_weighted_with_buffs(
        segment_damage, counts, manual_buffs, scenarios_list, final_attack, enemy_defense,
        enemy_resistance=enemy_resistance,
        ignore_resistance=ignore_resistance,
        imbalance_vulnerability_coeff=imbalance_vulnerability_coeff,
        is_unbalanced=is_unbalanced,
        is_true_damage=is_true_damage,
        combo_stacks=combo_stacks,
        break_defense_stacks=break_defense_stacks,
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
                damage_type=primary.damage_type or "物理",
                skill_type=primary.resolved_skill_type,
                enemy_defense=enemy_defense,
                enemy_resistance=enemy_resistance,
                ignore_resistance=ignore_resistance,
                imbalance_vulnerability_coeff=imbalance_vulnerability_coeff,
                is_unbalanced=is_unbalanced,
                is_true_damage=is_true_damage,
                break_defense_stacks=max(0, min(4, int(break_defense_stacks))),
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


def get_snapshot_from_app(app: Any) -> DamageSnapshot | None:
    return getattr(app, "_last_damage_snapshot", None)
