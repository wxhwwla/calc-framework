#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""全量搜索工作量与耗时预估（不物化全部任务）。"""

from __future__ import annotationsfrom dataclasses import dataclassfrom games.endfield.calc.loadout.optimizer import (    OptimizerConfig,    WeaponCandidate,    build_optimizer_search_plan,    count_loadout_combinations,)# 单组合耗时（含 MVP 续跑批量写库），实测后可调整
DEFAULT_SECONDS_PER_COMBO: float = 0.004


@dataclass(frozen=True)
class SearchWorkloadPreview:
    """搜索工作量摘要。"""

    total_combinations: int
    weapon_count: int
    loadout_combinations: int
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class SearchDurationEstimate:
    """耗时预估。"""

    total_combinations: int
    max_workers: int
    estimated_seconds: float
    seconds_per_combo: float


def preview_search_workload(
    *,
    weapons: list[WeaponCandidate],
    equipment_catalog: dict[str, list[dict]],
    config: OptimizerConfig,
) -> SearchWorkloadPreview:
    """预览组合总数（与 enumerate_optimizer_tasks 过滤规则一致，但不物化任务）。"""
    plan = build_optimizer_search_plan(
        weapons=weapons,
        equipment_catalog=equipment_catalog,
        config=config,
    )
    loadout_count = count_loadout_combinations(
        plan.equipment_catalog,
        allow_duplicate_accessory=config.allow_duplicate_accessory,
        selection=plan.fixed_loadout,
    )
    return SearchWorkloadPreview(
        total_combinations=plan.total_combinations,
        weapon_count=len(plan.weapons),
        loadout_combinations=loadout_count,
        warnings=plan.warnings,
    )


def estimate_search_duration(
    *,
    total_combinations: int,
    max_workers: int,
    already_processed: int = 0,
    seconds_per_combo: float = DEFAULT_SECONDS_PER_COMBO,
) -> SearchDurationEstimate:
    """按组合数与并行度估算耗时（线性模型）。"""
    remaining = max(0, int(total_combinations) - int(already_processed))
    workers = max(1, int(max_workers))
    estimated = (remaining * float(seconds_per_combo)) / workers
    return SearchDurationEstimate(
        total_combinations=int(total_combinations),
        max_workers=workers,
        estimated_seconds=estimated,
        seconds_per_combo=float(seconds_per_combo),
    )


def format_duration_human(seconds: float) -> str:
    """兼容导出：实现位于 utils.search_format。"""
    from utils.search_format import format_duration_human as _fmt

    return _fmt(seconds)


def format_workload_estimate_line(*, workload: SearchWorkloadPreview, duration: SearchDurationEstimate) -> str:
    """兼容导出：实现位于 utils.search_format。"""
    from utils.search_format import format_workload_estimate_line as _fmt

    return _fmt(workload=workload, duration=duration)
