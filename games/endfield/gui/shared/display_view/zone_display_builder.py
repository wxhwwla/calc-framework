# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""乘区展示行构建器 — 从 DisplayRequest 构建 ZoneDisplayLine 列表（无 PySide6 依赖）。

从 qt_columns.py 提取，可被 Web/CLI/测试复用。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from games.endfield.calc.zone_snapshot.types import ZoneDisplayLine

if TYPE_CHECKING:
    from games.endfield.gui.app.display_request import DisplayRequest


def build_zone_lines(request: DisplayRequest) -> list[ZoneDisplayLine]:
    """从 DisplayRequest 构建乘区展示行。

    Args:
        request: 显示请求，包含 loadout 和计算参数。

    Returns:
        乘区展示行列表。
    """
    from games.endfield.calc.core.preview_cache import sync_confirm_dependencies
    from games.endfield.calc.zone_snapshot import (
        MultiplicativeZoneSelection,
        WeaponBonusSelection,
        compute_multiplicative_zone_snapshot,
    )

    loadout = request.loadout
    skill_specials = loadout.weapon_skill_kwargs()

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

    s1, s2, s3 = loadout.skill_levels
    mode = loadout.calculation_mode

    if mode == "zone_snapshot":
        selection = MultiplicativeZoneSelection(
            character=loadout.char_data,
            weapon=loadout.weapon_data,
            char_level=loadout.char_level,
            weapon_level=loadout.weapon_level,
            trust_level=loadout.trust_level,
            bonuses=WeaponBonusSelection(
                normal_skill_1_name=skill_specials.get("normal_skill_1_name", ""),
                normal_skill_1_level=int(skill_specials.get("normal_skill_1_level", 1)),
                normal_skill_2_name=skill_specials.get("normal_skill_2_name", ""),
                normal_skill_2_level=int(skill_specials.get("normal_skill_2_level", 1)),
                normal_skill_3_name=skill_specials.get("normal_skill_3_name", ""),
                normal_skill_3_level=int(skill_specials.get("normal_skill_3_level", 0)),
                special_skill_1_name=skill_specials.get("special_skill_1_name", ""),
                special_skill_1_level=int(skill_specials.get("special_skill_1_level", 1)),
                special_skill_1_stack=int(skill_specials.get("special_skill_1_stack", 1)),
                special_skill_2_name=skill_specials.get("special_skill_2_name", ""),
                special_skill_2_level=int(skill_specials.get("special_skill_2_level", 1)),
                special_skill_2_stack=int(skill_specials.get("special_skill_2_stack", 1)),
            ),
        )
        return compute_multiplicative_zone_snapshot(selection)

    if mode == "single_hit":
        from games.endfield.gui.presentation.display_lines import build_single_hit_damage_lines

        return [
            ZoneDisplayLine(t, "#B8B8B8")
            for t in build_single_hit_damage_lines(
                char_data=loadout.char_data,
                weapon_data=loadout.weapon_data,
                char_level=loadout.char_level,
                weapon_level=loadout.weapon_level,
                trust_level=loadout.trust_level,
                skill_1_level=s1,
                skill_2_level=s2,
                skill_3_level=s3,
                enemy_defense=loadout.enemy_defense,
                **skill_specials,
            )
        ]

    if mode in ("single_skill_search", "multi_skill_search"):
        from games.endfield.gui.app.loadout_evaluation import build_search_preview_lines

        return [
            ZoneDisplayLine(t, "#B8B8B8")
            for t in build_search_preview_lines(
                loadout,
                equipment_catalog=request.equipment_catalog,
                preview_weapon_candidates=list(request.preview_weapon_candidates),
            )
        ]

    return [ZoneDisplayLine('该模式开发中，请先选择"乘区数据"。', "#888888")]
