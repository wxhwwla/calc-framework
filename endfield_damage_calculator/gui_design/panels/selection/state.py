#!/usr/bin/env python3
"""选择面板：数据更新与启用/禁用。"""

from __future__ import annotations

from typing import Any


class SelectionPanelStateMixin:
    def update_data_list(self, new_data: list[dict[str, Any]]) -> None:
        """
        动态更新数据列表并重置选择

        参数：
            new_data: 新的数据列表
        """
        self.list_c_w = new_data

        if not new_data:
            # 空数据，清空菜单
            self.type_menu.configure(values=[])
            self.star_menu.configure(values=[])
            self.name_menu.configure(values=[])
            self.selected_type.set("")
            self.selected_star.set("")
            self.selected_name.set("")
            self.selected_level.set("1")
            return

        # 获取唯一类型
        unique_types = sorted(list(set(item["类型"] for item in new_data)))

        if unique_types:
            self.type_menu.configure(values=unique_types)
            self.selected_type.set(unique_types[0])
        else:
            self.type_menu.configure(values=[])
            self.selected_type.set("")

    def disable_panel(self) -> None:
        """禁用面板所有控件"""
        self.type_menu.configure(state="disabled")
        self.star_menu.configure(state="disabled")
        self.name_menu.configure(state="disabled")
        if self.level_slider:
            self.level_slider.configure(state="disabled")
        if self._level_preset_80_btn:
            self._level_preset_80_btn.configure(state="disabled")
        if self._level_preset_90_btn:
            self._level_preset_90_btn.configure(state="disabled")
        if self._skill_preset_9_btn:
            self._skill_preset_9_btn.configure(state="disabled")
        if self._skill_preset_12_btn:
            self._skill_preset_12_btn.configure(state="disabled")

        # 禁用子组件
        if self.trust_panel:
            if self.trust_panel.trust_slider:
                self.trust_panel.trust_slider.configure(state="disabled")
        if self.special_ability_panel:
            # 禁用并隐藏特殊能力面板
            if self.special_ability_panel._ability_1_slider:
                self.special_ability_panel._ability_1_slider.configure(state="disabled")
            if self.special_ability_panel._ability_2_slider:
                self.special_ability_panel._ability_2_slider.configure(state="disabled")
            if self.special_ability_panel._ability_3_slider:
                self.special_ability_panel._ability_3_slider.configure(state="disabled")
            # 隐藏特殊能力面板
            self.special_ability_panel.hide()

    def enable_panel(self) -> None:
        """启用面板所有控件"""
        self.type_menu.configure(state="normal")
        self.star_menu.configure(state="normal")
        self.name_menu.configure(state="normal")
        if self.level_slider:
            self.level_slider.configure(state="normal")
        if self._level_preset_80_btn:
            self._level_preset_80_btn.configure(state="normal")
        if self._level_preset_90_btn:
            self._level_preset_90_btn.configure(state="normal")
        if self._skill_preset_9_btn:
            self._skill_preset_9_btn.configure(state="normal")
        if self._skill_preset_12_btn:
            self._skill_preset_12_btn.configure(state="normal")

        # 启用以子组件
        if self.trust_panel:
            if self.trust_panel.trust_slider:
                self.trust_panel.trust_slider.configure(state="normal")
        if self.special_ability_panel:
            # 启用特殊能力滑块
            if self.special_ability_panel._ability_1_slider:
                self.special_ability_panel._ability_1_slider.configure(state="normal")
            if self.special_ability_panel._ability_2_slider:
                self.special_ability_panel._ability_2_slider.configure(state="normal")
            if self.special_ability_panel._ability_3_slider:
                # 始终启用滑块，开关状态由特殊能力面板内部管理
                self.special_ability_panel._ability_3_slider.configure(state="normal")
