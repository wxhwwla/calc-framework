#!/usr/bin/env python3
"""计算页五列与高级页 dock 骨架布局。"""

from __future__ import annotations

from tkinter import messagebox

import customtkinter as ctk

from gui_design.app.confirm_orchestrator import handle_confirm
from gui_design.layout.gui_layout import (
    APP_COLUMN_WEIGHTS,
    ATTR_COLUMN_MINSIZE,
    CHAR_ATTR_COLUMN,
    CHAR_COLUMN,
    CONTROL_DOCK_MINSIZE,
    CONTROL_DOCK_ROW,
    CONTROL_INNER_COL_ACTIONS_MINSIZE,
    CONTROL_INNER_COL_MULTI_WEIGHT,
    CONTROL_INNER_COL_SEARCH_WEIGHT,
    MAIN_CONTENT_ROW,
    PRIMARY_ACTION_BUTTON_HEIGHT,
    SECONDARY_ACTION_BUTTON_HEIGHT,
    SELECTION_COLUMN_MINSIZE,
    WEAPON_ATTR_COLUMN,
    WEAPON_COLUMN,
    ZONE_COLUMN,
    ZONE_COLUMN_MINSIZE,
)
from gui_design.panels.selection_panel import ChooseTypesStarsNamesLevels
from gui_design.shared.ui_preferences import resolve_startup_page
from utils.operation_log import LogLevel, get_session_operation_log


class AppMainLayoutMixin:
    def _setup_ui(self) -> None:
        """
        设置主界面布局（使用 grid 布局实现自适应缩放）

        布局结构见 ``gui_layout``：双页签；计算页使用 5 列，操作控件集中在高级页。
        """
        self.app.grid_rowconfigure(0, weight=1)
        self.app.grid_columnconfigure(0, weight=1)

        self.page_tabs = ctk.CTkTabview(self.app, corner_radius=20)
        self.page_tabs.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")
        self.page_tabs.add("计算页")
        self.page_tabs.add("高级页")
        self.main_page_frame = self.page_tabs.tab("计算页")
        self.advanced_page_frame = self.page_tabs.tab("高级页")
        self.page_tabs.set(resolve_startup_page(self._ui_preferences))

        assert self.main_page_frame is not None, "main_page_frame 未初始化"
        assert self.advanced_page_frame is not None, "advanced_page_frame 未初始化"
        self.main_page_frame.grid_rowconfigure(MAIN_CONTENT_ROW, weight=1, minsize=480)
        self.advanced_page_frame.grid_rowconfigure(CONTROL_DOCK_ROW, weight=1, minsize=CONTROL_DOCK_MINSIZE)

        for idx, weight in enumerate(APP_COLUMN_WEIGHTS):
            self.main_page_frame.grid_columnconfigure(idx, weight=weight)
        self.main_page_frame.grid_columnconfigure(CHAR_COLUMN, minsize=SELECTION_COLUMN_MINSIZE)
        self.main_page_frame.grid_columnconfigure(WEAPON_COLUMN, minsize=SELECTION_COLUMN_MINSIZE)
        self.main_page_frame.grid_columnconfigure(CHAR_ATTR_COLUMN, minsize=ATTR_COLUMN_MINSIZE)
        self.main_page_frame.grid_columnconfigure(WEAPON_ATTR_COLUMN, minsize=ATTR_COLUMN_MINSIZE)
        self.main_page_frame.grid_columnconfigure(ZONE_COLUMN, weight=0, minsize=ZONE_COLUMN_MINSIZE)
        self.advanced_page_frame.grid_columnconfigure(0, weight=1)

        # ==================== 角色选择区（左侧）====================
        self.char_frame = ctk.CTkFrame(
            self.main_page_frame,  # 父容器
            corner_radius=20,  # 圆角半径（美化）
        )
        # 将角色框架放置在第 0 行第 0 列
        self.char_frame.grid(
            row=MAIN_CONTENT_ROW,
            column=CHAR_COLUMN,
            padx=(8, 4),
            pady=8,
            sticky="nsew",
        )
        self.char_frame.grid_rowconfigure(0, weight=1)
        self.char_frame.grid_columnconfigure(0, weight=1)

        # ==================== 武器选择区（仅武器词条与等级）====================
        self.weapon_frame = ctk.CTkFrame(self.main_page_frame, corner_radius=20)
        self.weapon_frame.grid(
            row=MAIN_CONTENT_ROW,
            column=WEAPON_COLUMN,
            padx=4,
            pady=8,
            sticky="nsew",
        )
        self.weapon_frame.grid_rowconfigure(0, weight=1)
        self.weapon_frame.grid_columnconfigure(0, weight=1)

        # ==================== 角色属性展示区 ====================
        self.char_attr_frame = ctk.CTkFrame(self.main_page_frame, corner_radius=20)
        self.char_attr_frame.grid(row=MAIN_CONTENT_ROW, column=CHAR_ATTR_COLUMN, padx=4, pady=8, sticky="nsew")
        self.char_attr_frame.grid_rowconfigure(0, weight=1)
        self.char_attr_frame.grid_columnconfigure(0, weight=1)

        self.char_attr_scroll = ctk.CTkScrollableFrame(
            self.char_attr_frame, label_text="角色属性", label_font=self.big_font
        )
        self.char_attr_scroll.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        # ==================== 武器属性展示区 ====================
        self.weapon_attr_frame = ctk.CTkFrame(self.main_page_frame, corner_radius=20)
        self.weapon_attr_frame.grid(
            row=MAIN_CONTENT_ROW,
            column=WEAPON_ATTR_COLUMN,
            padx=4,
            pady=8,
            sticky="nsew",
        )
        self.weapon_attr_frame.grid_rowconfigure(0, weight=1)
        self.weapon_attr_frame.grid_columnconfigure(0, weight=1)

        self.weapon_attr_scroll = ctk.CTkScrollableFrame(
            self.weapon_attr_frame, label_text="武器属性", label_font=self.big_font
        )
        self.weapon_attr_scroll.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        # ==================== 右侧乘区展示区 ====================
        self.right_frame = ctk.CTkFrame(self.main_page_frame, corner_radius=20)
        self.right_frame.grid(
            row=MAIN_CONTENT_ROW,
            column=ZONE_COLUMN,
            padx=(4, 8),
            pady=8,
            sticky="nsew",
        )
        # 配置右侧框架内部布局
        self.right_frame.grid_rowconfigure(0, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)

        # 滚动框架（用于展示乘区数据）
        self.right_scroll = ctk.CTkScrollableFrame(
            self.right_frame,  # 父容器
            label_text="乘区数据",  # 滚动框架标题
            label_font=self.big_font,  # 标题字体
        )
        self.right_scroll.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        quick_actions = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        quick_actions.grid(row=1, column=0, padx=8, pady=(0, 6), sticky="ew")
        quick_actions.grid_columnconfigure(0, weight=1)
        quick_actions.grid_columnconfigure(1, weight=1)
        self.main_confirm_btn = ctk.CTkButton(
            quick_actions,
            text="确认选择",
            font=self.small_font,
            height=PRIMARY_ACTION_BUTTON_HEIGHT,
            command=lambda: handle_confirm(self, force=True),
        )
        self.main_confirm_btn.grid(row=0, column=0, padx=(0, 4), sticky="ew")
        self.goto_advanced_btn = ctk.CTkButton(
            quick_actions,
            text="前往高级页",
            font=self.small_font,
            height=SECONDARY_ACTION_BUTTON_HEIGHT,
            fg_color="transparent",
            border_width=1,
            command=self._show_advanced_page,
        )
        self.goto_advanced_btn.grid(row=0, column=1, padx=(4, 0), sticky="ew")

        # ==================== 高级页（全量搜索 / 多技能次数 / 工具）====================
        self.control_frame = ctk.CTkFrame(self.advanced_page_frame, corner_radius=20)
        self.control_frame.grid(
            row=CONTROL_DOCK_ROW,
            column=0,
            padx=8,
            pady=8,
            sticky="nsew",
        )
        self.control_frame.grid_rowconfigure(1, weight=1)
        self.control_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            self.control_frame,
            text="计算与搜索",
            font=self.big_font,
            text_color="#FF6B6B",
        ).grid(row=0, column=0, padx=10, pady=(8, 4), sticky="w")

        dock_body = ctk.CTkFrame(self.control_frame, fg_color="transparent")
        dock_body.grid(row=1, column=0, padx=6, pady=(0, 8), sticky="nsew")
        dock_body.grid_rowconfigure(0, weight=1)
        dock_body.grid_columnconfigure(0, weight=0, minsize=CONTROL_INNER_COL_ACTIONS_MINSIZE)
        dock_body.grid_columnconfigure(1, weight=CONTROL_INNER_COL_SEARCH_WEIGHT)
        dock_body.grid_columnconfigure(2, weight=CONTROL_INNER_COL_MULTI_WEIGHT)
        self._control_dock_body = dock_body

        self._control_col_actions = ctk.CTkFrame(dock_body, fg_color="transparent")
        self._control_col_actions.grid(row=0, column=0, padx=(4, 8), pady=4, sticky="new")
        self._control_col_search = ctk.CTkFrame(dock_body, fg_color="transparent")
        self._control_col_search.grid(row=0, column=1, padx=8, pady=4, sticky="new")
        self._control_col_multi = ctk.CTkFrame(dock_body, fg_color="transparent")
        self._control_col_multi.grid(row=0, column=2, padx=(8, 4), pady=4, sticky="nsew")
        self._control_col_multi.grid_rowconfigure(0, weight=1)
        self._control_col_multi.grid_columnconfigure(0, weight=1)
        self._build_control_panel()
        self._apply_control_dock_layout(self.app.winfo_width())
        self._apply_adaptive_button_texts(self.app.winfo_width())

        # 加载数据并创建选择面板
        self._load_data_and_create_panels()

    def _load_data_and_create_panels(self) -> None:
        """
        加载角色和武器数据并创建选择面板

        执行流程：
        1. 调用 get_characters() 获取角色数据列表
        2. 调用 get_weapons() 获取武器数据列表
        3. 创建角色选择面板实例
        4. 创建武器选择面板实例（放在武器框架的第一行）
        5. 设置角色选择变化时的回调
        """
        characters = self.game_data.characters
        weapons = self.game_data.weapons
        if self.game_data.load_error is not None:
            messagebox.showerror(
                "游戏数据加载失败",
                f"{self.game_data.load_error}\n\n请确认程序目录下角色/武器 JSON 文件完整且格式正确。",
                parent=self.app,
            )
        if self.game_data.equipment_load_error is not None:
            messagebox.showwarning(
                "装备数据加载失败",
                f"{self.game_data.equipment_load_error}\n\n全量遍历与装备预览可能不可用。",
                parent=self.app,
            )
        if not characters and not weapons:
            messagebox.showwarning(
                "游戏数据为空",
                "未加载到任何角色或武器条目，界面将无法选择配装。",
                parent=self.app,
            )

        self.all_weapons = list(weapons)

        # 创建角色选择面板（主计算页优先直观操作，默认不使用滚动容器）
        assert self.char_frame is not None, "char_frame 未初始化"
        char_select_body = ctk.CTkFrame(
            self.char_frame,
            fg_color="transparent",
        )
        char_select_body.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        char_select_body.grid_columnconfigure(0, weight=1)
        self.char_panel = ChooseTypesStarsNamesLevels.use(
            char_select_body,
            characters,
            self.big_font,
        )

        # 创建武器选择面板（放在武器框架的第一行）
        assert self.weapon_frame is not None, "weapon_frame 未初始化"

        # 武器选择与角色一致使用普通容器；高级操作已迁移到「高级页」
        weapon_select_body = ctk.CTkFrame(
            self.weapon_frame,
            fg_color="transparent",
        )
        weapon_select_body.grid(
            row=0,
            column=0,
            padx=5,
            pady=(5, 0),
            sticky="nsew",
        )
        weapon_select_body.grid_columnconfigure(0, weight=1)

        self.weapon_panel = ChooseTypesStarsNamesLevels.use(
            weapon_select_body,
            weapons,  # 武器数据列表
            self.big_font,  # 使用的字体
            is_weapon_panel=True,  # 是否为武器面板（启用特殊能力滑块）
        )
        self._apply_selection_panel_expand_preferences()

        # 设置角色选择变化时的回调
        self.char_panel.selected_name.trace_add("write", self._on_char_name_change)
        self._bind_live_refresh_traces()

        # 根据默认选中的角色初始化武器面板
        # 角色面板初始化时已经自动选择了第一个角色，现在需要同步更新武器面板
        self._on_char_name_change()
        self._refresh_fixed_loadout_menus()

        # 如果没有选中角色或没有可用武器，禁用武器面板
        char_data = self.char_panel.get_selected_data()
        if not char_data:
            self.weapon_panel.disable_panel()
        else:
            char_weapon_type = char_data.get("武器", "")
            filtered_weapons = [w for w in self.all_weapons if w.get("类型") == char_weapon_type]
            if not filtered_weapons:
                self.weapon_panel.disable_panel()

        # 先刷新布局再进入事件循环，避免长时间黑屏
        self.app.update_idletasks()
        get_session_operation_log().record(LogLevel.INFO, "app_ready", {})
        self.app.after_idle(self._startup_refresh)
