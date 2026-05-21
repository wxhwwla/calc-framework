#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
选择面板组件模块

此模块包含选择面板中可复用的子组件类：
- SkillLevelPanel: 技能等级选择面板（角色专用）
- SpecialAbilityPanel: 特殊能力选择面板（武器专用）
- TrustPanel: 信赖等级选择面板（角色专用）

这些组件被设计为独立的、可组合的 UI 模块，便于维护和测试。
"""

import customtkinter as ctk
from typing import List, Dict, Any, Optional


class TrustPanel:
    """
    信赖等级选择面板
    
    提供角色信赖等级的滑块选择功能（0-4级）。
    
    属性：
        trust_level: 当前选中的信赖等级（StringVar）
    """
    
    def __init__(self, parent_frame: ctk.CTkFrame, my_font: ctk.CTkFont):
        """
        初始化信赖面板
        
        参数：
            parent_frame: 父框架容器
            my_font: 使用的字体配置
        """
        self.parent_frame = parent_frame
        self.my_font = my_font
        
        # 信赖等级变量
        self.trust_level: ctk.StringVar = ctk.StringVar(value="0")
        
        # UI控件
        self.trust_label: ctk.CTkLabel | None = None
        self.trust_slider: ctk.CTkSlider | None = None
        self.trust_name_label: ctk.CTkLabel | None = None
        
        # 构建GUI
        self._build_gui()
    
    def _build_gui(self) -> None:
        """构建信赖滑块GUI"""
        # 信赖标签（上方）
        self.trust_name_label = ctk.CTkLabel(self.parent_frame, text="信赖", font=self.my_font)
        self.trust_name_label.pack(anchor="w")
        
        # 信赖滑块框架（下方）
        trust_frame = ctk.CTkFrame(self.parent_frame, fg_color="transparent")
        trust_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        # 等级显示标签（右侧，固定宽度30）
        self.trust_label = ctk.CTkLabel(trust_frame, text="0", font=self.my_font, width=30)
        self.trust_label.pack(side="right")
        
        # 滑块（左侧，填充剩余空间）
        self.trust_slider = ctk.CTkSlider(
            trust_frame,
            from_=0,
            to=4,
            number_of_steps=4,
            command=self._on_slider_change
        )
        self.trust_slider.pack(side="left", fill="x", expand=True)
        self.trust_slider.set(0)
    
    def _on_slider_change(self, value: float) -> None:
        """
        滑块值变化事件处理
        
        参数：
            value: 滑块当前值（float类型）
        """
        level = int(value)
        if self.trust_label:
            self.trust_label.configure(text=str(level))
        self.trust_level.set(str(level))


class SpecialAbilityPanel:
    """
    武器附加属性与特殊能力选择面板。

    布局（自上而下）：
    1–2. 前两条 xxx+（常态滑块 1–9）
    3. 第三条 xxx+ 或占位「无第三技能」
    4. 特殊能力字段（开关 + 滑块，默认关闭）
    """

    _BONUS_EXCLUDED = frozenset({'名称', '类型', '星级', '等级', '潜能', '基础攻击力', '特殊能力'})
    _PLACEHOLDER_NO_THIRD = "无第三技能"

    def __init__(self, parent_frame: ctk.CTkFrame, my_font: ctk.CTkFont):
        self.parent_frame = parent_frame
        self.my_font = my_font

        self.special_ability_1_level: ctk.StringVar = ctk.StringVar(value="1")
        self.special_ability_2_level: ctk.StringVar = ctk.StringVar(value="1")
        self.special_ability_3_level: ctk.StringVar = ctk.StringVar(value="0")

        self.current_special_ability_1_name: str = ""
        self.current_special_ability_2_name: str = ""
        self.current_special_ability_3_name: str = ""

        self.weapon_special_level: ctk.StringVar = ctk.StringVar(value="0")
        self.current_weapon_special_name: str = ""
        self.weapon_special_enabled: ctk.BooleanVar = ctk.BooleanVar(value=False)
        self._weapon_special_available: bool = False

        self._ability_1_name_label: ctk.CTkLabel | None = None
        self._ability_1_frame: ctk.CTkFrame | None = None
        self._ability_1_label: ctk.CTkLabel | None = None
        self._ability_1_slider: ctk.CTkSlider | None = None

        self._ability_2_name_label: ctk.CTkLabel | None = None
        self._ability_2_frame: ctk.CTkFrame | None = None
        self._ability_2_label: ctk.CTkLabel | None = None
        self._ability_2_slider: ctk.CTkSlider | None = None

        self._ability_3_name_label: ctk.CTkLabel | None = None
        self._ability_3_frame: ctk.CTkFrame | None = None
        self._ability_3_label: ctk.CTkLabel | None = None
        self._ability_3_slider: ctk.CTkSlider | None = None

        self._weapon_special_header: ctk.CTkFrame | None = None
        self._weapon_special_name_label: ctk.CTkLabel | None = None
        self._weapon_special_switch: ctk.CTkSwitch | None = None
        self._weapon_special_frame: ctk.CTkFrame | None = None
        self._weapon_special_value_label: ctk.CTkLabel | None = None
        self._weapon_special_slider: ctk.CTkSlider | None = None

        self._build_gui()

    def _build_gui(self) -> None:
        """构建附加属性与特殊能力滑块"""
        self._ability_1_name_label = ctk.CTkLabel(
            self.parent_frame, text="附加属性1", font=self.my_font
        )
        self._ability_1_frame = ctk.CTkFrame(self.parent_frame, fg_color="transparent")
        self._ability_1_label = ctk.CTkLabel(
            self._ability_1_frame, text="1", font=self.my_font, width=30
        )
        self._ability_1_label.pack(side="right")
        self._ability_1_slider = ctk.CTkSlider(
            self._ability_1_frame,
            from_=1,
            to=9,
            number_of_steps=8,
            command=self._on_ability_1_change,
        )
        self._ability_1_slider.pack(side="left", fill="x", expand=True)
        self._ability_1_slider.set(1)

        self._ability_2_name_label = ctk.CTkLabel(
            self.parent_frame, text="附加属性2", font=self.my_font
        )
        self._ability_2_frame = ctk.CTkFrame(self.parent_frame, fg_color="transparent")
        self._ability_2_label = ctk.CTkLabel(
            self._ability_2_frame, text="1", font=self.my_font, width=30
        )
        self._ability_2_label.pack(side="right")
        self._ability_2_slider = ctk.CTkSlider(
            self._ability_2_frame,
            from_=1,
            to=9,
            number_of_steps=8,
            command=self._on_ability_2_change,
        )
        self._ability_2_slider.pack(side="left", fill="x", expand=True)
        self._ability_2_slider.set(1)

        self._ability_3_name_label = ctk.CTkLabel(
            self.parent_frame, text=self._PLACEHOLDER_NO_THIRD, font=self.my_font
        )
        self._ability_3_frame = ctk.CTkFrame(self.parent_frame, fg_color="transparent")
        self._ability_3_label = ctk.CTkLabel(
            self._ability_3_frame, text="—", font=self.my_font, width=30
        )
        self._ability_3_label.pack(side="right")
        self._ability_3_slider = ctk.CTkSlider(
            self._ability_3_frame,
            from_=1,
            to=9,
            number_of_steps=8,
            command=self._on_ability_3_change,
            state="disabled",
        )
        self._ability_3_slider.pack(side="left", fill="x", expand=True)
        self._ability_3_slider.set(1)

        self._weapon_special_header = ctk.CTkFrame(self.parent_frame, fg_color="transparent")
        self._weapon_special_name_label = ctk.CTkLabel(
            self._weapon_special_header, text="特殊能力", font=self.my_font
        )
        self._weapon_special_name_label.pack(side="left")
        self._weapon_special_switch = ctk.CTkSwitch(
            self._weapon_special_header,
            text="",
            variable=self.weapon_special_enabled,
            command=self._on_weapon_special_switch_change,
            width=40,
        )
        self._weapon_special_switch.pack(side="right")

        self._weapon_special_frame = ctk.CTkFrame(self.parent_frame, fg_color="transparent")
        self._weapon_special_value_label = ctk.CTkLabel(
            self._weapon_special_frame, text="0", font=self.my_font, width=30
        )
        self._weapon_special_value_label.pack(side="right")
        self._weapon_special_slider = ctk.CTkSlider(
            self._weapon_special_frame,
            from_=1,
            to=9,
            number_of_steps=8,
            command=self._on_weapon_special_change,
            state="disabled",
        )
        self._weapon_special_slider.pack(side="left", fill="x", expand=True)
        self._weapon_special_slider.set(1)

        self._pack_static_layout()

    def _pack_static_layout(self) -> None:
        """第三条与特殊能力区始终占位。"""
        for widget in (
            self._ability_3_name_label,
            self._ability_3_frame,
            self._weapon_special_header,
            self._weapon_special_frame,
        ):
            if widget:
                widget.pack_forget()
        if self._ability_3_name_label:
            self._ability_3_name_label.pack(anchor="w")
        if self._ability_3_frame:
            self._ability_3_frame.pack(fill="x", padx=10, pady=(0, 5))
        if self._weapon_special_header:
            self._weapon_special_header.pack(fill="x", pady=(5, 0))
        if self._weapon_special_frame:
            self._weapon_special_frame.pack(fill="x", padx=10, pady=(0, 5))

    def _on_ability_1_change(self, value: float) -> None:
        level = int(value)
        if self._ability_1_label:
            self._ability_1_label.configure(text=str(level))
        self.special_ability_1_level.set(str(level))

    def _on_ability_2_change(self, value: float) -> None:
        level = int(value)
        if self._ability_2_label:
            self._ability_2_label.configure(text=str(level))
        self.special_ability_2_level.set(str(level))

    def _on_ability_3_change(self, value: float) -> None:
        if not self.current_special_ability_3_name:
            return
        level = int(value)
        if self._ability_3_label:
            self._ability_3_label.configure(text=str(level))
        self.special_ability_3_level.set(str(level))

    def _on_weapon_special_change(self, value: float) -> None:
        level = int(value)
        if self._weapon_special_value_label:
            self._weapon_special_value_label.configure(text=str(level))
        self.weapon_special_level.set(str(level))

    def _on_weapon_special_switch_change(self) -> None:
        if not self._weapon_special_available:
            self.weapon_special_enabled.set(False)
            self.weapon_special_level.set("0")
            if self._weapon_special_value_label:
                self._weapon_special_value_label.configure(text="0")
            return

        enabled = self.weapon_special_enabled.get()
        if self._weapon_special_slider:
            self._weapon_special_slider.configure(state="normal" if enabled else "disabled")

        if enabled:
            current = int(self._weapon_special_slider.get()) if self._weapon_special_slider else 1
            self.weapon_special_level.set(str(current))
            if self._weapon_special_value_label:
                self._weapon_special_value_label.configure(text=str(current))
        else:
            self.weapon_special_level.set("0")
            if self._weapon_special_value_label:
                self._weapon_special_value_label.configure(text="0")

    def refresh(self, weapon_data: Dict[str, Any]) -> None:
        """根据武器数据刷新面板。"""
        bonus_attrs = self._extract_bonus_attributes(weapon_data)
        sa_available, sa_name = self._parse_weapon_special_field(weapon_data)

        if len(bonus_attrs) >= 1:
            self.current_special_ability_1_name = bonus_attrs[0]
            self._reset_bonus_row(1, self.current_special_ability_1_name)
            self._show_bonus_row(1)
        else:
            self.current_special_ability_1_name = ""
            self._hide_bonus_row(1)

        if len(bonus_attrs) >= 2:
            self.current_special_ability_2_name = bonus_attrs[1]
            self._reset_bonus_row(2, self.current_special_ability_2_name)
            self._show_bonus_row(2)
        else:
            self.current_special_ability_2_name = ""
            self._hide_bonus_row(2)

        if len(bonus_attrs) >= 3:
            self.current_special_ability_3_name = bonus_attrs[2]
            self._configure_third_bonus_active(self.current_special_ability_3_name)
        else:
            self.current_special_ability_3_name = ""
            self._configure_third_bonus_placeholder()

        self._weapon_special_available = sa_available
        self.current_weapon_special_name = sa_name if sa_available else ""
        self._configure_weapon_special_row(sa_available, sa_name)

    @classmethod
    def _extract_bonus_attributes(cls, weapon_data: Dict[str, Any]) -> List[str]:
        keys = list(weapon_data.keys())
        try:
            start = keys.index('基础攻击力') + 1
            end = keys.index('特殊能力')
        except ValueError:
            return []
        result: List[str] = []
        for key in keys[start:end]:
            if key not in cls._BONUS_EXCLUDED and isinstance(weapon_data.get(key), list):
                result.append(key)
        return result[:3]

    @staticmethod
    def _parse_weapon_special_field(weapon_data: Dict[str, Any]) -> tuple[bool, str]:
        field = weapon_data.get('特殊能力', [])
        if not isinstance(field, list) or not field:
            return False, ""
        enabled = bool(field[0])
        name = field[1] if len(field) > 1 and isinstance(field[1], str) else ""
        return enabled, name

    def _reset_bonus_row(self, index: int, title: str) -> None:
        if index == 1:
            name_lbl, val_lbl, slider = (
                self._ability_1_name_label,
                self._ability_1_label,
                self._ability_1_slider,
            )
            level_var = self.special_ability_1_level
        else:
            name_lbl, val_lbl, slider = (
                self._ability_2_name_label,
                self._ability_2_label,
                self._ability_2_slider,
            )
            level_var = self.special_ability_2_level
        if name_lbl:
            name_lbl.configure(text=title)
        if val_lbl:
            val_lbl.configure(text="1")
        level_var.set("1")
        if slider:
            slider.configure(state="normal")
            slider.set(1)

    def _configure_third_bonus_active(self, title: str) -> None:
        if self._ability_3_name_label:
            self._ability_3_name_label.configure(text=title)
        if self._ability_3_label:
            self._ability_3_label.configure(text="1")
        if self._ability_3_slider:
            self._ability_3_slider.configure(state="normal")
            self._ability_3_slider.set(1)
        self.special_ability_3_level.set("1")

    def _configure_third_bonus_placeholder(self) -> None:
        if self._ability_3_name_label:
            self._ability_3_name_label.configure(text=self._PLACEHOLDER_NO_THIRD)
        if self._ability_3_label:
            self._ability_3_label.configure(text="—")
        if self._ability_3_slider:
            self._ability_3_slider.configure(state="disabled")
            self._ability_3_slider.set(1)
        self.special_ability_3_level.set("0")

    def _configure_weapon_special_row(self, available: bool, name: str) -> None:
        title = name if available and name else "特殊能力"
        if self._weapon_special_name_label:
            self._weapon_special_name_label.configure(text=title)

        self.weapon_special_enabled.set(False)
        self.weapon_special_level.set("0")
        if self._weapon_special_value_label:
            self._weapon_special_value_label.configure(text="0")
        if self._weapon_special_slider:
            self._weapon_special_slider.configure(state="disabled")
            self._weapon_special_slider.set(1)

        if self._weapon_special_switch:
            if available:
                self._weapon_special_switch.configure(state="normal")
            else:
                self._weapon_special_switch.configure(state="disabled")

    def _show_bonus_row(self, index: int) -> None:
        if index == 1:
            widgets = (self._ability_1_name_label, self._ability_1_frame)
        else:
            widgets = (self._ability_2_name_label, self._ability_2_frame)
        for widget in widgets:
            if widget and not widget.winfo_ismapped():
                if widget == widgets[0]:
                    widget.pack(anchor="w")
                else:
                    widget.pack(fill="x", padx=10, pady=(0, 5))

    def _hide_bonus_row(self, index: int) -> None:
        if index == 1:
            widgets = (self._ability_1_name_label, self._ability_1_frame)
        else:
            widgets = (self._ability_2_name_label, self._ability_2_frame)
        for widget in widgets:
            if widget:
                widget.pack_forget()

    def hide(self) -> None:
        """隐藏前两条附加属性（第三与特殊能力区仍占位）。"""
        self._hide_bonus_row(1)
        self._hide_bonus_row(2)

    def show(self) -> None:
        """按当前数据恢复前两条附加属性显示。"""
        if self.current_special_ability_1_name:
            self._show_bonus_row(1)
        if self.current_special_ability_2_name:
            self._show_bonus_row(2)


class SkillLevelPanel:
    """
    技能等级选择面板
    
    提供角色技能等级的滑块选择功能（战技、连携技、终结技）。
    
    属性：
        skill_1_level: 战技等级（StringVar）
        skill_2_level: 连携技等级（StringVar）
        skill_3_level: 终结技等级（StringVar）
    """
    
    def __init__(self, parent_frame: ctk.CTkFrame, my_font: ctk.CTkFont, on_change_callback=None):
        """
        初始化技能等级面板
        
        参数：
            parent_frame: 父框架容器
            my_font: 使用的字体配置
            on_change_callback: 技能等级变化时的回调函数
        """
        self.parent_frame = parent_frame
        self.my_font = my_font
        self.on_change_callback = on_change_callback
        
        # 技能等级变量
        self.skill_1_level: ctk.StringVar = ctk.StringVar(value="1")
        self.skill_2_level: ctk.StringVar = ctk.StringVar(value="1")
        self.skill_3_level: ctk.StringVar = ctk.StringVar(value="1")
        
        # 当前技能名称
        self.current_skill_1_name: str = "战技"
        self.current_skill_2_name: str = "连携技"
        self.current_skill_3_name: str = "终结技"
        
        # 技能倍率数据引用
        self._skill_1_data: list = []
        self._skill_2_data: list = []
        self._skill_3_data: list = []
        
        # UI控件
        self._skill_1_name_label: ctk.CTkLabel | None = None
        self._skill_1_label: ctk.CTkLabel | None = None
        self._skill_1_slider: ctk.CTkSlider | None = None
        self._skill_1_frame: ctk.CTkFrame | None = None
        
        self._skill_2_name_label: ctk.CTkLabel | None = None
        self._skill_2_label: ctk.CTkLabel | None = None
        self._skill_2_slider: ctk.CTkSlider | None = None
        self._skill_2_frame: ctk.CTkFrame | None = None
        
        self._skill_3_name_label: ctk.CTkLabel | None = None
        self._skill_3_label: ctk.CTkLabel | None = None
        self._skill_3_slider: ctk.CTkSlider | None = None
        self._skill_3_frame: ctk.CTkFrame | None = None
        
        # 构建GUI
        self._build_gui()
    
    def _build_gui(self) -> None:
        """构建技能等级滑块GUI"""
        # 战技等级
        self._skill_1_name_label = ctk.CTkLabel(self.parent_frame, text="战技", font=self.my_font)
        self._skill_1_name_label.pack(anchor="w")
        
        self._skill_1_frame = ctk.CTkFrame(self.parent_frame, fg_color="transparent")
        self._skill_1_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        self._skill_1_label = ctk.CTkLabel(self._skill_1_frame, text="1", font=self.my_font, width=30)
        self._skill_1_label.pack(side="right")
        
        self._skill_1_slider = ctk.CTkSlider(
            self._skill_1_frame,
            from_=1,
            to=12,
            number_of_steps=11,
            command=self._on_skill_1_change
        )
        self._skill_1_slider.pack(side="left", fill="x", expand=True)
        self._skill_1_slider.set(1)
        
        # 连携技等级
        self._skill_2_name_label = ctk.CTkLabel(self.parent_frame, text="连携技", font=self.my_font)
        self._skill_2_name_label.pack(anchor="w")
        
        self._skill_2_frame = ctk.CTkFrame(self.parent_frame, fg_color="transparent")
        self._skill_2_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        self._skill_2_label = ctk.CTkLabel(self._skill_2_frame, text="1", font=self.my_font, width=30)
        self._skill_2_label.pack(side="right")
        
        self._skill_2_slider = ctk.CTkSlider(
            self._skill_2_frame,
            from_=1,
            to=12,
            number_of_steps=11,
            command=self._on_skill_2_change
        )
        self._skill_2_slider.pack(side="left", fill="x", expand=True)
        self._skill_2_slider.set(1)
        
        # 终结技等级
        self._skill_3_name_label = ctk.CTkLabel(self.parent_frame, text="终结技", font=self.my_font)
        self._skill_3_name_label.pack(anchor="w")
        
        self._skill_3_frame = ctk.CTkFrame(self.parent_frame, fg_color="transparent")
        self._skill_3_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        self._skill_3_label = ctk.CTkLabel(self._skill_3_frame, text="1", font=self.my_font, width=30)
        self._skill_3_label.pack(side="right")
        
        self._skill_3_slider = ctk.CTkSlider(
            self._skill_3_frame,
            from_=1,
            to=12,
            number_of_steps=11,
            command=self._on_skill_3_change
        )
        self._skill_3_slider.pack(side="left", fill="x", expand=True)
        self._skill_3_slider.set(1)
    
    def _on_skill_1_change(self, value: float) -> None:
        """战技滑块值变化事件处理"""
        level = int(value)
        if self._skill_1_label:
            self._skill_1_label.configure(text=str(level))
        self.skill_1_level.set(str(level))
        if self.on_change_callback:
            self.on_change_callback()
    
    def _on_skill_2_change(self, value: float) -> None:
        """连携技滑块值变化事件处理"""
        level = int(value)
        if self._skill_2_label:
            self._skill_2_label.configure(text=str(level))
        self.skill_2_level.set(str(level))
        if self.on_change_callback:
            self.on_change_callback()
    
    def _on_skill_3_change(self, value: float) -> None:
        """终结技滑块值变化事件处理"""
        level = int(value)
        if self._skill_3_label:
            self._skill_3_label.configure(text=str(level))
        self.skill_3_level.set(str(level))
        if self.on_change_callback:
            self.on_change_callback()
    
    def refresh(self, char_data: Dict[str, Any]) -> None:
        """
        根据角色数据刷新技能等级面板
        
        参数：
            char_data: 角色数据字典
        """
        # 获取技能倍率数据
        self._skill_1_data = char_data.get("战技倍率", [])
        self._skill_2_data = char_data.get("连携技倍率", [])
        self._skill_3_data = char_data.get("终结技倍率", [])
        
        # 检查是否有多个技能
        # 战技
        if len(self._skill_1_data) >= 1:
            self.current_skill_1_name = "战技"
            if self._skill_1_name_label:
                self._skill_1_name_label.configure(text=self.current_skill_1_name)
            if self._skill_1_label:
                self._skill_1_label.configure(text="1")
            self.skill_1_level.set("1")
            if self._skill_1_slider:
                self._skill_1_slider.set(1)
            self._show_skill_1()
        else:
            self.current_skill_1_name = ""
            self._hide_skill_1()
        
        # 连携技
        if len(self._skill_2_data) >= 1:
            self.current_skill_2_name = "连携技"
            if self._skill_2_name_label:
                self._skill_2_name_label.configure(text=self.current_skill_2_name)
            if self._skill_2_label:
                self._skill_2_label.configure(text="1")
            self.skill_2_level.set("1")
            if self._skill_2_slider:
                self._skill_2_slider.set(1)
            self._show_skill_2()
        else:
            self.current_skill_2_name = ""
            self._hide_skill_2()
        
        # 终结技
        if len(self._skill_3_data) >= 1:
            self.current_skill_3_name = "终结技"
            if self._skill_3_name_label:
                self._skill_3_name_label.configure(text=self.current_skill_3_name)
            if self._skill_3_label:
                self._skill_3_label.configure(text="1")
            self.skill_3_level.set("1")
            if self._skill_3_slider:
                self._skill_3_slider.set(1)
            self._show_skill_3()
        else:
            self.current_skill_3_name = ""
            self._hide_skill_3()
    
    def _show_skill_1(self) -> None:
        """显示战技滑块"""
        if self._skill_1_name_label:
            self._skill_1_name_label.pack(anchor="w")
        if self._skill_1_frame:
            self._skill_1_frame.pack(fill="x", padx=10, pady=(0, 5))
    
    def _hide_skill_1(self) -> None:
        """隐藏战技滑块"""
        if self._skill_1_name_label:
            self._skill_1_name_label.pack_forget()
        if self._skill_1_frame:
            self._skill_1_frame.pack_forget()
    
    def _show_skill_2(self) -> None:
        """显示连携技滑块"""
        if self._skill_2_name_label:
            self._skill_2_name_label.pack(anchor="w")
        if self._skill_2_frame:
            self._skill_2_frame.pack(fill="x", padx=10, pady=(0, 5))
    
    def _hide_skill_2(self) -> None:
        """隐藏连携技滑块"""
        if self._skill_2_name_label:
            self._skill_2_name_label.pack_forget()
        if self._skill_2_frame:
            self._skill_2_frame.pack_forget()
    
    def _show_skill_3(self) -> None:
        """显示终结技滑块"""
        if self._skill_3_name_label:
            self._skill_3_name_label.pack(anchor="w")
        if self._skill_3_frame:
            self._skill_3_frame.pack(fill="x", padx=10, pady=(0, 5))
    
    def _hide_skill_3(self) -> None:
        """隐藏终结技滑块"""
        if self._skill_3_name_label:
            self._skill_3_name_label.pack_forget()
        if self._skill_3_frame:
            self._skill_3_frame.pack_forget()
    
    def hide(self) -> None:
        """隐藏所有技能等级面板"""
        self._hide_skill_1()
        self._hide_skill_2()
        self._hide_skill_3()
    
    def show(self) -> None:
        """显示所有技能等级面板（根据当前数据）"""
        if self.current_skill_1_name:
            self._show_skill_1()
        if self.current_skill_2_name:
            self._show_skill_2()
        if self.current_skill_3_name:
            self._show_skill_3()

