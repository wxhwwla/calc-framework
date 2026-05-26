#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""预设构建/应用辅助。"""

from __future__ import annotations

from pathlib import Path
from tkinter import filedialog, messagebox
from typing import TYPE_CHECKING, Any, Callable, Optional

from utils.platform_win32_patch import apply_platform_win32_patch

apply_platform_win32_patch()
import customtkinter as ctk

from gui_design.shared.calc_history import CalculationHistory, HistoryEntry
from gui_design.shared.calc_mode_labels import CALC_MODE_OPTIONS
from gui_design.presentation.damage_snapshot import get_snapshot_from_app, store_snapshot_on_app
from gui_design.shared.damage_visualization import (
    build_damage_pie_figure,
    build_improvement_bar_figure,
    damage_breakdown_from_skill_map,
    is_matplotlib_available,
)
from utils.optional_deps import matplotlib_install_hint
from data.enemy_params import list_plugin_enemy_choices, resolve_enemy_defense
from gui_design.app.loadout_preset import (
    LoadoutPreset,
    export_preset_json,
    import_preset_json,
    import_presets_from_json_text,
)
from gui_design.shared.preset_batch_compare import compare_presets_parallel
from data.game_data_facade import GameDataFacade
from data.loader import get_characters, get_equipments, get_weapons
from gui_design.search_ui.search_settings import resolve_parallel_workers
from gui_design.layout.gui_layout import (
    MORE_SETTINGS_VIEWPORT_HEIGHT,
    SECONDARY_ACTION_BUTTON_HEIGHT,
)
from gui_design.shared.ui_preferences import (
    STARTUP_MODE_ALWAYS_MAIN,
    STARTUP_MODE_REMEMBER_LAST,
    save_ui_preferences,
)
from utils.gui_fonts import default_ui_font
from utils.operation_log import LogLevel, get_session_operation_log

if TYPE_CHECKING:
    from gui_design.shell.app import DamageCalculatorApp
    from gui_design.app.loadout_state import LoadoutState


def _label_for_mode(mode_id: str) -> str:
    for label, mid in CALC_MODE_OPTIONS:
        if mid == mode_id:
            return label
    return mode_id


def _lists_for_preset_compare(app: "DamageCalculatorApp") -> tuple[list, list, list]:
    """多方案对比用的角色/武器/装备列表（优先 app.game_data）。"""
    game_data = getattr(app, "game_data", None)
    if isinstance(game_data, GameDataFacade):
        return (
            game_data.characters,
            game_data.weapons,
            game_data.equipment_rows,
        )
    return get_characters(), get_weapons(), get_equipments()


def build_preset_from_app(app: "DamageCalculatorApp") -> LoadoutPreset:
    """从当前 GUI 状态组装可导出预设。"""
    from gui_design.app.loadout_state import read_loadout_from_app

    state = read_loadout_from_app(app)
    if state is None:
        raise ValueError("请先选择有效角色和武器")
    preset = state.to_loadout_preset()
    char_var = getattr(getattr(app, "char_panel", None), "_show_advanced_params_var", None)
    weapon_var = getattr(getattr(app, "weapon_panel", None), "_show_advanced_params_var", None)
    more_var = getattr(app, "_show_more_settings_var", None)
    ui_state = {
        "char_advanced_expanded": bool(char_var.get()) if char_var is not None else False,
        "weapon_advanced_expanded": bool(weapon_var.get()) if weapon_var is not None else False,
        "more_settings_expanded": bool(more_var.get()) if more_var is not None else False,
        "current_page": str(app.page_tabs.get()) if getattr(app, "page_tabs", None) is not None else "计算页",
    }
    return LoadoutPreset(
        char_name=preset.char_name,
        weapon_name=preset.weapon_name,
        char_level=preset.char_level,
        weapon_level=preset.weapon_level,
        trust_level=preset.trust_level,
        skill_levels=preset.skill_levels,
        calculation_mode=preset.calculation_mode,
        weapon_scope=preset.weapon_scope,
        equipment_scope=preset.equipment_scope,
        fixed_equipment_names=preset.fixed_equipment_names,
        multi_skill_counts=preset.multi_skill_counts,
        use_manual_multi_skill_counts=preset.use_manual_multi_skill_counts,
        physical_abnormal_counts=preset.physical_abnormal_counts,
        spell_abnormal_counts=preset.spell_abnormal_counts,
        damage_component_mode=preset.damage_component_mode,
        use_expected_crit=preset.use_expected_crit,
        include_conditional_equipment_crit=preset.include_conditional_equipment_crit,
        extra_crit_rate=preset.extra_crit_rate,
        extra_crit_damage=preset.extra_crit_damage,
        ui_state=ui_state,
        note=preset.note,
    )


def _refresh_more_settings_visibility(app: "DamageCalculatorApp") -> None:
    """按 app._show_more_settings_var 刷新「更多设置」折叠区显隐。"""
    toggle_btn = getattr(app, "_more_settings_toggle_btn", None)
    body = getattr(app, "_more_settings_body", None)
    var = getattr(app, "_show_more_settings_var", None)
    expanded = bool(var.get()) if var is not None else False
    if toggle_btn is not None:
        toggle_btn.configure(text="更多设置（收起）" if expanded else "更多设置（展开）")
    if body is not None:
        if expanded:
            body.grid()
        else:
            body.grid_remove()


def _select_panel_by_name(panel, name: str) -> bool:
    if not name or not panel.list_c_w:
        return False
    match = next((row for row in panel.list_c_w if row.get("名称") == name), None)
    if not match:
        return False
    panel.selected_type.set(str(match.get("类型", "")))
    panel.selected_star.set(str(match.get("星级", "")))
    panel.selected_name.set(name)
    return True


def apply_preset_to_app(app: "DamageCalculatorApp", preset: LoadoutPreset) -> None:
    """将预设写回 GUI（名称须存在于当前数据列表）。"""
    if not _select_panel_by_name(app.char_panel, preset.char_name):
        raise ValueError(f"未找到角色: {preset.char_name}")
    app._on_char_name_change()
    if not _select_panel_by_name(app.weapon_panel, preset.weapon_name):
        raise ValueError(f"未找到武器: {preset.weapon_name}")
    weapon_data = app.weapon_panel.get_selected_data()
    if weapon_data:
        from gui_design.panels.weapon_skill_selection import (
            WeaponSkillSelection,
            apply_weapon_skill_selection_to_panel,
        )

        skill_selection = WeaponSkillSelection.from_preset_view(
            weapon_data,
            weapon_normal_levels=preset.weapon_normal_levels,
            weapon_special_states=preset.weapon_special_states,
        )
        apply_weapon_skill_selection_to_panel(app.weapon_panel, skill_selection)
    app.char_panel.selected_level.set(str(preset.char_level))
    app.weapon_panel.selected_level.set(str(preset.weapon_level))
    if app.char_panel.trust_panel:
        app.char_panel.trust_panel.trust_level.set(str(preset.trust_level))
    if app.char_panel.skill_level_panel:
        s = app.char_panel.skill_level_panel
        s.skill_1_level.set(str(preset.skill_levels[0]))
        s.skill_2_level.set(str(preset.skill_levels[1]))
        s.skill_3_level.set(str(preset.skill_levels[2]))
    app.calc_mode_var.set(_label_for_mode(preset.calculation_mode))
    app.single_skill_scope_var.set(preset.weapon_scope)
    app.single_skill_equipment_scope_var.set(preset.equipment_scope)
    app.use_manual_skill_counts_var.set(preset.use_manual_multi_skill_counts)
    from ..multi_skill import (
        apply_physical_abnormal_counts_to_app,
        apply_spell_abnormal_counts_to_app,
        apply_segment_counts_to_app,
    )

    apply_segment_counts_to_app(app, preset.multi_skill_counts)
    apply_physical_abnormal_counts_to_app(app, preset.physical_abnormal_counts)
    apply_spell_abnormal_counts_to_app(app, getattr(preset, "spell_abnormal_counts", {}))
    if hasattr(app, "damage_component_mode_var"):
        if preset.damage_component_mode == "skill_only":
            app.damage_component_mode_var.set("仅技能")
        elif preset.damage_component_mode == "abnormal_only":
            app.damage_component_mode_var.set("仅异常")
        else:
            app.damage_component_mode_var.set("技能+异常")
    if hasattr(app, "use_expected_crit_var"):
        app.use_expected_crit_var.set(bool(preset.use_expected_crit))
    if hasattr(app, "include_conditional_equipment_crit_var"):
        app.include_conditional_equipment_crit_var.set(
            bool(preset.include_conditional_equipment_crit)
        )
    if hasattr(app, "extra_crit_rate_percent_var"):
        app.extra_crit_rate_percent_var.set(str(float(preset.extra_crit_rate) * 100.0))
    if hasattr(app, "extra_crit_damage_percent_var"):
        app.extra_crit_damage_percent_var.set(str(float(preset.extra_crit_damage) * 100.0))
    manual_buffs = getattr(preset, "manual_buffs", None)
    if manual_buffs:
        app._manual_buff_store = {k: [dict(e) for e in v] for k, v in manual_buffs.items()}
    ui_state = preset.ui_state or {}
    char_panel = getattr(app, "char_panel", None)
    if char_panel is not None and hasattr(char_panel, "_show_advanced_params_var"):
        char_panel._show_advanced_params_var.set(bool(ui_state.get("char_advanced_expanded", True)))
        if hasattr(char_panel, "_refresh_advanced_params_visibility"):
            char_panel._refresh_advanced_params_visibility()
    weapon_panel = getattr(app, "weapon_panel", None)
    if weapon_panel is not None and hasattr(weapon_panel, "_show_advanced_params_var"):
        weapon_panel._show_advanced_params_var.set(bool(ui_state.get("weapon_advanced_expanded", True)))
        if hasattr(weapon_panel, "_refresh_advanced_params_visibility"):
            weapon_panel._refresh_advanced_params_visibility()
    if hasattr(app, "_show_more_settings_var"):
        app._show_more_settings_var.set(bool(ui_state.get("more_settings_expanded", False)))
        _refresh_more_settings_visibility(app)
    if getattr(app, "page_tabs", None) is not None:
        target_page = str(ui_state.get("current_page", "计算页"))
        if target_page in ("计算页", "高级页"):
            if hasattr(app, "_set_current_page"):
                app._set_current_page(target_page)
            else:
                app.page_tabs.set(target_page)
    app._refresh_fixed_loadout_menus()
    app._schedule_confirm(force=True)


