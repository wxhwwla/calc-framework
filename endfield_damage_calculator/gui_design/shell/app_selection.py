#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""选择面板 trace、页签切换与关闭持久化。"""

from __future__ import annotations

from gui_design.app.confirm_orchestrator import handle_confirm, schedule_confirm
from gui_design.app.loadout_pending import mark_loadout_pending
from gui_design.shared.ui_preferences import (
    record_char_advanced_expanded,
    record_last_page,
    record_weapon_advanced_expanded,
    save_ui_preferences,
)

class AppSelectionMixin:
    def _bind_live_refresh_traces(self) -> None:
        """绑定输入 trace：换名即时确认刷新；数值/选项仅标记待确认。"""
        assert self.char_panel is not None, "char_panel 未初始化"
        assert self.weapon_panel is not None, "weapon_panel 未初始化"

        def _schedule_name_confirm(*_args: object) -> None:
            schedule_confirm(self)

        def _mark_pending(*_args: object) -> None:
            mark_loadout_pending(self)

        # 换角色/武器名：立刻刷新三列
        self.char_panel.selected_name.trace_add("write", _schedule_name_confirm)
        self.weapon_panel.selected_name.trace_add("write", _schedule_name_confirm)

        # 等级、信赖、技能、武器词条：仅待确认，不自动重算三列
        self.char_panel.selected_level.trace_add("write", _mark_pending)
        self.weapon_panel.selected_level.trace_add("write", _mark_pending)

        if self.char_panel.trust_panel is not None:
            self.char_panel.trust_panel.trust_level.trace_add("write", _mark_pending)
        if self.char_panel.skill_level_panel is not None:
            skill_panel = self.char_panel.skill_level_panel
            skill_panel.skill_1_level.trace_add("write", _mark_pending)
            skill_panel.skill_2_level.trace_add("write", _mark_pending)
            skill_panel.skill_3_level.trace_add("write", _mark_pending)

        if self.weapon_panel.special_ability_panel is not None:
            special_panel = self.weapon_panel.special_ability_panel
            special_panel.special_ability_1_level.trace_add("write", _mark_pending)
            special_panel.special_ability_2_level.trace_add("write", _mark_pending)
            special_panel.special_ability_3_level.trace_add("write", _mark_pending)
            special_panel.weapon_special_level.trace_add("write", _mark_pending)
            special_panel.weapon_special_2_level.trace_add("write", _mark_pending)

    def _startup_refresh(self) -> None:
        """首帧绘制后再做确认刷新与搜索预估（勿在 __init__ 中同步调用）。"""
        handle_confirm(self, force=True)
        self._refresh_search_estimate()

    def _apply_selection_panel_expand_preferences(self) -> None:
        """从 ui_preferences 恢复角色/武器技能折叠展开态。"""
        if self.char_panel is not None:
            expanded = bool(self._ui_preferences.get("char_advanced_expanded", True))
            self.char_panel._show_advanced_params_var.set(expanded)
            self.char_panel._refresh_advanced_params_visibility()
        if self.weapon_panel is not None:
            expanded = bool(self._ui_preferences.get("weapon_advanced_expanded", True))
            self.weapon_panel._show_advanced_params_var.set(expanded)
            self.weapon_panel._refresh_advanced_params_visibility()

    def _show_main_page(self) -> None:
        """切回计算页（保留当前输入状态）。"""
        self._set_current_page("计算页")

    def _show_advanced_page(self) -> None:
        """切到高级页（保留当前输入状态）。"""
        self._set_current_page("高级页")

    def _set_current_page(self, page: str) -> None:
        """设置当前页签，并同步更新内存中的 last_page。"""
        if self.page_tabs is None:
            return
        if page not in ("计算页", "高级页"):
            page = "计算页"
        self.page_tabs.set(page)
        self._ui_preferences = record_last_page(self._ui_preferences, page=page)

    def _on_close(self) -> None:
        """关闭窗口前持久化 UI 偏好。"""
        try:
            if self.page_tabs is not None:
                self._ui_preferences = record_last_page(
                    self._ui_preferences,
                    page=str(self.page_tabs.get()),
                )
            if self.char_panel is not None:
                self._ui_preferences = record_char_advanced_expanded(
                    self._ui_preferences,
                    expanded=bool(self.char_panel._show_advanced_params_var.get()),
                )
            if self.weapon_panel is not None:
                self._ui_preferences = record_weapon_advanced_expanded(
                    self._ui_preferences,
                    expanded=bool(self.weapon_panel._show_advanced_params_var.get()),
                )
            save_ui_preferences(self._ui_preferences)
        finally:
            self.app.destroy()

