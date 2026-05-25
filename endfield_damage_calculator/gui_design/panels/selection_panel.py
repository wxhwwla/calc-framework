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
    │ 信赖滑块（角色，主区）   │
    │ 技能等级折叠（角色）     │
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
            self._advanced_toggle_btn.configure(
                text=f"{title}（收起）" if expanded else f"{title}（展开）"
            )
        if self._advanced_body is not None:
            if expanded:
                self._advanced_body.pack(fill="x", padx=0, pady=(0, 4))
            else:
                self._advanced_body.pack_forget()

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
    
    def get_normal_skill_1_name(self) -> str:
        """获取第一技能名称（仅武器面板有效）。"""
        if self.special_ability_panel:
            return self.special_ability_panel.current_special_ability_1_name
        return ""

    def get_special_ability_1_name(self) -> str:
        """兼容旧命名：第一技能名称。"""
        return self.get_normal_skill_1_name()

    def get_normal_skill_1_level(self) -> int:
        """获取第一技能等级（仅武器面板有效）。"""
        if self.special_ability_panel:
            level_str = self.special_ability_panel.special_ability_1_level.get()
            return int(level_str) if level_str.isdigit() else 0
        return 0

    def get_special_ability_1_level(self) -> int:
        """兼容旧命名：第一技能等级。"""
        return self.get_normal_skill_1_level()

    def get_normal_skill_2_name(self) -> str:
        """获取第二技能名称（仅武器面板有效）。"""
        if self.special_ability_panel:
            return self.special_ability_panel.current_special_ability_2_name
        return ""

    def get_special_ability_2_name(self) -> str:
        """兼容旧命名：第二技能名称。"""
        return self.get_normal_skill_2_name()

    def get_normal_skill_2_level(self) -> int:
        """获取第二技能等级（仅武器面板有效）。"""
        if self.special_ability_panel:
            level_str = self.special_ability_panel.special_ability_2_level.get()
            return int(level_str) if level_str.isdigit() else 0
        return 0

    def get_special_ability_2_level(self) -> int:
        """兼容旧命名：第二技能等级。"""
        return self.get_normal_skill_2_level()

    def get_normal_skill_3_name(self) -> str:
        """获取第三技能名称（仅武器面板有效）。"""
        if self.special_ability_panel:
            return self.special_ability_panel.current_special_ability_3_name
        return ""

    def get_special_ability_3_name(self) -> str:
        """兼容旧命名：第三技能名称。"""
        return self.get_normal_skill_3_name()

    def get_normal_skill_3_level(self) -> int:
        """获取第三技能等级（仅武器面板有效）。"""
        if self.special_ability_panel:
            level_str = self.special_ability_panel.special_ability_3_level.get()
            return int(level_str) if level_str.isdigit() else 0
        return 0

    def get_special_ability_3_level(self) -> int:
        """兼容旧命名：第三技能等级。"""
        return self.get_normal_skill_3_level()

    def get_special_skill_1_name(self) -> str:
        """获取特殊一名称（仅武器面板有效）。"""
        if self.special_ability_panel:
            return self.special_ability_panel.current_weapon_special_name
        return ""

    def get_weapon_special_name(self) -> str:
        """兼容旧命名：特殊一名称。"""
        return self.get_special_skill_1_name()

    def get_special_skill_1_level(self) -> int:
        """获取特殊一等级（1-9）。"""
        if self.special_ability_panel:
            level_str = self.special_ability_panel.weapon_special_level.get()
            return int(level_str) if level_str.isdigit() else 1
        return 1

    def get_weapon_special_level(self) -> int:
        """兼容旧命名：特殊一等级。"""
        return self.get_special_skill_1_level()

    def get_special_skill_1_stack(self) -> int:
        """获取特殊一叠加层数。"""
        if self.special_ability_panel:
            stack_str = self.special_ability_panel.weapon_special_stack.get()
            return int(stack_str) if stack_str.isdigit() else 0
        return 0

    def get_weapon_special_stack(self) -> int:
        """兼容旧命名：特殊一叠加层数。"""
        return self.get_special_skill_1_stack()

    def get_special_skill_2_name(self) -> str:
        """获取特殊二名称（仅武器面板有效）。"""
        if self.special_ability_panel:
            return self.special_ability_panel.current_weapon_special_2_name
        return ""

    def get_weapon_special_2_name(self) -> str:
        """兼容旧命名：特殊二名称。"""
        return self.get_special_skill_2_name()

    def get_special_skill_2_level(self) -> int:
        """获取特殊二等级（1-9）。"""
        if self.special_ability_panel:
            level_str = self.special_ability_panel.weapon_special_2_level.get()
            return int(level_str) if level_str.isdigit() else 1
        return 1

    def get_weapon_special_2_level(self) -> int:
        """兼容旧命名：特殊二等级。"""
        return self.get_special_skill_2_level()

    def get_special_skill_2_stack(self) -> int:
        """获取特殊二叠加层数。"""
        if self.special_ability_panel:
            stack_str = self.special_ability_panel.weapon_special_2_stack.get()
            return int(stack_str) if stack_str.isdigit() else 0
        return 0

    def get_weapon_special_2_stack(self) -> int:
        """兼容旧命名：特殊二叠加层数。"""
        return self.get_special_skill_2_stack()

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
        if self._level_preset_80_btn:
            self._level_preset_80_btn.configure(state="disabled")
        if self._level_preset_90_btn:
            self._level_preset_90_btn.configure(state="disabled")
        if self._skill_preset_9_btn:
            self._skill_preset_9_btn.configure(state="disabled")
        if self._skill_preset_12_btn:
            self._skill_preset_12_btn.configure(state="disabled")
        
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
        if self._level_preset_80_btn:
            self._level_preset_80_btn.configure(state="normal")
        if self._level_preset_90_btn:
            self._level_preset_90_btn.configure(state="normal")
        if self._skill_preset_9_btn:
            self._skill_preset_9_btn.configure(state="normal")
        if self._skill_preset_12_btn:
            self._skill_preset_12_btn.configure(state="normal")
        
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

