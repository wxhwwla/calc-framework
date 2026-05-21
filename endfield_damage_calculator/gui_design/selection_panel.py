#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
选择面板模块

此模块包含通用的类型/星级/名称/等级选择面板类，适用于角色和武器选择。

主要类：
- ChooseTypesStarsNamesLevels: 通用选择面板类
"""

import customtkinter as ctk
from typing import List, Dict, Any, Optional
from .selection_components import TrustPanel, SpecialAbilityPanel, SkillLevelPanel


class ChooseTypesStarsNamesLevels:
    """
    通用选择面板类

    提供类型、星级、名称、等级的四级联动选择功能，适用于角色和武器选择。
    支持武器的特殊能力选择和角色的信赖等级选择。

    面板布局（使用 pack 布局）：
    ┌──────────────────────────┐
    │ 类型标签 + 下拉菜单      │
    │ 星级标签 + 下拉菜单      │
    │ 角色/武器标签 + 下拉菜单 │
    │ 等级标签 + 滑块          │
    │ 信赖滑块（角色）         │
    │ 特殊能力滑块（武器）      │
    └──────────────────────────┘

    联动逻辑：
    1. 选择类型后，星级菜单自动过滤该类型下的星级（自动选择第一个）
    2. 选择星级后，名称菜单自动过滤该类型+星级下的名称（自动选择第一个）
    3. 选择名称后，等级滑块自动调整范围
    4. 选择名称后，特殊能力滑块自动调整（武器面板）
    5. 等级使用滑块选择（1-90级）
    """

    def __init__(self, frame: ctk.CTkFrame, list_c_w: List[Dict[str, Any]], my_font: ctk.CTkFont, is_weapon_panel: bool = False):
        """
        初始化配置

        参数：
            frame: 父框架容器
            list_c_w: 数据列表（角色或武器数据）
            my_font: 使用的字体配置
            is_weapon_panel: 是否为武器面板（默认为False）
        """
        self.frame: ctk.CTkFrame = frame              # 父框架
        self.list_c_w: List[Dict[str, Any]] = list_c_w  # 数据列表
        self.my_font: ctk.CTkFont = my_font            # 字体配置
        self.is_weapon_panel: bool = is_weapon_panel   # 是否为武器面板

        # 选中的变量（使用 StringVar 实现联动）
        self.selected_type: ctk.StringVar = ctk.StringVar()
        self.selected_star: ctk.StringVar = ctk.StringVar()
        self.selected_name: ctk.StringVar = ctk.StringVar()
        self.selected_level: ctk.StringVar = ctk.StringVar()

        # 子组件
        self.trust_panel: Optional[TrustPanel] = None              # 信赖面板（角色专用）
        self.skill_level_panel: Optional[SkillLevelPanel] = None   # 技能等级面板（角色专用）
        self.special_ability_panel: Optional[SpecialAbilityPanel] = None  # 特殊能力面板（武器专用）

        # UI控件
        self.type_menu: ctk.CTkOptionMenu = ctk.CTkOptionMenu(
            self.frame, values=[], variable=self.selected_type, font=self.my_font
        )
        self.star_menu: ctk.CTkOptionMenu = ctk.CTkOptionMenu(
            self.frame, values=[], variable=self.selected_star, font=self.my_font
        )
        self.name_menu: ctk.CTkOptionMenu = ctk.CTkOptionMenu(
            self.frame, values=[], variable=self.selected_name, font=self.my_font
        )
        self.level_label: ctk.CTkLabel | None = None
        self.level_slider: ctk.CTkSlider | None = None

    @classmethod
    def use(cls, frame: ctk.CTkFrame, list_c_w: List[Dict[str, Any]], my_font: ctk.CTkFont, is_weapon_panel: bool = False) -> 'ChooseTypesStarsNamesLevels':
        """
        工厂方法：创建并初始化面板实例

        参数：
            frame: 父框架容器
            list_c_w: 数据列表（角色或武器）
            my_font: 使用的字体配置
            is_weapon_panel: 是否为武器面板（默认为False）

        返回：
            ChooseTypesStarsNamesLevels 实例（已完成GUI构建和联动设置）
        """
        panel = cls(frame, list_c_w, my_font, is_weapon_panel)
        panel._build_gui()
        panel._connect_trace()
        panel._init_values()
        return panel

    def _build_gui(self) -> None:
        """
        建立GUI框架（使用 pack 布局）

        创建顺序：类型 → 星级 → 名称 → 等级（滑块）
        """
        # 类型选择区域
        ctk.CTkLabel(self.frame, text="类型", font=self.my_font).pack(anchor="w", pady=(15, 0))
        self.type_menu.pack(fill="x", padx=10, pady=(0, 5))

        # 星级选择区域
        ctk.CTkLabel(self.frame, text="星级", font=self.my_font).pack(anchor="w")
        self.star_menu.pack(fill="x", padx=10, pady=(0, 5))

        # 名称选择区域（根据面板类型动态设置标签）
        name_label_text = "武器" if self.is_weapon_panel else "角色"
        ctk.CTkLabel(self.frame, text=name_label_text, font=self.my_font).pack(anchor="w")
        self.name_menu.pack(fill="x", padx=10, pady=(0, 5))

        # 等级选择区域（使用滑块）
        ctk.CTkLabel(self.frame, text="等级", font=self.my_font).pack(anchor="w")
        level_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        level_frame.pack(fill="x", padx=10, pady=(0, 5))

        # 等级显示标签（右侧）
        self.level_label = ctk.CTkLabel(level_frame, text="1", font=self.my_font, width=30)
        self.level_label.pack(side="right")

        # 等级滑块（左侧，填充剩余空间）
        self.level_slider = ctk.CTkSlider(
            level_frame,
            from_=1,
            to=90,
            number_of_steps=89,
            command=self._on_level_slider_change
        )
        self.level_slider.pack(side="left", fill="x", expand=True)
        try:
            self.level_slider.set(1)
        except ZeroDivisionError:
            # 处理初始化时的除零问题
            pass

        # 如果是角色面板，添加信赖滑块和技能等级滑块
        if not self.is_weapon_panel:
            self.trust_panel = TrustPanel(self.frame, self.my_font)
            self.skill_level_panel = SkillLevelPanel(self.frame, self.my_font)
        
        # 如果是武器面板，添加特殊能力滑块
        if self.is_weapon_panel:
            self.special_ability_panel = SpecialAbilityPanel(self.frame, self.my_font)

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
    
    # ==================== 获取数据方法 ====================
    
    def get_selected_data(self) -> Optional[Dict[str, Any]]:
        """
        获取当前选中的角色/武器数据

        返回：
            当前选中的角色/武器数据字典，如果未选择或选中的是"暂未收录"提示则返回 None
        """
        name = self.selected_name.get()
        if not name:
            return None
        
        data = next((ch for ch in self.list_c_w if ch["名称"] == name), None)
        
        if data:
            # 检查是否是"暂未收录"提示（等级数组为空表示无效数据）
            levels = data.get("等级", [])
            if not levels:
                return None
        
        return data
    
    def get_level(self) -> int:
        """
        获取当前选中的等级

        返回：
            当前选中的等级（int），默认返回1
        """
        level_str = self.selected_level.get()
        return int(level_str) if level_str.isdigit() else 1
    
    def get_trust_level(self) -> int:
        """
        获取当前选中的信赖等级（仅角色面板有效）

        返回：
            当前选中的信赖等级（0-4），如果是武器面板则返回0
        """
        if self.trust_panel:
            trust_str = self.trust_panel.trust_level.get()
            return int(trust_str) if trust_str.isdigit() else 0
        return 0
    
    def get_special_ability_1_name(self) -> str:
        """
        获取特殊能力1的名称（仅武器面板有效）

        返回：
            特殊能力1的名称，如果不存在则返回空字符串
        """
        if self.special_ability_panel:
            return self.special_ability_panel.current_special_ability_1_name
        return ""
    
    def get_special_ability_1_level(self) -> int:
        """
        获取特殊能力1的等级（仅武器面板有效）

        返回：
            特殊能力1的等级（1-9），如果不存在则返回0
        """
        if self.special_ability_panel:
            level_str = self.special_ability_panel.special_ability_1_level.get()
            return int(level_str) if level_str.isdigit() else 0
        return 0
    
    def get_special_ability_2_name(self) -> str:
        """
        获取特殊能力2的名称（仅武器面板有效）

        返回：
            特殊能力2的名称，如果不存在则返回空字符串
        """
        if self.special_ability_panel:
            return self.special_ability_panel.current_special_ability_2_name
        return ""
    
    def get_special_ability_2_level(self) -> int:
        """
        获取特殊能力2的等级（仅武器面板有效）

        返回：
            特殊能力2的等级（1-9），如果不存在则返回0
        """
        if self.special_ability_panel:
            level_str = self.special_ability_panel.special_ability_2_level.get()
            return int(level_str) if level_str.isdigit() else 0
        return 0
    
    def get_special_ability_3_name(self) -> str:
        """
        获取第三条附加属性（xxx+）名称（仅武器面板有效）

        返回：
            属性名；无第三条时返回空字符串
        """
        if self.special_ability_panel:
            return self.special_ability_panel.current_special_ability_3_name
        return ""
    
    def get_special_ability_3_level(self) -> int:
        """
        获取第三条附加属性等级（仅武器面板有效）

        返回：
            1-9；无第三条时为 0
        """
        if self.special_ability_panel:
            level_str = self.special_ability_panel.special_ability_3_level.get()
            return int(level_str) if level_str.isdigit() else 0
        return 0

    def get_weapon_special_name(self) -> str:
        """获取武器「特殊能力」字段中的能力名称（仅武器面板有效）。"""
        if self.special_ability_panel:
            return self.special_ability_panel.current_weapon_special_name
        return ""

    def get_weapon_special_level(self) -> int:
        """获取武器「特殊能力」字段等级；0 表示开关关闭。"""
        if self.special_ability_panel:
            if not self.special_ability_panel.weapon_special_enabled.get():
                return 0
            level_str = self.special_ability_panel.weapon_special_level.get()
            return int(level_str) if level_str.isdigit() else 0
        return 0
    
    def get_skill_1_level(self) -> int:
        """
        获取战技等级（仅角色面板有效）

        返回：
            战技等级（1-12），如果不存在则返回0
        """
        if self.skill_level_panel:
            level_str = self.skill_level_panel.skill_1_level.get()
            return int(level_str) if level_str.isdigit() else 0
        return 0
    
    def get_skill_2_level(self) -> int:
        """
        获取连携技等级（仅角色面板有效）

        返回：
            连携技等级（1-12），如果不存在则返回0
        """
        if self.skill_level_panel:
            level_str = self.skill_level_panel.skill_2_level.get()
            return int(level_str) if level_str.isdigit() else 0
        return 0
    
    def get_skill_3_level(self) -> int:
        """
        获取终结技等级（仅角色面板有效）

        返回：
            终结技等级（1-12），如果不存在则返回0
        """
        if self.skill_level_panel:
            level_str = self.skill_level_panel.skill_3_level.get()
            return int(level_str) if level_str.isdigit() else 0
        return 0
    
    def update_data_list(self, new_data: List[Dict[str, Any]]) -> None:
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

