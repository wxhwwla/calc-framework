#!/usr/bin/env python3
"""武器普通/特殊技能与附加属性面板。"""

from __future__ import annotations

from utils.platform_win32_patch import apply_platform_win32_patch

apply_platform_win32_patch()

import customtkinter as ctk

from .build_mixin import SpecialAbilityBuildMixin
from .handlers_mixin import SpecialAbilityHandlersMixin
from .refresh_mixin import SpecialAbilityRefreshMixin


class SpecialAbilityPanel(
    SpecialAbilityBuildMixin,
    SpecialAbilityHandlersMixin,
    SpecialAbilityRefreshMixin,
):
    """
    武器附加属性与特殊能力选择面板。

    布局（自上而下，pack 顺序固定）：
    第一技能 → 第二技能 → 第三技能 → 特殊技能
    """

    _BONUS_EXCLUDED = frozenset(
        {"名称", "类型", "星级", "等级", "潜能", "基础攻击力", "特殊能力", "特殊能力1", "特殊能力2"}
    )
    _BONUS_SKILL_PREFIX = ("第一技能", "第二技能", "第三技能")
    _WEAPON_SPECIAL_PREFIX = ("特殊一", "特殊二")

    def __init__(self, parent_frame: ctk.CTkFrame, my_font: ctk.CTkFont):
        self.parent_frame = parent_frame
        self.my_font = my_font

        self.special_ability_1_level: ctk.StringVar = ctk.StringVar(value="1")
        self.special_ability_2_level: ctk.StringVar = ctk.StringVar(value="1")
        self.special_ability_3_level: ctk.StringVar = ctk.StringVar(value="0")

        self.current_special_ability_1_name: str = ""
        self.current_special_ability_2_name: str = ""
        self.current_special_ability_3_name: str = ""

        self.weapon_special_level: ctk.StringVar = ctk.StringVar(value="1")
        self.weapon_special_stack: ctk.StringVar = ctk.StringVar(value="0")
        self.weapon_special_2_level: ctk.StringVar = ctk.StringVar(value="1")
        self.weapon_special_2_stack: ctk.StringVar = ctk.StringVar(value="0")
        self.current_weapon_special_name: str = ""
        self.current_weapon_special_2_name: str = ""
        self._weapon_special_available: bool = False
        self._weapon_special_2_available: bool = False
        self._weapon_special_max_stack: int = 1
        self._weapon_special_2_max_stack: int = 1
        self._bonus_rows_suppressed: bool = False

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

        self._weapon_special_name_label: ctk.CTkLabel | None = None
        self._weapon_special_frame: ctk.CTkFrame | None = None
        self._weapon_special_value_label: ctk.CTkLabel | None = None
        self._weapon_special_slider: ctk.CTkSlider | None = None

        self._weapon_special_stack_name_label: ctk.CTkLabel | None = None
        self._weapon_special_stack_frame: ctk.CTkFrame | None = None
        self._weapon_special_stack_value_label: ctk.CTkLabel | None = None
        self._weapon_special_stack_slider: ctk.CTkSlider | None = None

        self._weapon_special_2_name_label: ctk.CTkLabel | None = None
        self._weapon_special_2_frame: ctk.CTkFrame | None = None
        self._weapon_special_2_value_label: ctk.CTkLabel | None = None
        self._weapon_special_2_slider: ctk.CTkSlider | None = None

        self._weapon_special_2_stack_name_label: ctk.CTkLabel | None = None
        self._weapon_special_2_stack_frame: ctk.CTkFrame | None = None
        self._weapon_special_2_stack_value_label: ctk.CTkLabel | None = None
        self._weapon_special_2_stack_slider: ctk.CTkSlider | None = None

        self._normal_section_label: ctk.CTkLabel | None = None
        self._special_section_label: ctk.CTkLabel | None = None

        self._build_gui()

    def hide(self) -> None:
        """隐藏前两条附加属性（第三与特殊能力区仍占位）。"""
        self._bonus_rows_suppressed = True
        self._apply_layout()

    def show(self) -> None:
        """按当前数据恢复前两条附加属性显示。"""
        self._bonus_rows_suppressed = False
        self._apply_layout()
