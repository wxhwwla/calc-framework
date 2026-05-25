#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""角色战技/连携/终结等级滑块。"""

from utils.platform_win32_patch import apply_platform_win32_patch

apply_platform_win32_patch()

import customtkinter as ctk
from typing import Any, Callable, Dict, List, Optional

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

