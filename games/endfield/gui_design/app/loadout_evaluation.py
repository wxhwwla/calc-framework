#!/usr/bin/env python3
"""当前配装下的伤害求值（预览/仪表盘共用缓存接缝）。"""

from __future__ import annotations

from typing import Any

from adapters.endfield.calc.core.preview_cache import sync_confirm_dependencies
from adapters.endfield.calc.loadout.optimizer import WeaponCandidate
from gui_design.presentation.damage_snapshot import (
    DamageSnapshot,
    build_damage_snapshot,
    store_snapshot_on_app,
)
from gui_design.presentation.preview_lines import (
    build_multi_skill_search_preview_lines,
    build_single_skill_search_preview_lines,
)

from .loadout_state import LoadoutState


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
        physical_abnormal_counts=loadout.physical_abnormal_counts,
        spell_abnormal_counts=loadout.spell_abnormal_counts,
        damage_component_mode=loadout.damage_component_mode,
        use_expected_crit=loadout.use_expected_crit,
        include_conditional_equipment_crit=loadout.include_conditional_equipment_crit,
        extra_crit_rate=loadout.extra_crit_rate,
        extra_crit_damage=loadout.extra_crit_damage,
        enemy_defense=loadout.enemy_defense,
    )


def build_search_preview_lines(
    loadout: LoadoutState,
    *,
    equipment_catalog: dict[str, list[dict[str, Any]]],
    preview_weapon_candidates: list[WeaponCandidate] | None = None,
) -> list[str]:
    """单/多技能快速预览文案（须传入门面 catalog，不再隐式读全库）。"""
    sync_evaluation_cache(loadout)
    s1, s2, s3 = loadout.skill_levels
    char_data = loadout.char_data
    weapon_data = loadout.weapon_data
    skill_kwargs = loadout.weapon_skill_kwargs()
    if loadout.calculation_mode == "multi_skill_search":
        return build_multi_skill_search_preview_lines(
            char_data=char_data,
            weapon_data=weapon_data,
            char_level=loadout.char_level,
            weapon_level=loadout.weapon_level,
            trust_level=loadout.trust_level,
            skill_1_level=s1,
            skill_2_level=s2,
            skill_3_level=s3,
            manual_counts=loadout.manual_counts,
            use_manual_counts=loadout.use_manual_multi_skill_counts,
            preview_equipment_catalog=equipment_catalog,
            preview_equipment_scope_label=loadout.equipment_scope_label,
            enemy_defense=loadout.enemy_defense,
            physical_abnormal_counts=loadout.physical_abnormal_counts,
            spell_abnormal_counts=loadout.spell_abnormal_counts,
            damage_component_mode=loadout.damage_component_mode,
            use_expected_crit=loadout.use_expected_crit,
            extra_crit_rate=loadout.extra_crit_rate,
            extra_crit_damage=loadout.extra_crit_damage,
            **skill_kwargs,
        )
    if loadout.calculation_mode == "single_skill_search":
        return build_single_skill_search_preview_lines(
            char_data=char_data,
            weapon_data=weapon_data,
            char_level=loadout.char_level,
            weapon_level=loadout.weapon_level,
            trust_level=loadout.trust_level,
            skill_1_level=s1,
            skill_2_level=s2,
            skill_3_level=s3,
            preview_weapon_candidates=preview_weapon_candidates,
            preview_scope_label=loadout.weapon_scope_label,
            preview_equipment_catalog=equipment_catalog,
            preview_equipment_scope_label=loadout.equipment_scope_label,
            enemy_defense=loadout.enemy_defense,
            physical_abnormal_counts=loadout.physical_abnormal_counts,
            spell_abnormal_counts=loadout.spell_abnormal_counts,
            damage_component_mode=loadout.damage_component_mode,
            use_expected_crit=loadout.use_expected_crit,
            extra_crit_rate=loadout.extra_crit_rate,
            extra_crit_damage=loadout.extra_crit_damage,
            **skill_kwargs,
        )
    return []


def build_snapshot_from_loadout(loadout: LoadoutState) -> DamageSnapshot:
    """从 LoadoutState 构建伤害仪表盘快照。"""
    sync_evaluation_cache(loadout)
    skill_kwargs = loadout.weapon_skill_kwargs()
    return build_damage_snapshot(
        char_data=loadout.char_data,
        weapon_data=loadout.weapon_data,
        char_level=loadout.char_level,
        weapon_level=loadout.weapon_level,
        trust_level=loadout.trust_level,
        skill_levels=loadout.skill_levels,
        skill_counts=loadout.manual_counts,
        use_manual_counts=loadout.use_manual_multi_skill_counts,
        enemy_defense=loadout.enemy_defense,
        enemy_resistance=loadout.enemy_resistance,
        ignore_resistance=loadout.ignore_resistance,
        imbalance_vulnerability_coeff=loadout.imbalance_vulnerability_coeff,
        is_unbalanced=loadout.is_unbalanced,
        manual_buffs=loadout.manual_buffs if loadout.manual_buffs else None,
        **skill_kwargs,
    )


def refresh_damage_snapshot(
    app: Any,
    *,
    loadout: LoadoutState | None = None,
) -> None:
    """确认后刷新伤害快照（从 LoadoutState 重建并存储）。"""
    from gui_design.app.loadout_state import read_loadout_from_app

    if loadout is None:
        loadout = read_loadout_from_app(app)
    if loadout is None:
        return
    store_snapshot_on_app(app, build_snapshot_from_loadout(loadout))
