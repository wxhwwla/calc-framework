#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""选择面板：类型/星级/名称/等级联动。"""

from __future__ import annotations


class SelectionPanelCascadeMixin:
    def _connect_trace(self) -> None:
        """
        连接变量追踪（实现联动效果）

        设置 StringVar 的 trace_add 回调，当变量变化时触发相应的刷新方法：
        - selected_type 变化 → 刷新星级菜单
        - selected_star 变化 → 刷新名称菜单
        - selected_name 变化 → 刷新等级滑块
        """
        self.selected_type.trace_add("write", self._refresh_stars)
        self.selected_star.trace_add("write", self._refresh_names)
        self.selected_name.trace_add("write", self._refresh_levels)

    def _init_values(self) -> None:
        """
        初始化默认值

        获取所有唯一类型，设置类型菜单选项，并自动选择第一个类型（触发链式联动）
        """
        unique_types = sorted(list(set(ch["类型"] for ch in self.list_c_w)))

        if unique_types:
            self.type_menu.configure(values=unique_types)
            self.selected_type.set(unique_types[0])
        else:
            self.type_menu.configure(values=["无角色/武器数据"])
            self.selected_type.set("无角色/武器数据")

    def _refresh_stars(self, *args: str) -> None:
        """
        根据选中的类型，刷新星级菜单

        参数：
            *args: trace_add 回调参数（忽略）
        """
        sel_type = self.selected_type.get()

        if not sel_type or not self.list_c_w:
            self.star_menu.configure(values=[])
            return

        chars = [ch for ch in self.list_c_w if ch["类型"] == sel_type]
        stars = sorted(list(set(str(ch["星级"]) for ch in chars)), key=int)

        self.star_menu.configure(values=stars)

        if stars:
            self.selected_star.set(stars[0])
        else:
            self.selected_star.set("")
            self._reset_name_and_level()

    def _refresh_names(self, *args: str) -> None:
        """
        根据选中的星级，刷新名称菜单

        参数：
            *args: trace_add 回调参数（忽略）
        """
        sel_type = self.selected_type.get()
        sel_star = self.selected_star.get()

        if not sel_type or not sel_star or not self.list_c_w:
            self.name_menu.configure(values=[])
            return

        filtered = [ch for ch in self.list_c_w if ch["类型"] == sel_type and str(ch["星级"]) == sel_star]
        names = [ch["名称"] for ch in filtered]

        self.name_menu.configure(values=names)

        if names:
            self.selected_name.set(names[0])
        else:
            self.selected_name.set("")
            self._reset_name_and_level()

    def _refresh_levels(self, *args: str) -> None:
        """
        根据选中的名称，刷新等级滑块

        参数：
            *args: trace_add 回调参数（忽略）
        """
        if not self.level_slider or not self.level_label:
            return

        name = self.selected_name.get()

        if not name or not self.list_c_w:
            self._reset_level_slider()
            return

        char = next((ch for ch in self.list_c_w if ch["名称"] == name), None)

        if char:
            max_level = len(char["等级"])
            
            if max_level == 0:
                # 没有等级数据（如"暂未收录"情况），清空显示
                self.level_label.configure(text="")
                self.selected_level.set("")
                # 隐藏特殊能力面板
                if self.is_weapon_panel and self.special_ability_panel:
                    self.special_ability_panel.hide()
                return
            
            current = int(self.selected_level.get()) if self.selected_level.get().isdigit() else 1

            # 配置滑块范围，确保 number_of_steps 至少为 1
            steps = max(max_level - 1, 1)
            self.level_slider.configure(to=max_level, number_of_steps=steps)

            # 确保当前等级不超过最大等级
            if current > max_level:
                current = max_level

            # 更新滑块位置和显示（处理可能的除零错误）
            try:
                self.level_slider.set(current)
            except ZeroDivisionError:
                # 配置失败时使用默认值
                self.level_slider.configure(to=2, number_of_steps=1)
                self.level_slider.set(1)
            self.level_label.configure(text=str(current))
            self.selected_level.set(str(current))

            # 如果是武器面板，刷新特殊能力面板
            if self.is_weapon_panel and self.special_ability_panel:
                self.special_ability_panel.refresh(char)
                self.special_ability_panel.show()
            
            # 如果是角色面板，刷新技能等级面板
            if not self.is_weapon_panel and self.skill_level_panel:
                self.skill_level_panel.refresh(char)
                self.skill_level_panel.show()
        else:
            self._reset_level_slider()

    def _reset_name_and_level(self) -> None:
        """清空名称菜单并复位滑块"""
        self.name_menu.configure(values=[])
        self.selected_name.set("")
        self._reset_level_slider()

    def _reset_level_slider(self) -> None:
        """复位等级滑块到初始状态"""
        if self.level_slider and self.level_label:
            # 先获取当前状态
            current_state = str(self.level_slider.cget("state"))
            # 只有在滑块未被禁用时才设置值
            if current_state != "disabled":
                try:
                    self.level_slider.configure(to=90, number_of_steps=89)
                    self.level_slider.set(1)
                except ZeroDivisionError:
                    # 如果配置失败，尝试更安全的配置
                    self.level_slider.configure(to=2, number_of_steps=1)
                    self.level_slider.set(1)
            self.level_label.configure(text="1")
        self.selected_level.set("1")

    def _on_level_slider_change(self, value: float) -> None:
        """
        等级滑块值变化事件处理

        参数：
            value: 滑块当前值（float类型）
        """
        level = int(value)
        if self.level_label:
            self.level_label.configure(text=str(level))
        self.selected_level.set(str(level))

