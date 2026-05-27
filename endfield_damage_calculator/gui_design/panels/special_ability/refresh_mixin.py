#!/usr/bin/env python3
"""特殊能力面板：数据刷新与行配置。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import customtkinter as ctk

from character_weapon_equipment.weapon_data.special_fields import (
    bonus_attribute_keys,
    read_weapon_special_slots,
)
from gui_design.layout.label_layout import bind_wrapped_label
from gui_design.shared.weapon_display_text import (
    extract_effect_display_name,
    format_weapon_skill_slider_value,
    format_weapon_skill_title,
    split_special_skill_display,
)

if TYPE_CHECKING:
    from .panel import SpecialAbilityPanel


class SpecialAbilityRefreshMixin:
    """根据武器数据刷新面板控件。"""

    def refresh(self: SpecialAbilityPanel, weapon_data: dict[str, Any]) -> None:
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
    def _extract_bonus_attributes(cls, weapon_data: dict[str, Any]) -> list[str]:
        return bonus_attribute_keys(weapon_data)[:3]

    @staticmethod
    def _parse_weapon_special_field(weapon_data: dict[str, Any]) -> tuple[bool, str]:
        """兼容旧测试：仅返回特殊能力1（或旧 ``特殊能力``）。"""
        enabled, name, _ = read_weapon_special_slots(weapon_data)[0]
        return enabled, name

    def _reset_bonus_row(self: SpecialAbilityPanel, index: int, title: str) -> None:
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

    def _configure_third_bonus_active(self: SpecialAbilityPanel, title: str) -> None:
        if self._ability_3_name_label:
            display = extract_effect_display_name(title) if title else ""
            self._ability_3_name_label.configure(text=format_weapon_skill_title(self._BONUS_SKILL_PREFIX[2], display))
        if self._ability_3_label:
            self._ability_3_label.configure(text="1")
        if self._ability_3_slider:
            self._ability_3_slider.configure(state="normal")
            self._ability_3_slider.set(1)
        self.special_ability_3_level.set("1")

    def _configure_third_bonus_placeholder(self: SpecialAbilityPanel) -> None:
        if self._ability_3_name_label:
            self._ability_3_name_label.configure(text=format_weapon_skill_title(self._BONUS_SKILL_PREFIX[2]))
        if self._ability_3_label:
            self._ability_3_label.configure(text=format_weapon_skill_slider_value(active=False))
        if self._ability_3_slider:
            self._ability_3_slider.configure(state="disabled")
            self._ability_3_slider.set(1)
        self.special_ability_3_level.set("0")

    def _configure_weapon_special_row(
        self: SpecialAbilityPanel,
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
