#!/usr/bin/env python3
"""选择面板：布局构建与预设。"""

from __future__ import annotations

from utils.platform_win32_patch import apply_platform_win32_patch

apply_platform_win32_patch()
import customtkinter as ctk

from ..selection_components import SkillLevelPanel, SpecialAbilityPanel, TrustPanel


class SelectionPanelBuildMixin:
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
            level_frame, from_=1, to=90, number_of_steps=89, command=self._on_level_slider_change
        )
        self.level_slider.pack(side="left", fill="x", expand=True)
        try:
            self.level_slider.set(1)
        except ZeroDivisionError:
            # 处理初始化时的除零问题
            pass
        self._build_level_preset_buttons()

        if not self.is_weapon_panel:
            self.trust_panel = TrustPanel(self.frame, self.my_font)
            self._build_advanced_params_container()
            assert self._advanced_body is not None
            self.skill_level_panel = SkillLevelPanel(self._advanced_body, self.my_font)
        elif self.is_weapon_panel:
            self._build_advanced_params_container()
            assert self._advanced_body is not None
            self.special_ability_panel = SpecialAbilityPanel(self._advanced_body, self.my_font)

    def _build_level_preset_buttons(self) -> None:
        """等级快捷预设：一键设置 80/90 级。"""
        preset_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        preset_frame.pack(fill="x", padx=10, pady=(0, 4))
        preset_frame.grid_columnconfigure(0, weight=1)
        preset_frame.grid_columnconfigure(1, weight=1)
        self._level_preset_80_btn = ctk.CTkButton(
            preset_frame,
            text="80级",
            font=self.my_font,
            height=28,
            command=lambda: self._apply_level_preset(80),
        )
        self._level_preset_80_btn.grid(row=0, column=0, padx=(0, 3), sticky="ew")
        self._level_preset_90_btn = ctk.CTkButton(
            preset_frame,
            text="90级",
            font=self.my_font,
            height=28,
            command=lambda: self._apply_level_preset(90),
        )
        self._level_preset_90_btn.grid(row=0, column=1, padx=(3, 0), sticky="ew")

    def _apply_level_preset(self, target_level: int) -> None:
        """将当前面板等级设置为预设值（自动夹到有效范围）。"""
        if self.level_slider is None:
            return
        if str(self.level_slider.cget("state")) == "disabled":
            return
        try:
            max_level = int(float(self.level_slider.cget("to")))
        except Exception:
            max_level = 90
        clamped = max(1, min(int(target_level), max_level))
        try:
            self.level_slider.set(clamped)
            self._on_level_slider_change(float(clamped))
        except ZeroDivisionError:
            self.selected_level.set(str(clamped))
            if self.level_label is not None:
                self.level_label.configure(text=str(clamped))

    def _apply_character_skill_preset(self, target_level: int) -> None:
        """角色技能一键预设（9/12）。"""
        if self.skill_level_panel is None:
            return
        skill_panel = self.skill_level_panel
        for slider, level_var, name in (
            (skill_panel._skill_1_slider, skill_panel.skill_1_level, skill_panel.current_skill_1_name),
            (skill_panel._skill_2_slider, skill_panel.skill_2_level, skill_panel.current_skill_2_name),
            (skill_panel._skill_3_slider, skill_panel.skill_3_level, skill_panel.current_skill_3_name),
        ):
            if not name:
                continue
            if slider is None or str(slider.cget("state")) == "disabled":
                level_var.set(str(target_level))
                continue
            try:
                max_level = int(float(slider.cget("to")))
            except Exception:
                max_level = 12
            clamped = max(1, min(int(target_level), max_level))
            slider.set(clamped)
            if slider is skill_panel._skill_1_slider:
                skill_panel._on_skill_1_change(float(clamped))
            elif slider is skill_panel._skill_2_slider:
                skill_panel._on_skill_2_change(float(clamped))
            else:
                skill_panel._on_skill_3_change(float(clamped))

    def _apply_weapon_skill_preset(self, target_level: int) -> None:
        """武器词条与特殊能力一键预设（默认 9 级）。"""
        if self.special_ability_panel is None:
            return
        panel = self.special_ability_panel

        if panel.current_special_ability_1_name and panel._ability_1_slider is not None:
            clamped = max(1, min(int(target_level), 9))
            panel._ability_1_slider.set(clamped)
            panel._on_ability_1_change(float(clamped))
        if panel.current_special_ability_2_name and panel._ability_2_slider is not None:
            clamped = max(1, min(int(target_level), 9))
            panel._ability_2_slider.set(clamped)
            panel._on_ability_2_change(float(clamped))
        if panel.current_special_ability_3_name and panel._ability_3_slider is not None:
            if str(panel._ability_3_slider.cget("state")) != "disabled":
                clamped = max(1, min(int(target_level), 9))
                panel._ability_3_slider.set(clamped)
                panel._on_ability_3_change(float(clamped))
        if panel._weapon_special_available and panel._weapon_special_slider is not None:
            if str(panel._weapon_special_slider.cget("state")) != "disabled":
                clamped = max(1, min(int(target_level), 9))
                panel._weapon_special_slider.set(clamped)
                panel._on_weapon_special_change(float(clamped))
        if panel._weapon_special_2_available and panel._weapon_special_2_slider is not None:
            if str(panel._weapon_special_2_slider.cget("state")) != "disabled":
                clamped = max(1, min(int(target_level), 9))
                panel._weapon_special_2_slider.set(clamped)
                panel._on_weapon_special_2_change(float(clamped))

    def _build_advanced_params_container(self) -> None:
        """构建低频参数折叠区（角色=技能等级，武器=高级参数）。"""
        collapsed_label = f"{self._advanced_section_title}（展开）"
        self._advanced_toggle_btn = ctk.CTkButton(
            self.frame,
            text=collapsed_label,
            font=self.my_font,
            fg_color="transparent",
            border_width=1,
            command=self._toggle_advanced_params,
            height=30,
        )
        self._advanced_toggle_btn.pack(fill="x", padx=10, pady=(4, 4))
        self._advanced_body = ctk.CTkFrame(self.frame, fg_color="transparent")
        self._advanced_body.pack(fill="x", padx=0, pady=(0, 4))
        if not self.is_weapon_panel:
            self._skill_preset_9_btn = ctk.CTkButton(
                self._advanced_body,
                text="技能9级",
                font=self.my_font,
                height=28,
                command=lambda: self._apply_character_skill_preset(9),
            )
            self._skill_preset_9_btn.pack(fill="x", padx=10, pady=(0, 4))
            self._skill_preset_12_btn = ctk.CTkButton(
                self._advanced_body,
                text="技能12级",
                font=self.my_font,
                height=28,
                command=lambda: self._apply_character_skill_preset(12),
            )
            self._skill_preset_12_btn.pack(fill="x", padx=10, pady=(0, 4))
        else:
            self._skill_preset_9_btn = ctk.CTkButton(
                self._advanced_body,
                text="技能9级",
                font=self.my_font,
                height=28,
                command=lambda: self._apply_weapon_skill_preset(9),
            )
            self._skill_preset_9_btn.pack(fill="x", padx=10, pady=(0, 4))
        self._refresh_advanced_params_visibility()

    def _toggle_advanced_params(self) -> None:
        self._show_advanced_params_var.set(not bool(self._show_advanced_params_var.get()))
        self._refresh_advanced_params_visibility()

    def _refresh_advanced_params_visibility(self) -> None:
        expanded = bool(self._show_advanced_params_var.get())
        if self._advanced_toggle_btn is not None:
            title = self._advanced_section_title
            self._advanced_toggle_btn.configure(text=f"{title}（收起）" if expanded else f"{title}（展开）")
        if self._advanced_body is not None:
            if expanded:
                self._advanced_body.pack(fill="x", padx=0, pady=(0, 4))
            else:
                self._advanced_body.pack_forget()
