#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""特殊能力面板：控件构建与布局。"""

from __future__ import annotations

from typing import TYPE_CHECKING, List

import customtkinter as ctk

from gui_design.shared.weapon_display_text import (
    format_weapon_skill_slider_value,
    format_weapon_skill_title,
)

if TYPE_CHECKING:
    from .panel import SpecialAbilityPanel


class SpecialAbilityBuildMixin:
    """构建附加属性与特殊能力滑块，并按分段 pack。"""

    def _build_gui(self: SpecialAbilityPanel) -> None:
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

    def _apply_layout(self: SpecialAbilityPanel) -> None:
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
