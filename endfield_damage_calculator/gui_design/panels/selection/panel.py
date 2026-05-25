#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
选择面板模块

此模块包含通用的类型/星级/名称/等级选择面板类，适用于角色和武器选择。

主要类：
- ChooseTypesStarsNamesLevels: 通用选择面板类
"""

from utils.platform_win32_patch import apply_platform_win32_patch

apply_platform_win32_patch()
import customtkinter as ctk
from typing import List, Dict, Any, Optional
from ..selection_components import TrustPanel, SpecialAbilityPanel, SkillLevelPanel
from .accessors import SelectionPanelAccessorsMixin
from .build import SelectionPanelBuildMixin
from .cascade import SelectionPanelCascadeMixin
from .state import SelectionPanelStateMixin


class ChooseTypesStarsNamesLevels(
    SelectionPanelBuildMixin,
    SelectionPanelCascadeMixin,
    SelectionPanelAccessorsMixin,
    SelectionPanelStateMixin,
):
    """
    通用选择面板类

    提供类型、星级、名称、等级的四级联动选择功能，适用于角色和武器选择。
    支持武器的特殊能力选择和角色的信赖等级选择。
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
        # 角色/武器侧默认展开「技能等级 / 武器技能」
        self._show_advanced_params_var: ctk.BooleanVar = ctk.BooleanVar(value=True)
        self._advanced_section_title: str = (
            "武器技能" if is_weapon_panel else "技能等级"
        )
        self._advanced_toggle_btn: ctk.CTkButton | None = None
        self._advanced_body: ctk.CTkFrame | None = None
        self._level_preset_80_btn: ctk.CTkButton | None = None
        self._level_preset_90_btn: ctk.CTkButton | None = None
        self._skill_preset_9_btn: ctk.CTkButton | None = None
        self._skill_preset_12_btn: ctk.CTkButton | None = None

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
