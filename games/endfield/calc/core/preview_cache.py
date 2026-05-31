#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""预览/确认路径共用的结果缓存桥接。"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

from games.endfield.calc.core.result_cache import get_global_result_cache

T = TypeVar("T")


def sync_preview_dependencies(**dependencies: Any) -> None:
    """将当前 GUI 输入同步到全局缓存依赖表；任一变化会使缓存失效。"""
    cache = get_global_result_cache()
    for name, value in dependencies.items():
        cache.set_dependency(name, value)


def cached_preview(cache_key: str, compute: Callable[[], T]) -> tuple[T, bool]:
    """执行带缓存的计算，返回 (结果, 是否命中)。"""
    return get_global_result_cache().get_or_compute(cache_key, compute)


def sync_confirm_dependencies(
    *,
    char_data: dict | None,
    weapon_data: dict | None,
    char_level: int,
    weapon_level: int,
    trust_level: int,
    skill_levels: tuple[int, int, int],
    calculation_mode: str,
    weapon_scope: str = "",
    equipment_scope: str = "",
    multi_skill_counts: dict[str, int] | None = None,
    use_manual_multi_skill_counts: bool = False,
    physical_abnormal_counts: dict[str, int] | None = None,
    spell_abnormal_counts: dict[str, int] | None = None,
    damage_component_mode: str = "skill_and_abnormal",
    use_expected_crit: bool = False,
    include_conditional_equipment_crit: bool = False,
    extra_crit_rate: float = 0.0,
    extra_crit_damage: float = 0.0,
    enemy_defense: float = 100.0,
) -> None:
    """确认/预览前同步依赖，供各模式缓存共享。"""
    sync_preview_dependencies(
        char_name=(char_data or {}).get("名称", ""),
        weapon_name=(weapon_data or {}).get("名称", ""),
        char_level=char_level,
        weapon_level=weapon_level,
        trust_level=trust_level,
        skill_1=skill_levels[0],
        skill_2=skill_levels[1],
        skill_3=skill_levels[2],
        calculation_mode=calculation_mode,
        weapon_scope=weapon_scope,
        equipment_scope=equipment_scope,
        multi_skill_counts=tuple(sorted((multi_skill_counts or {}).items())),
        use_manual_multi_skill_counts=use_manual_multi_skill_counts,
        physical_abnormal_counts=tuple(sorted((physical_abnormal_counts or {}).items())),
        spell_abnormal_counts=tuple(sorted((spell_abnormal_counts or {}).items())),
        damage_component_mode=damage_component_mode,
        use_expected_crit=use_expected_crit,
        include_conditional_equipment_crit=bool(include_conditional_equipment_crit),
        extra_crit_rate=float(extra_crit_rate),
        extra_crit_damage=float(extra_crit_damage),
        enemy_defense=enemy_defense,
    )
