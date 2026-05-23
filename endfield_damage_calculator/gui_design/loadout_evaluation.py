#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""当前配装下的伤害求值（预览/仪表盘共用缓存接缝）。"""

from __future__ import annotations

from calculation.preview_cache import sync_confirm_dependencies
from gui_design.damage_snapshot import DamageSnapshot, build_damage_snapshot
from gui_design.loadout_state import LoadoutState


def sync_evaluation_cache(loadout: LoadoutState) -> None:
    """与确认刷新一致的 preview_cache 依赖键。"""
    sync_confirm_dependencies(
        char_data=loadout.char_data,
        weapon_data=loadout.weapon_data,
        char_level=loadout.char_level,
        weapon_level=loadout.weapon_level,
        trust_level=loadout.trust_level,
        skill_levels=loadout.skill_levels,
        calculation_mode=loadout.calculation_mode,
        weapon_scope=loadout.weapon_scope_label,
        equipment_scope=loadout.equipment_scope_label,
        multi_skill_counts=loadout.manual_counts,
        use_manual_multi_skill_counts=loadout.use_manual_multi_skill_counts,
        enemy_defense=loadout.enemy_defense,
    )


def build_snapshot_from_loadout(loadout: LoadoutState) -> DamageSnapshot:
    """从 LoadoutState 构建伤害仪表盘快照。"""
    sync_evaluation_cache(loadout)
    specials = loadout.weapon_special_kwargs()
    return build_damage_snapshot(
        char_data=loadout.char_data,
        weapon_data=loadout.weapon_data,
        char_level=loadout.char_level,
        weapon_level=loadout.weapon_level,
        trust_level=loadout.trust_level,
        skill_levels=loadout.skill_levels,
        skill_counts=loadout.effective_skill_counts(),
        enemy_defense=loadout.enemy_defense,
        **specials,
    )
