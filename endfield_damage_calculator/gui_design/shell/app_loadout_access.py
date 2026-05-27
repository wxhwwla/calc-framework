#!/usr/bin/env python3
"""配装刮取、预览候选与计算模式读取。"""

from __future__ import annotations

from typing import Any

from calculation.loadout.optimizer import WeaponCandidate
from calculation.search.plan.job import build_weapon_candidates
from gui_design.app.confirm_orchestrator import schedule_confirm
from gui_design.app.loadout_pending import mark_loadout_pending
from gui_design.controls.multi_skill import (
    read_manual_multi_skill_counts,
    read_manual_physical_abnormal_counts,
    read_manual_spell_abnormal_counts,
)
from gui_design.panels.weapon_skill_selection import read_weapon_skill_selection_from_panel
from gui_design.shared.calc_mode_labels import calculation_mode_from_label


class AppLoadoutAccessMixin:
    def _manual_multi_skill_counts(self) -> dict[str, int]:
        return read_manual_multi_skill_counts(self)

    def _manual_physical_abnormal_counts(self) -> dict[str, int]:
        return read_manual_physical_abnormal_counts(self)

    def _manual_spell_abnormal_counts(self) -> dict[str, int]:
        return read_manual_spell_abnormal_counts(self)

    def _current_damage_component_mode(self) -> str:
        """获取当前伤害组件模式。

        返回值：
        - "skill_only": 仅技能伤害
        - "abnormal_only": 仅异常伤害
        - "skill_and_abnormal": 技能+异常伤害（默认）

        Returns:
            伤害组件模式标识字符串
        """
        label = str(self.damage_component_mode_var.get()).strip()
        if label == "仅技能":
            return "skill_only"
        if label == "仅异常":
            return "abnormal_only"
        return "skill_and_abnormal"

    def _extra_crit_rate(self) -> float:
        """获取额外暴击率（已转换为小数）。

        从 UI 输入框读取额外暴击率百分比，转换为小数形式。
        若输入无效则返回 0.0。

        Returns:
            额外暴击率（0.0 到 1.0 之间）
        """
        try:
            return float(self.extra_crit_rate_percent_var.get()) / 100.0
        except (TypeError, ValueError):
            return 0.0

    def _extra_crit_damage(self) -> float:
        """获取额外暴击伤害（已转换为小数）。

        从 UI 输入框读取额外暴击伤害百分比，转换为小数形式。
        若输入无效则返回 0.0。

        Returns:
            额外暴击伤害（0.0 到 1.0 之间）
        """
        try:
            return float(self.extra_crit_damage_percent_var.get()) / 100.0
        except (TypeError, ValueError):
            return 0.0

    def _mark_loadout_pending(self) -> None:
        """配装数值/选项变更：不刷新三列，仅更新待确认按钮。"""
        mark_loadout_pending(self)

    def _schedule_confirm(self, *, force: bool = False) -> None:
        """调度确认刷新。

        委托给 schedule_confirm 函数，用于延迟执行伤害计算更新，
        避免频繁修改输入时重复计算。

        Args:
            force: 是否强制刷新（忽略签名缓存）
        """
        schedule_confirm(self, force=force)

    def _current_calculation_mode_label(self) -> str:
        """获取当前计算模式标签（显示用）。

        Returns:
            计算模式显示标签（如"非暴击"、"暴击"、"期望暴击"）
        """
        return str(self.calc_mode_var.get())

    def _single_skill_preview_candidates(self) -> list[WeaponCandidate]:
        """按候选范围生成单技能预览武器集合。

        根据当前选择的武器范围（当前武器/所有武器）生成候选武器列表，
        用于单技能预览和配装优化。

        Returns:
            武器候选对象列表，若角色或武器数据无效则返回空列表
        """
        assert self.char_panel is not None, "char_panel 未初始化"
        assert self.weapon_panel is not None, "weapon_panel 未初始化"
        char_data = self.char_panel.get_selected_data()
        current_weapon = self.weapon_panel.get_selected_data()
        if not char_data or not current_weapon:
            return []

        skill_view = read_weapon_skill_selection_from_panel(self.weapon_panel).to_preset_view()
        return build_weapon_candidates(
            all_weapons=self.all_weapons,
            char_data=char_data,
            current_weapon=current_weapon,
            weapon_scope_label=self.single_skill_scope_var.get(),
            char_level=self.char_panel.get_level(),
            weapon_level=self.weapon_panel.get_level(),
            trust_level=self.char_panel.get_trust_level(),
            weapon_normal_levels=skill_view["weapon_normal_levels"],
            weapon_special_states=skill_view["weapon_special_states"],
        )

    def _single_skill_preview_equipment_catalog(self) -> dict[str, list[dict[str, Any]]]:
        """按装备范围构建单技能预览装备目录。

        根据当前选择的装备范围（全部装备/仅已选套装）构建装备目录，
        用于固定配装选择和配装优化。

        Returns:
            装备目录字典，键为装备部位（护甲/护手/配件），值为装备列表
        """
        return self.game_data.equipment_catalog(self.single_skill_equipment_scope_var.get())

    def _current_calculation_mode(self) -> str:
        """读取当前模式下拉框并转换为内部标识。

        将显示用的计算模式标签转换为内部使用的标识字符串。

        Returns:
            计算模式内部标识（如"non_crit"、"crit"、"expected"）
        """
        return calculation_mode_from_label(self.calc_mode_var.get())
