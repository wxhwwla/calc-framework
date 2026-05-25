#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI 主应用模块

此模块包含 DamageCalculatorApp 类，是整个应用的 GUI 核心组件。
负责创建主窗口、布局管理、事件处理和数据展示。

主要功能：
1. 创建主窗口并设置初始属性
2. 使用「计算页 / 高级页」双页签：计算页承载 5 列主视图，高级页承载操作/全量搜索/多技能
3. 加载角色和武器数据
4. 处理用户交互事件（确认选择等）
5. 支持窗口缩放自适应

依赖模块：
- customtkinter: GUI 库
- gui_design.display_view / display_lines: 属性列与乘区展示
- data.loader: 数据加载模块
"""

# 导入必要的模块（Windows 上须先打 platform 补丁，否则 darkdetect→WMI 卡死）
from utils.platform_win32_patch import apply_platform_win32_patch

apply_platform_win32_patch()

import customtkinter as ctk  # CustomTkinter GUI 库
from tkinter import messagebox
from typing import Optional, List, Dict, Any   # 类型提示支持
import os
from gui_design.gui_settings import gui_settings
from gui_design.confirm_orchestrator import (
    handle_confirm,
    schedule_confirm,
    WINDOW_RESTORE_SETTLE_MS,
)
from gui_design.multi_skill_controls import (
    place_multi_skill_section,
    read_manual_physical_abnormal_counts,
    read_manual_spell_abnormal_counts,
    read_manual_multi_skill_counts,
    rebuild_multi_skill_segment_rows,
)
from gui_design.selection_panel import ChooseTypesStarsNamesLevels
from data.game_data_facade import GameDataFacade
from please_read_me import get_exe_version  # EXE版本号
from legal.attribution import open_attribution_dialog
from calculation.damage_engine import DamageContext
from calculation.loadout_optimizer import WeaponCandidate
from calculation.search_cancel import SearchCancelToken
from calculation.single_skill_search_job import build_weapon_candidates
from gui_design.fixed_loadout_controls import (
    refresh_all_fixed_slot_menus,
    resolve_fixed_loadout_selection,
)
from gui_design.calc_mode_labels import (
    CALC_MODE_LABELS,
    DEFAULT_CALC_MODE_LABEL,
    calculation_mode_from_label,
)
from gui_design.gui_layout import (
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
    SELECTION_COLUMN_MINSIZE,
    SECONDARY_ACTION_BUTTON_HEIGHT,
    search_action_button_texts,
    WEAPON_ATTR_COLUMN,
    WEAPON_COLUMN,
    ZONE_COLUMN,
    ZONE_COLUMN_MINSIZE,
    should_use_compact_control_dock,
    control_dock_layout_needs_update,
)
from gui_design.label_layout import bind_wrapped_label
from utils.gui_window import apply_startup_maximized
from utils.gui_fonts import default_ui_font
from gui_design.search_settings import build_worker_option_labels
from gui_design.enhancement_controls import place_enhancement_section
from gui_design.ui_preferences import (
    record_char_advanced_expanded,
    record_last_page,
    resolve_startup_page,
    save_ui_preferences,
    load_ui_preferences,
)
from utils.operation_log import LogLevel, get_session_operation_log
from gui_design.loadout_pending import mark_loadout_pending
from gui_design.search_controls import place_search_section, refresh_search_estimate

class DamageCalculatorApp:
    """
    终末地伤害计算小工具主应用类
    
    包含完整的 GUI 界面，提供角色和武器选择功能，支持窗口缩放自适应。
    
    界面布局（双页签，启动后默认最大化）：
    - 计算页：角色 | 武器 | 角色属性 | 武器属性 | 乘区数据
    - 高级页：操作与分享 | 全量搜索 | 多技能次数
    
    属性：
        app: CTk 主窗口对象
        big_font: 大号字体配置
        small_font: 小号字体配置
        char_frame: 角色选择区框架（第 0 列）
        weapon_frame: 武器选择区框架（第 1 列，含确认按钮）
        confirm_btn: 确认选择按钮
        char_attr_frame: 角色属性区外框（第 2 列）
        char_attr_scroll: 角色属性滚动容器
        weapon_attr_frame: 武器属性区外框（第 3 列）
        weapon_attr_scroll: 武器属性滚动容器
        right_frame: 右侧乘区框架（第 5 列）
        right_scroll: 右侧乘区滚动容器
        char_panel: 角色选择面板实例
        weapon_panel: 武器选择面板实例
        all_weapons: 所有武器数据（用于动态过滤）
    """

    def __init__(self) -> None:
        """
        初始化应用实例
        
        执行流程：
        1. 调用 gui_settings() 初始化 GUI 外观设置
        2. 创建 CTk 主窗口对象
        3. 设置窗口初始大小、标题和最小尺寸
        4. 绑定窗口大小变化事件
        5. 初始化字体配置
        6. 初始化 UI 组件引用（设为 None）
        7. 调用 _setup_ui() 创建界面
        """
        # 初始化 GUI 全局设置（主题、外观模式等）
        gui_settings()

        # 创建主窗口对象
        self.app: ctk.CTk = ctk.CTk()

        # 初始尺寸（启动后 apply_startup_maximized 会最大化）
        self.app.geometry("1280x720")

        # 设置窗口标题（包含 EXE 版本号）
        self.app.title(f"终末地伤害计算小工具 v{get_exe_version()}")

        # 最小尺寸：保证五列+底栏布局可读
        self.app.minsize(1024, 600)
        
        # 绑定窗口大小变化事件，用于自适应缩放
        self.app.bind("<Configure>", self._on_window_resize)
        # 最小化/恢复时 Map/Unmap 用于防抖，避免恢复瞬间重复重排
        self.app.bind("<Map>", self._on_window_map, add="+")
        self.app.bind("<Unmap>", self._on_window_unmap, add="+")

        # 与系统默认 UI 字体一致
        self.big_font: ctk.CTkFont = default_ui_font(size=14, weight="bold")
        self.small_font: ctk.CTkFont = default_ui_font(size=12)

        # 初始化 UI 组件引用为 None（后续在 _setup_ui 中创建）
        self.char_frame: Optional[ctk.CTkFrame] = None
        self.weapon_frame: Optional[ctk.CTkFrame] = None
        self.page_tabs: Optional[ctk.CTkTabview] = None
        self.main_page_frame: Optional[ctk.CTkFrame] = None
        self.advanced_page_frame: Optional[ctk.CTkFrame] = None
        self.control_frame: Optional[ctk.CTkFrame] = None
        self._control_dock_body: Optional[ctk.CTkFrame] = None
        self._control_col_actions: Optional[ctk.CTkFrame] = None
        self._control_col_search: Optional[ctk.CTkFrame] = None
        self._control_col_multi: Optional[ctk.CTkFrame] = None
        self.goto_advanced_btn: Optional[ctk.CTkButton] = None
        self.main_confirm_btn: Optional[ctk.CTkButton] = None
        self.back_to_main_btn: Optional[ctk.CTkButton] = None
        self.confirm_btn: Optional[ctk.CTkButton] = None
        self.attribution_btn: Optional[ctk.CTkButton] = None
        self.mvp_search_btn: Optional[ctk.CTkButton] = None
        self.full_search_btn: Optional[ctk.CTkButton] = None
        self.search_workers_var: ctk.StringVar = ctk.StringVar(
            value=build_worker_option_labels()[0]
        )
        self.search_top_n_var: ctk.StringVar = ctk.StringVar(value="10")
        self.search_workers_menu: Optional[ctk.CTkOptionMenu] = None
        self.search_workers_hint_label: Optional[ctk.CTkLabel] = None
        self.search_top_n_menu: Optional[ctk.CTkOptionMenu] = None
        self.search_cancel_btn: Optional[ctk.CTkButton] = None
        # --- 全量/MVP 搜索状态（后台线程写 outcome，UI 更新须经 app.after）---
        self._search_cancel_token: Optional[SearchCancelToken] = None
        self._search_estimated_total_seconds: float = 0.0
        self.search_estimate_label: Optional[ctk.CTkLabel] = None
        self.mvp_status_label: Optional[ctk.CTkLabel] = None
        self.calc_mode_var: ctk.StringVar = ctk.StringVar(value=DEFAULT_CALC_MODE_LABEL)
        self.calc_mode_menu: Optional[ctk.CTkOptionMenu] = None
        self.use_manual_skill_counts_var: ctk.BooleanVar = ctk.BooleanVar(value=False)
        self.damage_component_mode_var: ctk.StringVar = ctk.StringVar(value="技能+异常")
        self.use_expected_crit_var: ctk.BooleanVar = ctk.BooleanVar(value=False)
        self.include_conditional_equipment_crit_var: ctk.BooleanVar = ctk.BooleanVar(value=False)
        self.extra_crit_rate_percent_var: ctk.StringVar = ctk.StringVar(value="0")
        self.extra_crit_damage_percent_var: ctk.StringVar = ctk.StringVar(value="0")
        self.single_skill_scope_var: ctk.StringVar = ctk.StringVar(value="当前武器")
        self.single_skill_scope_menu: Optional[ctk.CTkOptionMenu] = None
        self.single_skill_equipment_scope_var: ctk.StringVar = ctk.StringVar(value="全部装备")
        self.single_skill_equipment_scope_menu: Optional[ctk.CTkOptionMenu] = None
        self._fixed_loadout_slots: Dict[str, Any] = {}
        self._fixed_loadout_frame: Optional[ctk.CTkFrame] = None
        self.skill_count_1_var: ctk.StringVar = ctk.StringVar(value="0")
        self.skill_count_2_var: ctk.StringVar = ctk.StringVar(value="0")
        self.skill_count_3_var: ctk.StringVar = ctk.StringVar(value="0")
        self._segment_count_vars: Dict[str, ctk.StringVar] = {}
        self._physical_abnormal_count_vars: Dict[str, ctk.StringVar] = {}
        self._spell_abnormal_count_vars: Dict[str, ctk.StringVar] = {}
        self._multi_skill_counts_body: Optional[ctk.CTkFrame] = None
        self.char_attr_frame: Optional[ctk.CTkFrame] = None
        self.char_attr_scroll: Optional[ctk.CTkScrollableFrame] = None
        self.weapon_attr_frame: Optional[ctk.CTkFrame] = None
        self.weapon_attr_scroll: Optional[ctk.CTkScrollableFrame] = None
        self.right_frame: Optional[ctk.CTkFrame] = None
        self.right_scroll: Optional[ctk.CTkScrollableFrame] = None
        self.char_panel: Optional[ChooseTypesStarsNamesLevels] = None
        self.weapon_panel: Optional[ChooseTypesStarsNamesLevels] = None
        self.game_data: GameDataFacade = GameDataFacade.create()
        self.all_weapons: List[Dict[str, Any]] = list(self.game_data.weapons)
        # 确认刷新：合并同帧多次调用；签名未变时跳过整页重绘
        self._confirm_refresh_signature: Optional[tuple] = None
        self._confirmed_display_signature: Optional[tuple] = None
        self._confirm_after_id: Optional[str] = None
        self._pending_ui_after_id: Optional[str] = None
        self._confirm_button_default_styles: dict[int, tuple] = {}
        self._skill_count_last_committed: Dict[str, str] = {}
        self._suppress_full_confirm_refresh: bool = False
        self._ui_preferences: Dict[str, Any] = load_ui_preferences()
        # 高级页布局缓存：宽度/紧凑模式未变时不重复 grid
        self._control_dock_last_width: Optional[int] = None
        self._control_dock_last_compact: Optional[bool] = None
        # 窗口恢复后短暂防抖，避免 Configure/confirm 在布局未稳时触发
        self._restore_settling: bool = False
        self._restore_after_id: Optional[str] = None
        self._window_has_been_mapped: bool = False
        # 创建并布局所有 UI 组件
        self._setup_ui()
        self.app.protocol("WM_DELETE_WINDOW", self._on_close)

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
            self.main_page_frame,           # 父容器
            corner_radius=20    # 圆角半径（美化）
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
        self.char_attr_frame = ctk.CTkFrame(
            self.main_page_frame,
            corner_radius=20
        )
        self.char_attr_frame.grid(
            row=MAIN_CONTENT_ROW,
            column=CHAR_ATTR_COLUMN,
            padx=4,
            pady=8,
            sticky="nsew"
        )
        self.char_attr_frame.grid_rowconfigure(0, weight=1)
        self.char_attr_frame.grid_columnconfigure(0, weight=1)

        self.char_attr_scroll = ctk.CTkScrollableFrame(
            self.char_attr_frame,
            label_text="角色属性",
            label_font=self.big_font
        )
        self.char_attr_scroll.grid(
            row=0,
            column=0,
            padx=5,
            pady=5,
            sticky="nsew"
        )

        # ==================== 武器属性展示区 ====================
        self.weapon_attr_frame = ctk.CTkFrame(
            self.main_page_frame,
            corner_radius=20
        )
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
            self.weapon_attr_frame,
            label_text="武器属性",
            label_font=self.big_font
        )
        self.weapon_attr_scroll.grid(
            row=0,
            column=0,
            padx=5,
            pady=5,
            sticky="nsew"
        )

        # ==================== 右侧乘区展示区 ====================
        self.right_frame = ctk.CTkFrame(
            self.main_page_frame,
            corner_radius=20
        )
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
            self.right_frame,        # 父容器
            label_text="乘区数据",    # 滚动框架标题
            label_font=self.big_font # 标题字体
        )
        self.right_scroll.grid(
            row=0,
            column=0,
            padx=5,
            pady=5,
            sticky="nsew"
        )

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
            weapons,               # 武器数据列表
            self.big_font,          # 使用的字体
            is_weapon_panel=True   # 是否为武器面板（启用特殊能力滑块）
        )
        self._apply_char_skill_levels_expanded_preference()

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

    def _bind_live_refresh_traces(self) -> None:
        """绑定输入 trace：换名即时确认刷新；数值/选项仅标记待确认。"""
        assert self.char_panel is not None, "char_panel 未初始化"
        assert self.weapon_panel is not None, "weapon_panel 未初始化"

        def _schedule_name_confirm(*_args: object) -> None:
            schedule_confirm(self)

        def _mark_pending(*_args: object) -> None:
            mark_loadout_pending(self)

        # 换角色/武器名：立刻刷新三列
        self.char_panel.selected_name.trace_add("write", _schedule_name_confirm)
        self.weapon_panel.selected_name.trace_add("write", _schedule_name_confirm)

        # 等级、信赖、技能、武器词条：仅待确认，不自动重算三列
        self.char_panel.selected_level.trace_add("write", _mark_pending)
        self.weapon_panel.selected_level.trace_add("write", _mark_pending)

        if self.char_panel.trust_panel is not None:
            self.char_panel.trust_panel.trust_level.trace_add("write", _mark_pending)
        if self.char_panel.skill_level_panel is not None:
            skill_panel = self.char_panel.skill_level_panel
            skill_panel.skill_1_level.trace_add("write", _mark_pending)
            skill_panel.skill_2_level.trace_add("write", _mark_pending)
            skill_panel.skill_3_level.trace_add("write", _mark_pending)

        if self.weapon_panel.special_ability_panel is not None:
            special_panel = self.weapon_panel.special_ability_panel
            special_panel.special_ability_1_level.trace_add("write", _mark_pending)
            special_panel.special_ability_2_level.trace_add("write", _mark_pending)
            special_panel.special_ability_3_level.trace_add("write", _mark_pending)
            special_panel.weapon_special_level.trace_add("write", _mark_pending)
            special_panel.weapon_special_2_level.trace_add("write", _mark_pending)

    def _startup_refresh(self) -> None:
        """首帧绘制后再做确认刷新与搜索预估（勿在 __init__ 中同步调用）。"""
        handle_confirm(self, force=True)
        self._refresh_search_estimate()

    def _apply_char_skill_levels_expanded_preference(self) -> None:
        """从 ui_preferences 恢复角色「技能等级」折叠展开态。"""
        if self.char_panel is None:
            return
        expanded = bool(self._ui_preferences.get("char_advanced_expanded", True))
        self.char_panel._show_advanced_params_var.set(expanded)
        self.char_panel._refresh_advanced_params_visibility()

    def _show_main_page(self) -> None:
        """切回计算页（保留当前输入状态）。"""
        self._set_current_page("计算页")

    def _show_advanced_page(self) -> None:
        """切到高级页（保留当前输入状态）。"""
        self._set_current_page("高级页")

    def _set_current_page(self, page: str) -> None:
        """设置当前页签，并同步更新内存中的 last_page。"""
        if self.page_tabs is None:
            return
        if page not in ("计算页", "高级页"):
            page = "计算页"
        self.page_tabs.set(page)
        self._ui_preferences = record_last_page(self._ui_preferences, page=page)

    def _on_close(self) -> None:
        """关闭窗口前持久化 UI 偏好。"""
        try:
            if self.page_tabs is not None:
                self._ui_preferences = record_last_page(
                    self._ui_preferences,
                    page=str(self.page_tabs.get()),
                )
            if self.char_panel is not None:
                self._ui_preferences = record_char_advanced_expanded(
                    self._ui_preferences,
                    expanded=bool(self.char_panel._show_advanced_params_var.get()),
                )
            save_ui_preferences(self._ui_preferences)
        finally:
            self.app.destroy()

    def _apply_control_dock_layout(self, window_width: int) -> None:
        """根据窗口宽度重排高级页三列，避免窄窗口下横向挤压。"""
        body = self._control_dock_body
        actions = self._control_col_actions
        search = self._control_col_search
        multi = self._control_col_multi
        if body is None or actions is None or search is None or multi is None:
            return

        compact = should_use_compact_control_dock(window_width)
        if compact:
            body.grid_columnconfigure(0, weight=1, minsize=260)
            body.grid_columnconfigure(1, weight=1, minsize=260)
            body.grid_columnconfigure(2, weight=0, minsize=0)
            actions.grid(row=0, column=0, columnspan=2, padx=(4, 4), pady=(4, 2), sticky="new")
            search.grid(row=1, column=0, padx=(4, 6), pady=(2, 4), sticky="new")
            multi.grid(row=1, column=1, padx=(6, 4), pady=(2, 4), sticky="nsew")
            return

        body.grid_columnconfigure(0, weight=0, minsize=CONTROL_INNER_COL_ACTIONS_MINSIZE)
        body.grid_columnconfigure(1, weight=CONTROL_INNER_COL_SEARCH_WEIGHT, minsize=0)
        body.grid_columnconfigure(2, weight=CONTROL_INNER_COL_MULTI_WEIGHT, minsize=0)
        actions.grid(row=0, column=0, columnspan=1, padx=(4, 8), pady=4, sticky="new")
        search.grid(row=0, column=1, padx=8, pady=4, sticky="new")
        multi.grid(row=0, column=2, padx=(8, 4), pady=4, sticky="nsew")

    def _apply_adaptive_button_texts(self, window_width: int) -> None:
        """按窗口宽度调整按钮文案长度，降低窄屏文本挤压。"""
        compact = should_use_compact_control_dock(window_width)
        full_text, mvp_text = search_action_button_texts(compact=compact)
        if self.full_search_btn is not None:
            self.full_search_btn.configure(text=full_text)
        if self.mvp_search_btn is not None:
            self.mvp_search_btn.configure(text=mvp_text)

    def _on_char_name_change(self, *args: str) -> None:
        """
        角色名称变化时的回调函数
        
        功能：
        1. 获取当前选中角色的武器类型
        2. 根据武器类型过滤可用武器列表
        3. 如果没有对应类型的武器，显示提示
        4. 更新武器面板的可用武器列表（保持选中的武器不变）
        5. 启用/禁用武器面板
        
        参数：
            *args: trace_add 回调参数（忽略）
        """
        assert self.char_panel is not None, "char_panel 未初始化"
        assert self.weapon_panel is not None, "weapon_panel 未初始化"
        
        # 获取当前选中的角色数据
        char_data = self.char_panel.get_selected_data()
        
        if not char_data:
            # 未选择角色，禁用武器面板
            self.weapon_panel.disable_panel()
            # 直接设置空数据，不调用 update_data_list 避免滑块问题
            self.weapon_panel.list_c_w = []
            self.weapon_panel.selected_name.set("")
            return
        
        # 获取角色的武器类型
        char_weapon_type = char_data.get("武器", "")
        
        if not char_weapon_type:
            # 角色没有指定武器类型
            self.weapon_panel.disable_panel()
            self.weapon_panel.list_c_w = []
            self.weapon_panel.selected_name.set("")
            return
        
        # 根据角色武器类型过滤武器列表
        filtered_weapons = [
            weapon for weapon in self.all_weapons
            if weapon.get("类型", "") == char_weapon_type
        ]
        
        if not filtered_weapons:
            # 没有对应类型的武器，显示提示
            self.weapon_panel.disable_panel()
            self.weapon_panel.list_c_w = [{
                "名称": f"暂未收录{char_weapon_type}类型武器",
                "类型": char_weapon_type,
                "星级": 0,
                "等级": []  # 空数组，避免显示等级滑块
            }]
            # 手动设置菜单值
            self.weapon_panel.type_menu.configure(values=[char_weapon_type])
            self.weapon_panel.selected_type.set(char_weapon_type)
            self.weapon_panel.star_menu.configure(values=["0"])
            self.weapon_panel.selected_star.set("0")
            self.weapon_panel.name_menu.configure(values=[f"暂未收录{char_weapon_type}类型武器"])
            self.weapon_panel.selected_name.set(f"暂未收录{char_weapon_type}类型武器")
            # 清空等级显示
            if self.weapon_panel.level_label:
                self.weapon_panel.level_label.configure(text="")
            self.weapon_panel.selected_level.set("")
        else:
            # 保存当前选中的武器名称
            current_weapon_name = self.weapon_panel.selected_name.get()
            
            # 有可用武器，先启用面板再更新列表
            self.weapon_panel.enable_panel()
            self.weapon_panel.update_data_list(filtered_weapons)
            
            # 尝试恢复之前选中的武器（如果它在新的武器列表中）
            if current_weapon_name:
                weapon_names = [w["名称"] for w in filtered_weapons]
                if current_weapon_name in weapon_names:
                    self.weapon_panel.selected_name.set(current_weapon_name)

        rebuild_multi_skill_segment_rows(self)

    def _on_attribution(self) -> None:
        """打开数据来源与许可说明窗口。"""
        open_attribution_dialog(
            self.app,
            font=self.big_font,
            small_font=self.small_font,
        )

    def _wrap_control_label(self, label: ctk.CTkLabel, container: ctk.CTkBaseClass) -> None:
        """底栏内长文案：以整个 control_frame 宽度为换行参考。"""
        bind_wrapped_label(label, container, viewport=self.control_frame, padding=12)

    def _build_control_panel(self) -> None:
        """底栏三列：操作/模式 | 全量搜索 | 多技能次数。"""
        assert (
            self._control_col_actions is not None
            and self._control_col_search is not None
            and self._control_col_multi is not None
        )
        actions = self._control_col_actions
        search = self._control_col_search
        multi = self._control_col_multi
        for col in (actions, search, multi):
            col.grid_columnconfigure(0, weight=1)

        def _section(parent: ctk.CTkFrame, title: str, row: int) -> int:
            ctk.CTkLabel(
                parent,
                text=title,
                font=self.big_font,
                text_color="#FF6B6B",
            ).grid(row=row, column=0, padx=4, pady=(6, 2), sticky="w")
            return row + 1

        def _place(parent: ctk.CTkFrame, row: int, widget, *, pady: tuple[int, int] = (0, 4)) -> int:
            widget.grid(row=row, column=0, padx=4, pady=pady, sticky="ew")
            return row + 1

        ar = 0
        ar = _section(actions, "操作", ar)
        self.back_to_main_btn = ctk.CTkButton(
            actions,
            text="返回计算页",
            font=self.small_font,
            height=SECONDARY_ACTION_BUTTON_HEIGHT,
            fg_color="transparent",
            border_width=1,
            command=self._show_main_page,
        )
        ar = _place(actions, ar, self.back_to_main_btn, pady=(0, 6))
        self.confirm_btn = ctk.CTkButton(
            actions,
            text="确认选择",
            font=self.big_font,
            height=PRIMARY_ACTION_BUTTON_HEIGHT,
            command=lambda: handle_confirm(self, force=True),
        )
        ar = _place(actions, ar, self.confirm_btn, pady=(0, 6))
        self.attribution_btn = ctk.CTkButton(
            actions,
            text="数据来源与许可",
            font=self.small_font,
            height=SECONDARY_ACTION_BUTTON_HEIGHT,
            fg_color="transparent",
            border_width=1,
            command=self._on_attribution,
        )
        ar = _place(actions, ar, self.attribution_btn, pady=(0, 8))
        ar = _section(actions, "乘区展示", ar)
        ar = _place(
            actions,
            ar,
            ctk.CTkLabel(actions, text="计算模式", font=self.small_font, text_color="#CCCCCC"),
            pady=(0, 2),
        )
        self.calc_mode_menu = ctk.CTkOptionMenu(
            actions,
            values=list(CALC_MODE_LABELS),
            variable=self.calc_mode_var,
            font=self.small_font,
            command=lambda _v: mark_loadout_pending(self),
        )
        ar = _place(actions, ar, self.calc_mode_menu, pady=(0, 4))
        ar = place_enhancement_section(
            self, actions, start_row=ar, place_fn=_place
        )

        place_search_section(
            self,
            search,
            wrap_label=self._wrap_control_label,
        )

        place_multi_skill_section(
            self,
            multi,
            wrap_label=self._wrap_control_label,
            schedule_confirm=lambda **_kw: mark_loadout_pending(self),
        )

    def _build_fixed_loadout_selection(self):
        """从底栏勾选状态解析固定/遍历配装。"""
        from calculation.loadout_slot_search import FixedLoadoutSelection

        if not self._fixed_loadout_slots:
            return FixedLoadoutSelection()
        catalog = self._single_skill_preview_equipment_catalog()
        return resolve_fixed_loadout_selection(catalog, self._fixed_loadout_slots)

    def _refresh_fixed_loadout_menus(self) -> None:
        """装备范围变化后刷新各部位套装/装备下拉。"""
        if not self._fixed_loadout_slots:
            return
        catalog = self._single_skill_preview_equipment_catalog()
        refresh_all_fixed_slot_menus(catalog, self._fixed_loadout_slots)

    def _refresh_search_estimate(self) -> None:
        """刷新「预计组合数/耗时」标签（委托 search_controls）。"""
        refresh_search_estimate(self)

    def _is_window_iconified(self) -> bool:
        """窗口是否处于最小化状态（最小化时跳过重绘，避免恢复后闪屏）。"""
        try:
            return str(self.app.state()) == "iconic"
        except Exception:
            return False

    def _apply_responsive_layout(self, window_width: int) -> None:
        """按窗口宽度更新高级页布局与按钮文案；未变化时跳过。"""
        width = int(window_width)
        if width <= 1:
            return
        if not control_dock_layout_needs_update(
            width,
            last_width=self._control_dock_last_width,
            last_compact=self._control_dock_last_compact,
        ):
            return
        compact = should_use_compact_control_dock(width)
        self._control_dock_last_width = width
        self._control_dock_last_compact = compact
        self._apply_control_dock_layout(width)
        self._apply_adaptive_button_texts(width)

    def _on_window_unmap(self, _event: object = None) -> None:
        """窗口被隐藏/最小化时取消待执行的恢复防抖。"""
        if self._restore_after_id is not None:
            try:
                self.app.after_cancel(self._restore_after_id)
            except Exception:
                pass
            self._restore_after_id = None

    def _on_window_map(self, _event: object = None) -> None:
        """窗口重新显示：首次映射立即布局，后续恢复走防抖。"""
        if self._is_window_iconified():
            return
        if not self._window_has_been_mapped:
            self._window_has_been_mapped = True
            self._apply_responsive_layout(int(self.app.winfo_width()))
            return
        self._begin_restore_settle()

    def _begin_restore_settle(self) -> None:
        """恢复显示后延迟一帧再重排，避免与 CTk remap 争抢导致黑屏。"""
        self._restore_settling = True
        if self._restore_after_id is not None:
            try:
                self.app.after_cancel(self._restore_after_id)
            except Exception:
                pass
        self._restore_after_id = self.app.after(
            WINDOW_RESTORE_SETTLE_MS,
            self._finish_restore_settle,
        )

    def _finish_restore_settle(self) -> None:
        """恢复防抖结束：若仍可见则补一次必要布局。"""
        self._restore_after_id = None
        self._restore_settling = False
        if self._is_window_iconified():
            return
        self._apply_responsive_layout(int(self.app.winfo_width()))

    def _on_window_resize(self, event) -> None:
        """
        窗口大小变化事件处理：仅根窗口、非最小化、非恢复防抖中且尺寸变化时重排。

        参数：
            event: Tkinter 事件对象（包含窗口大小等信息）
        """
        if getattr(event, "widget", None) is not self.app:
            return
        if self._is_window_iconified() or self._restore_settling:
            return
        width = getattr(event, "width", None)
        if width is None:
            width = self.app.winfo_width()
        self._apply_responsive_layout(int(width))

    def _manual_multi_skill_counts(self) -> Dict[str, int]:
        return read_manual_multi_skill_counts(self)

    def _manual_physical_abnormal_counts(self) -> Dict[str, int]:
        return read_manual_physical_abnormal_counts(self)

    def _manual_spell_abnormal_counts(self) -> Dict[str, int]:
        return read_manual_spell_abnormal_counts(self)

    def _current_damage_component_mode(self) -> str:
        """获取当前伤害组件模式。

        返回值：
        - "skill_only": 仅技能伤害
        - "abnormal_only": 仅异常伤害
        - "skill_and_abnormal": 技能+异常伤害（默认）

        Returns:
            伤害组件模式标识字符串
        """
        label = str(self.damage_component_mode_var.get()).strip()
        if label == "仅技能":
            return "skill_only"
        if label == "仅异常":
            return "abnormal_only"
        return "skill_and_abnormal"

    def _extra_crit_rate(self) -> float:
        """获取额外暴击率（已转换为小数）。

        从 UI 输入框读取额外暴击率百分比，转换为小数形式。
        若输入无效则返回 0.0。

        Returns:
            额外暴击率（0.0 到 1.0 之间）
        """
        try:
            return float(self.extra_crit_rate_percent_var.get()) / 100.0
        except (TypeError, ValueError):
            return 0.0

    def _extra_crit_damage(self) -> float:
        """获取额外暴击伤害（已转换为小数）。

        从 UI 输入框读取额外暴击伤害百分比，转换为小数形式。
        若输入无效则返回 0.0。

        Returns:
            额外暴击伤害（0.0 到 1.0 之间）
        """
        try:
            return float(self.extra_crit_damage_percent_var.get()) / 100.0
        except (TypeError, ValueError):
            return 0.0

    def _mark_loadout_pending(self) -> None:
        """配装数值/选项变更：不刷新三列，仅更新待确认按钮。"""
        mark_loadout_pending(self)

    def _schedule_confirm(self, *, force: bool = False) -> None:
        """调度确认刷新。

        委托给 schedule_confirm 函数，用于延迟执行伤害计算更新，
        避免频繁修改输入时重复计算。

        Args:
            force: 是否强制刷新（忽略签名缓存）
        """
        schedule_confirm(self, force=force)

    def _current_calculation_mode_label(self) -> str:
        """获取当前计算模式标签（显示用）。

        Returns:
            计算模式显示标签（如"非暴击"、"暴击"、"期望暴击"）
        """
        return str(self.calc_mode_var.get())

    def _single_skill_preview_candidates(self) -> List[WeaponCandidate]:
        """按候选范围生成单技能预览武器集合。

        根据当前选择的武器范围（当前武器/所有武器）生成候选武器列表，
        用于单技能预览和配装优化。

        Returns:
            武器候选对象列表，若角色或武器数据无效则返回空列表
        """
        assert self.char_panel is not None, "char_panel 未初始化"
        assert self.weapon_panel is not None, "weapon_panel 未初始化"
        char_data = self.char_panel.get_selected_data()
        current_weapon = self.weapon_panel.get_selected_data()
        if not char_data or not current_weapon:
            return []
        from gui_design.weapon_skill_selection import read_weapon_skill_selection_from_panel

        skill_view = read_weapon_skill_selection_from_panel(self.weapon_panel).to_preset_view()
        return build_weapon_candidates(
            all_weapons=self.all_weapons,
            char_data=char_data,
            current_weapon=current_weapon,
            weapon_scope_label=self.single_skill_scope_var.get(),
            char_level=self.char_panel.get_level(),
            weapon_level=self.weapon_panel.get_level(),
            trust_level=self.char_panel.get_trust_level(),
            weapon_normal_levels=skill_view["weapon_normal_levels"],
            weapon_special_states=skill_view["weapon_special_states"],
        )

    def _single_skill_preview_equipment_catalog(self) -> Dict[str, List[Dict[str, Any]]]:
        """按装备范围构建单技能预览装备目录。

        根据当前选择的装备范围（全部装备/仅已选套装）构建装备目录，
        用于固定配装选择和配装优化。

        Returns:
            装备目录字典，键为装备部位（护甲/护手/配件），值为装备列表
        """
        return self.game_data.equipment_catalog(
            self.single_skill_equipment_scope_var.get()
        )

    def _current_calculation_mode(self) -> str:
        """读取当前模式下拉框并转换为内部标识。

        将显示用的计算模式标签转换为内部使用的标识字符串。

        Returns:
            计算模式内部标识（如"non_crit"、"crit"、"expected"）
        """
        return calculation_mode_from_label(self.calc_mode_var.get())

    def run(self) -> None:
        """
        启动应用主循环
        
        调用 CTk 窗口的 mainloop() 方法，开始事件循环，显示窗口。
        此方法会阻塞直到窗口关闭。
        """
        apply_startup_maximized(self.app)
        self.app.mainloop()


def main() -> None:
    """
    备用入口函数（可直接运行此模块测试）
    
    功能：创建应用实例并启动
    """
    app = DamageCalculatorApp()
    app.run()


# 模块直接运行时的入口
if __name__ == "__main__":
    main()
