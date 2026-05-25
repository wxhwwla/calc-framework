#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""武器普通/特殊技能与附加属性面板。"""

from utils.platform_win32_patch import apply_platform_win32_patch

apply_platform_win32_patch()

import customtkinter as ctk
from typing import Any, Dict, List, Optional

from character_weapon_equipment.weapon_data.special_fields import (
    bonus_attribute_keys,
    read_weapon_special_slots,
)
from gui_design.label_layout import bind_wrapped_label
from gui_design.weapon_display_text import (
    extract_effect_display_name,
    format_weapon_skill_slider_value,
    format_weapon_skill_title,
    split_special_skill_display,
)

class SpecialAbilityPanel:
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

        self._build_gui()

    def _build_gui(self) -> None:
        """构建附加属性与特殊能力滑块"""
        self._ability_1_name_label = ctk.CTkLabel(
            self.parent_frame,
            text=format_weapon_skill_title(self._BONUS_SKILL_PREFIX[0]),
            font=self.my_font,
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
            self.parent_frame,
            text=format_weapon_skill_title(self._BONUS_SKILL_PREFIX[1]),
            font=self.my_font,
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
            self.parent_frame,
            text=format_weapon_skill_title(self._BONUS_SKILL_PREFIX[2]),
            font=self.my_font,
        )
        self._ability_3_frame = ctk.CTkFrame(self.parent_frame, fg_color="transparent")
        self._ability_3_label = ctk.CTkLabel(
            self._ability_3_frame,
            text=format_weapon_skill_slider_value(active=False),
            font=self.my_font,
            width=30,
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

        self._weapon_special_name_label = ctk.CTkLabel(
            self.parent_frame,
            text=format_weapon_skill_title(self._WEAPON_SPECIAL_PREFIX[0]),
            font=self.my_font,
        )
        self._weapon_special_frame = ctk.CTkFrame(self.parent_frame, fg_color="transparent")
        self._weapon_special_value_label = ctk.CTkLabel(
            self._weapon_special_frame, text="1", font=self.my_font, width=30
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

        self._weapon_special_stack_name_label = ctk.CTkLabel(
            self.parent_frame,
            text=f"{self._WEAPON_SPECIAL_PREFIX[0]} 叠加",
            font=self.my_font,
        )
        self._weapon_special_stack_frame = ctk.CTkFrame(self.parent_frame, fg_color="transparent")
        self._weapon_special_stack_value_label = ctk.CTkLabel(
            self._weapon_special_stack_frame, text="0", font=self.my_font, width=30
        )
        self._weapon_special_stack_value_label.pack(side="right")
        self._weapon_special_stack_slider = ctk.CTkSlider(
            self._weapon_special_stack_frame,
            from_=0,
            to=2,
            number_of_steps=2,
            command=self._on_weapon_special_stack_change,
            state="disabled",
        )
        self._weapon_special_stack_slider.pack(side="left", fill="x", expand=True)
        self._weapon_special_stack_slider.set(0)

        self._weapon_special_2_name_label = ctk.CTkLabel(
            self.parent_frame,
            text=format_weapon_skill_title(self._WEAPON_SPECIAL_PREFIX[1]),
            font=self.my_font,
        )
        self._weapon_special_2_frame = ctk.CTkFrame(self.parent_frame, fg_color="transparent")
        self._weapon_special_2_value_label = ctk.CTkLabel(
            self._weapon_special_2_frame, text="1", font=self.my_font, width=30
        )
        self._weapon_special_2_value_label.pack(side="right")
        self._weapon_special_2_slider = ctk.CTkSlider(
            self._weapon_special_2_frame,
            from_=1,
            to=9,
            number_of_steps=8,
            command=self._on_weapon_special_2_change,
            state="disabled",
        )
        self._weapon_special_2_slider.pack(side="left", fill="x", expand=True)
        self._weapon_special_2_slider.set(1)

        self._weapon_special_2_stack_name_label = ctk.CTkLabel(
            self.parent_frame,
            text=f"{self._WEAPON_SPECIAL_PREFIX[1]} 叠加",
            font=self.my_font,
        )
        self._weapon_special_2_stack_frame = ctk.CTkFrame(self.parent_frame, fg_color="transparent")
        self._weapon_special_2_stack_value_label = ctk.CTkLabel(
            self._weapon_special_2_stack_frame, text="0", font=self.my_font, width=30
        )
        self._weapon_special_2_stack_value_label.pack(side="right")
        self._weapon_special_2_stack_slider = ctk.CTkSlider(
            self._weapon_special_2_stack_frame,
            from_=0,
            to=2,
            number_of_steps=2,
            command=self._on_weapon_special_2_stack_change,
            state="disabled",
        )
        self._weapon_special_2_stack_slider.pack(side="left", fill="x", expand=True)
        self._weapon_special_2_stack_slider.set(0)

        self._normal_section_label = ctk.CTkLabel(
            self.parent_frame,
            text="普通技能",
            font=self.my_font,
            text_color="#AAAAAA",
        )
        self._special_section_label = ctk.CTkLabel(
            self.parent_frame,
            text="特殊技能",
            font=self.my_font,
            text_color="#AAAAAA",
        )

        self._apply_layout()

    def _apply_layout(self) -> None:
        """按 普通技能 → 特殊技能 分段 pack。"""
        show_bonus = not self._bonus_rows_suppressed
        normal_rows: List[tuple[ctk.CTkLabel | None, ctk.CTkFrame | None, bool]] = [
            (
                self._ability_1_name_label,
                self._ability_1_frame,
                show_bonus and bool(self.current_special_ability_1_name),
            ),
            (
                self._ability_2_name_label,
                self._ability_2_frame,
                show_bonus and bool(self.current_special_ability_2_name),
            ),
            (self._ability_3_name_label, self._ability_3_frame, True),
        ]
        special_rows: List[tuple[ctk.CTkLabel | None, ctk.CTkFrame | None, bool]] = [
            (
                self._weapon_special_name_label,
                self._weapon_special_frame,
                self._weapon_special_available,
            ),
            (
                self._weapon_special_stack_name_label,
                self._weapon_special_stack_frame,
                self._weapon_special_available and self._weapon_special_max_stack > 1,
            ),
            (
                self._weapon_special_2_name_label,
                self._weapon_special_2_frame,
                self._weapon_special_2_available,
            ),
            (
                self._weapon_special_2_stack_name_label,
                self._weapon_special_2_stack_frame,
                self._weapon_special_2_available and self._weapon_special_2_max_stack > 1,
            ),
        ]
        for lbl in (self._normal_section_label, self._special_section_label):
            lbl.pack_forget()
        for name_lbl, frame, _ in normal_rows + special_rows:
            if name_lbl:
                name_lbl.pack_forget()
            if frame:
                frame.pack_forget()

        def _pack_rows(rows: list, *, section: ctk.CTkLabel | None = None) -> None:
            if not any(visible for _, _, visible in rows):
                return
            if section is not None:
                section.pack(anchor="w", padx=8, pady=(6, 2))
            for name_lbl, frame, visible in rows:
                if not visible:
                    continue
                if name_lbl:
                    name_lbl.pack(anchor="w")
                if frame:
                    frame.pack(fill="x", padx=10, pady=(0, 5))

        _pack_rows(normal_rows, section=self._normal_section_label)
        _pack_rows(special_rows, section=self._special_section_label)

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
        if not self._weapon_special_available:
            return
        level = int(value)
        if self._weapon_special_value_label:
            self._weapon_special_value_label.configure(text=str(level))
        self.weapon_special_level.set(str(level))

    def _on_weapon_special_stack_change(self, value: float) -> None:
        if not self._weapon_special_available or self._weapon_special_max_stack <= 1:
            return
        stack = int(value)
        if self._weapon_special_stack_value_label:
            self._weapon_special_stack_value_label.configure(text=str(stack))
        self.weapon_special_stack.set(str(stack))

    def _on_weapon_special_2_change(self, value: float) -> None:
        if not self._weapon_special_2_available:
            return
        level = int(value)
        if self._weapon_special_2_value_label:
            self._weapon_special_2_value_label.configure(text=str(level))
        self.weapon_special_2_level.set(str(level))

    def _on_weapon_special_2_stack_change(self, value: float) -> None:
        if not self._weapon_special_2_available or self._weapon_special_2_max_stack <= 1:
            return
        stack = int(value)
        if self._weapon_special_2_stack_value_label:
            self._weapon_special_2_stack_value_label.configure(text=str(stack))
        self.weapon_special_2_stack.set(str(stack))

    def refresh(self, weapon_data: Dict[str, Any]) -> None:
        """根据武器数据刷新面板。"""
        bonus_attrs = self._extract_bonus_attributes(weapon_data)
        slots = read_weapon_special_slots(weapon_data)
        sa_available, sa_name, _, sa_max_stack = slots[0]
        sa2_available, sa2_name, _, sa2_max_stack = slots[1]

        if len(bonus_attrs) >= 1:
            self.current_special_ability_1_name = bonus_attrs[0]
            self._reset_bonus_row(1, self.current_special_ability_1_name)
        else:
            self.current_special_ability_1_name = ""

        if len(bonus_attrs) >= 2:
            self.current_special_ability_2_name = bonus_attrs[1]
            self._reset_bonus_row(2, self.current_special_ability_2_name)
        else:
            self.current_special_ability_2_name = ""

        if len(bonus_attrs) >= 3:
            self.current_special_ability_3_name = bonus_attrs[2]
            self._configure_third_bonus_active(self.current_special_ability_3_name)
        else:
            self.current_special_ability_3_name = ""
            self._configure_third_bonus_placeholder()

        self._weapon_special_available = sa_available
        self.current_weapon_special_name = sa_name if sa_available else ""
        self._weapon_special_max_stack = sa_max_stack if sa_available else 1
        self._configure_weapon_special_row(
            1,
            sa_available,
            sa_name,
            sa_max_stack,
            self._weapon_special_name_label,
            self._weapon_special_value_label,
            self._weapon_special_slider,
            self.weapon_special_level,
            self._weapon_special_stack_name_label,
            self._weapon_special_stack_value_label,
            self._weapon_special_stack_slider,
            self.weapon_special_stack,
        )

        self._weapon_special_2_available = sa2_available
        self.current_weapon_special_2_name = sa2_name if sa2_available else ""
        self._weapon_special_2_max_stack = sa2_max_stack if sa2_available else 1
        self._configure_weapon_special_row(
            2,
            sa2_available,
            sa2_name,
            sa2_max_stack,
            self._weapon_special_2_name_label,
            self._weapon_special_2_value_label,
            self._weapon_special_2_slider,
            self.weapon_special_2_level,
            self._weapon_special_2_stack_name_label,
            self._weapon_special_2_stack_value_label,
            self._weapon_special_2_stack_slider,
            self.weapon_special_2_stack,
        )
        for lbl in (
            self._ability_1_name_label,
            self._ability_2_name_label,
            self._ability_3_name_label,
            self._weapon_special_name_label,
            self._weapon_special_2_name_label,
        ):
            if lbl is not None:
                bind_wrapped_label(lbl, self.parent_frame, padding=16, min_wrap=120)

        self._apply_layout()

    @classmethod
    def _extract_bonus_attributes(cls, weapon_data: Dict[str, Any]) -> List[str]:
        return bonus_attribute_keys(weapon_data)[:3]

    @staticmethod
    def _parse_weapon_special_field(weapon_data: Dict[str, Any]) -> tuple[bool, str]:
        """兼容旧测试：仅返回特殊能力1（或旧 ``特殊能力``）。"""
        enabled, name, _ = read_weapon_special_slots(weapon_data)[0]
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
            prefix = self._BONUS_SKILL_PREFIX[index - 1]
            display = extract_effect_display_name(title) if title else ""
            name_lbl.configure(text=format_weapon_skill_title(prefix, display))
        if val_lbl:
            val_lbl.configure(text="1")
        level_var.set("1")
        if slider:
            slider.configure(state="normal")
            slider.set(1)

    def _configure_third_bonus_active(self, title: str) -> None:
        if self._ability_3_name_label:
            display = extract_effect_display_name(title) if title else ""
            self._ability_3_name_label.configure(
                text=format_weapon_skill_title(self._BONUS_SKILL_PREFIX[2], display)
            )
        if self._ability_3_label:
            self._ability_3_label.configure(text="1")
        if self._ability_3_slider:
            self._ability_3_slider.configure(state="normal")
            self._ability_3_slider.set(1)
        self.special_ability_3_level.set("1")

    def _configure_third_bonus_placeholder(self) -> None:
        if self._ability_3_name_label:
            self._ability_3_name_label.configure(
                text=format_weapon_skill_title(self._BONUS_SKILL_PREFIX[2])
            )
        if self._ability_3_label:
            self._ability_3_label.configure(
                text=format_weapon_skill_slider_value(active=False)
            )
        if self._ability_3_slider:
            self._ability_3_slider.configure(state="disabled")
            self._ability_3_slider.set(1)
        self.special_ability_3_level.set("0")

    def _configure_weapon_special_row(
        self,
        index: int,
        available: bool,
        name: str,
        max_stack: int,
        name_label: ctk.CTkLabel | None,
        value_label: ctk.CTkLabel | None,
        slider: ctk.CTkSlider | None,
        level_var: ctk.StringVar,
        stack_name_label: ctk.CTkLabel | None,
        stack_value_label: ctk.CTkLabel | None,
        stack_slider: ctk.CTkSlider | None,
        stack_var: ctk.StringVar,
    ) -> None:
        prefix = self._WEAPON_SPECIAL_PREFIX[index - 1]
        if available and name:
            condition, effect = split_special_skill_display(name)
            if name_label:
                if condition:
                    name_label.configure(text=f"{prefix}：{condition}\n{effect}")
                else:
                    name_label.configure(text=format_weapon_skill_title(prefix, effect))
            if stack_name_label:
                stack_name_label.configure(text=f"{prefix} 叠加")
            if value_label:
                value_label.configure(text="1")
            if stack_value_label:
                stack_value_label.configure(text="0")
            if slider:
                slider.configure(state="normal", from_=1, to=9, number_of_steps=8)
                slider.set(1)
            if stack_slider:
                if max_stack > 1:
                    stack_slider.configure(
                        state="normal",
                        from_=0,
                        to=max_stack,
                        number_of_steps=max_stack,
                    )
                    stack_slider.set(0)
                else:
                    stack_slider.configure(state="disabled")
                    stack_slider.set(0)
            level_var.set("1")
            stack_var.set("0")
        else:
            if name_label:
                name_label.configure(text=format_weapon_skill_title(prefix))
            if stack_name_label:
                stack_name_label.configure(text=f"{prefix} 叠加")
            if value_label:
                value_label.configure(text="0")
            if stack_value_label:
                stack_value_label.configure(text="0")
            if slider:
                slider.configure(state="disabled")
                slider.set(1)
            if stack_slider:
                stack_slider.configure(state="disabled")
                stack_slider.set(0)
            level_var.set("1")
            stack_var.set("0")

    def hide(self) -> None:
        """隐藏前两条附加属性（第三与特殊能力区仍占位）。"""
        self._bonus_rows_suppressed = True
        self._apply_layout()

    def show(self) -> None:
        """按当前数据恢复前两条附加属性显示。"""
        self._bonus_rows_suppressed = False
        self._apply_layout()


