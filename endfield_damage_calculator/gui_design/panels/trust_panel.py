#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""角色信赖等级滑块。"""

from utils.platform_win32_patch import apply_platform_win32_patch

apply_platform_win32_patch()

import customtkinter as ctk
from typing import Optional

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


