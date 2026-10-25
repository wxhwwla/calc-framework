#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""确认刷新去重：避免最小化/失焦等触发整页重绘。"""

from __future__ import annotations

from typing import Any


def normalize_skill_count_text(text: str) -> str:
    """将技能次数输入规范为非负整数字符串。"""
    try:
        value = max(0, int(float((text or "").strip())))
    except (TypeError, ValueError):
        value = 0
    return str(value)


def skill_count_commit_changed(text: str, last_committed: str | None) -> tuple[str, bool]:
    """
    判断次数是否相对上次「已提交」值发生变化。

    用于 FocusOut：最小化导致失焦时不应因未改动的值触发整页刷新。
    """
    normalized = normalize_skill_count_text(text)
    if last_committed is not None and normalized == last_committed:
        return normalized, False
    return normalized, True


def build_confirm_refresh_signature(
    *,
    calculation_mode: str,
    char_name: str,
    char_level: int,
    weapon_name: str,
    weapon_level: int,
    trust_level: int,
    skill_levels: tuple[int, int, int],
    weapon_specials: tuple[Any, ...],
    use_manual_multi_skill_counts: bool,
    multi_skill_manual_counts: dict[str, int],
    preview_scope_label: str,
    preview_equipment_scope_label: str,
    fixed_loadout_token: str,
    damage_component_mode: str = "skill_and_abnormal",
    use_expected_crit: bool = False,
    include_conditional_equipment_crit: bool = False,
    extra_crit_rate: float = 0.0,
    extra_crit_damage: float = 0.0,
    physical_abnormal_counts: dict[str, int] | None = None,
    spell_abnormal_counts: dict[str, int] | None = None,
) -> tuple:
    """生成可哈希签名；相同输入时跳过 destroy+重建三列展示。"""
    return (
        calculation_mode,
        char_name,
        char_level,
        weapon_name,
        weapon_level,
        trust_level,
        skill_levels,
        weapon_specials,
        use_manual_multi_skill_counts,
        tuple(sorted(multi_skill_manual_counts.items())),
        preview_scope_label,
        preview_equipment_scope_label,
        fixed_loadout_token,
        damage_component_mode,
        bool(use_expected_crit),
        bool(include_conditional_equipment_crit),
        float(extra_crit_rate),
        float(extra_crit_damage),
        tuple(sorted((physical_abnormal_counts or {}).items())),
        tuple(sorted((spell_abnormal_counts or {}).items())),
    )


def build_display_pending_signature(
    *,
    calculation_mode: str,
    char_name: str,
    char_level: int,
    weapon_name: str,
    weapon_level: int,
    trust_level: int,
    skill_levels: tuple[int, int, int],
    weapon_specials: tuple[Any, ...],
    use_manual_multi_skill_counts: bool,
    multi_skill_manual_counts: dict[str, int],
    damage_component_mode: str = "skill_and_abnormal",
    use_expected_crit: bool = False,
    include_conditional_equipment_crit: bool = False,
    extra_crit_rate: float = 0.0,
    extra_crit_damage: float = 0.0,
    physical_abnormal_counts: dict[str, int] | None = None,
    spell_abnormal_counts: dict[str, int] | None = None,
    enemy_defense: float = 100.0,
    enemy_resistance: float = 0.0,
    ignore_resistance: float = 0.0,
    imbalance_vulnerability_coeff: float = 1.3,
    is_unbalanced: bool = False,
    is_true_damage: bool = False,
    enemy_tier: str = "普通",
    combo_stacks: int = 0,
    attached_effect_multiplier: float = 1.0,
    corrosion_duration_seconds: float = 15.0,
    imbalance_efficiency_bonus: float = 0.0,
    break_defense_stacks: int = 0,
) -> tuple:
    """
    三列展示 + 快照/历史所用配装签名（不含搜索范围、固定配装等仅影响预估/搜索的字段）。
    """
    return (
        calculation_mode,
        char_name,
        char_level,
        weapon_name,
        weapon_level,
        trust_level,
        skill_levels,
        weapon_specials,
        use_manual_multi_skill_counts,
        tuple(sorted(multi_skill_manual_counts.items())),
        damage_component_mode,
        bool(use_expected_crit),
        bool(include_conditional_equipment_crit),
        float(extra_crit_rate),
        float(extra_crit_damage),
        tuple(sorted((physical_abnormal_counts or {}).items())),
        tuple(sorted((spell_abnormal_counts or {}).items())),
        float(enemy_defense),
        float(enemy_resistance),
        float(ignore_resistance),
        float(imbalance_vulnerability_coeff),
        bool(is_unbalanced),
        bool(is_true_damage),
        str(enemy_tier),
        max(0, min(4, int(combo_stacks))),
        float(attached_effect_multiplier),
        float(corrosion_duration_seconds),
        float(imbalance_efficiency_bonus),
        max(0, min(4, int(break_defense_stacks))),
    )
