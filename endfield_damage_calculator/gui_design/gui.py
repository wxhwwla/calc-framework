#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI 主应用模块

此模块包含 DamageCalculatorApp 类，是整个应用的 GUI 核心组件。
负责创建主窗口、布局管理、事件处理和数据展示。

主要功能：
1. 创建主窗口并设置初始属性
2. 使用 grid 布局管理五个内容区（角色/武器选择、角色/武器属性、右侧乘区）
3. 加载角色和武器数据
4. 处理用户交互事件（确认选择等）
5. 支持窗口缩放自适应

依赖模块：
- customtkinter: GUI 库
- gui_design.property_display: 属性与乘区展示
- data.loader: 数据加载模块
"""

# 导入必要的模块
import customtkinter as ctk  # CustomTkinter GUI 库
from tkinter import filedialog, messagebox
from typing import Optional, List, Dict, Any   # 类型提示支持
from pathlib import Path
import threading
import os
from gui_design.gui_settings import gui_settings
from gui_design.property_display import confirm_selection
from gui_design.selection_panel import ChooseTypesStarsNamesLevels
from data.loader import fetch_game_data_for_gui  # 数据加载（含失败信息）
from data.equipment_catalog import catalog_full_search_error, get_equipment_catalog
from please_read_me import get_exe_version  # EXE版本号
from legal.attribution import open_attribution_dialog
from calculation.damage_engine import DamageContext
from calculation.loadout_optimizer import WeaponCandidate, optimizer_config_for_character
from calculation.mvp_pipeline import MvpSearchOutcome
from calculation.search_cancel import SearchCancelToken
from calculation.single_skill_search_job import (
    SingleSkillSearchJob,
    build_weapon_candidates,
    prepare_single_skill_search_job,
)
from calculation.single_skill_search_runner import (
    estimate_single_skill_search,
    run_exported_single_skill_search,
)
from gui_design.label_layout import (
    ATTR_COLUMN_MINSIZE,
    CONTROL_COLUMN_MINSIZE,
    SELECTION_COLUMN_MINSIZE,
    bind_wrapped_label,
)
from utils.gui_window import apply_startup_maximized
from utils.app_paths import allocate_search_run_directory, default_search_output_root
from utils.gui_fonts import default_ui_font
from gui_design.search_settings import (
    build_worker_option_labels,
    format_parallel_workers_help,
    format_search_progress_text,
    get_cpu_parallel_info,
    resolve_parallel_workers,
    resolve_top_n,
)
from gui_design.search_results_view import (
    build_search_results_report_lines,
    export_paths_to_strings,
    show_search_results_dialog,
)

# 列 0/1：配装（固定宽）；列 2：计算与搜索；列 3/4：属性（均分）；列 5：乘区（主伸缩）
APP_COLUMN_WEIGHTS = (0, 0, 1, 1, 1, 5)


class DamageCalculatorApp:
    """
    终末地伤害计算小工具主应用类
    
    包含完整的 GUI 界面，提供角色和武器选择功能，支持窗口缩放自适应。
    
    界面布局（6 列 grid，启动后默认最大化）：
    ┌──────────────────────────────────────────────────────────────────┐
    │ 角色选择 │ 武器选择 │ 计算与搜索 │ 角色属性 │ 武器属性 │ 乘区数据 │
    └──────────────────────────────────────────────────────────────────┘
    
    属性：
        app: CTk 主窗口对象
        big_font: 大号字体配置
        small_font: 小号字体配置
        char_frame: 角色选择区框架（第 0 列）
        weapon_frame: 武器选择区框架（第 1 列，含确认按钮）
        confirm_btn: 确认选择按钮
        char_attr_frame: 角色属性区外框（第 3 列）
        char_attr_scroll: 角色属性滚动容器
        weapon_attr_frame: 武器属性区外框（第 5 列）
        weapon_attr_scroll: 武器属性滚动容器
        right_frame: 右侧乘区框架（第 7 列）
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

        # 最小尺寸：保证六列布局可读
        self.app.minsize(1024, 600)
        
        # 绑定窗口大小变化事件，用于自适应缩放
        self.app.bind("<Configure>", self._on_window_resize)

        # 与系统默认 UI 字体一致
        self.big_font: ctk.CTkFont = default_ui_font(size=14, weight="bold")
        self.small_font: ctk.CTkFont = default_ui_font(size=12)

        # 初始化 UI 组件引用为 None（后续在 _setup_ui 中创建）
        self.char_frame: Optional[ctk.CTkFrame] = None
        self.weapon_frame: Optional[ctk.CTkFrame] = None
        self.control_frame: Optional[ctk.CTkFrame] = None
        self.control_scroll: Optional[ctk.CTkScrollableFrame] = None
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
        self._search_cancel_token: Optional[SearchCancelToken] = None
        self._search_estimated_total_seconds: float = 0.0
        self.search_estimate_label: Optional[ctk.CTkLabel] = None
        self.mvp_status_label: Optional[ctk.CTkLabel] = None
        self.calc_mode_var: ctk.StringVar = ctk.StringVar(value="single_hit")
        self.calc_mode_menu: Optional[ctk.CTkOptionMenu] = None
        self.use_manual_skill_counts_var: ctk.BooleanVar = ctk.BooleanVar(value=False)
        self.single_skill_scope_var: ctk.StringVar = ctk.StringVar(value="当前武器")
        self.single_skill_scope_menu: Optional[ctk.CTkOptionMenu] = None
        self.single_skill_equipment_scope_var: ctk.StringVar = ctk.StringVar(value="全部装备")
        self.single_skill_equipment_scope_menu: Optional[ctk.CTkOptionMenu] = None
        self.search_varying_slots_var: ctk.StringVar = ctk.StringVar(value="4")
        self.search_varying_slots_menu: Optional[ctk.CTkOptionMenu] = None
        self.skill_count_1_var: ctk.StringVar = ctk.StringVar(value="1")
        self.skill_count_2_var: ctk.StringVar = ctk.StringVar(value="0")
        self.skill_count_3_var: ctk.StringVar = ctk.StringVar(value="0")
        self.char_attr_frame: Optional[ctk.CTkFrame] = None
        self.char_attr_scroll: Optional[ctk.CTkScrollableFrame] = None
        self.weapon_attr_frame: Optional[ctk.CTkFrame] = None
        self.weapon_attr_scroll: Optional[ctk.CTkScrollableFrame] = None
        self.right_frame: Optional[ctk.CTkFrame] = None
        self.right_scroll: Optional[ctk.CTkScrollableFrame] = None
        self.char_panel: Optional[ChooseTypesStarsNamesLevels] = None
        self.weapon_panel: Optional[ChooseTypesStarsNamesLevels] = None
        self.all_weapons: List[Dict[str, Any]] = []  # 存储所有武器数据

        # 创建并布局所有 UI 组件
        self._setup_ui()

    def _setup_ui(self) -> None:
        """
        设置主界面布局（使用 grid 布局实现自适应缩放）
        
        布局结构：
            - 主窗口分为 6 列，使用权重分配空间
            - 第0列：角色选择区
            - 第1列：武器选择区
            - 第2列：计算与搜索
            - 第3列：角色属性展示区
            - 第4列：武器属性展示区
            - 第5列：右侧乘区数据计算区
        
        实现步骤：
            1. 配置主窗口 grid 布局的行和列权重（见 APP_COLUMN_WEIGHTS）
            2. 创建角色选择框架并放置在第 0 列
            3. 创建武器选择框架并放置在第 1 列（包含确认按钮）
            4. 创建角色属性展示框架并放置在第 3 列
            5. 创建武器属性展示框架并放置在第 4 列
            6. 创建右侧乘区数据框架并放置在第 5 列
            7. 调用 _load_data_and_create_panels 加载数据并创建选择面板
        """
        # 配置主窗口 grid 布局的行权重（只有 1 行，权重为 1 表示占满垂直空间）
        self.app.grid_rowconfigure(0, weight=1)
        
        # 配置主窗口 grid 布局的列权重（按比例分配宽度）
        # 注：CTkFrame 有内置最小宽度限制，设置 weight=0 让组件仅占用最小尺寸
        for idx, weight in enumerate(APP_COLUMN_WEIGHTS):
            self.app.grid_columnconfigure(idx, weight=weight)
        self.app.grid_columnconfigure(0, minsize=SELECTION_COLUMN_MINSIZE)
        self.app.grid_columnconfigure(1, minsize=SELECTION_COLUMN_MINSIZE)
        self.app.grid_columnconfigure(2, minsize=CONTROL_COLUMN_MINSIZE)
        self.app.grid_columnconfigure(3, minsize=ATTR_COLUMN_MINSIZE)
        self.app.grid_columnconfigure(4, minsize=ATTR_COLUMN_MINSIZE)

        # ==================== 角色选择区（左侧）====================
        self.char_frame = ctk.CTkFrame(
            self.app,           # 父容器
            corner_radius=20    # 圆角半径（美化）
        )
        # 将角色框架放置在第 0 行第 0 列
        self.char_frame.grid(
            row=0,
            column=0,
            padx=(8, 4),
            pady=8,
            sticky="nsew",
        )
        self.char_frame.grid_rowconfigure(0, weight=1)
        self.char_frame.grid_columnconfigure(0, weight=1)

        # ==================== 武器选择区（仅武器词条与等级）====================
        self.weapon_frame = ctk.CTkFrame(self.app, corner_radius=20)
        self.weapon_frame.grid(
            row=0,
            column=1,
            padx=4,
            pady=8,
            sticky="nsew",
        )
        self.weapon_frame.grid_rowconfigure(0, weight=1)
        self.weapon_frame.grid_columnconfigure(0, weight=1)

        # ==================== 计算与搜索（独立列，可滚动）====================
        self.control_frame = ctk.CTkFrame(self.app, corner_radius=20)
        self.control_frame.grid(
            row=0,
            column=2,
            padx=4,
            pady=8,
            sticky="nsew",
        )
        self.control_frame.grid_rowconfigure(0, weight=1)
        self.control_frame.grid_columnconfigure(0, weight=1)
        self.control_scroll = ctk.CTkScrollableFrame(
            self.control_frame,
            label_text="计算与搜索",
            label_font=self.big_font,
        )
        self.control_scroll.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.control_scroll.grid_columnconfigure(0, weight=1)
        self._build_control_panel()

        # ==================== 角色属性展示区 ====================
        self.char_attr_frame = ctk.CTkFrame(
            self.app,
            corner_radius=20
        )
        self.char_attr_frame.grid(
            row=0,
            column=3,
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
            self.app,
            corner_radius=20
        )
        self.weapon_attr_frame.grid(
            row=0,
            column=4,
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
            self.app,
            corner_radius=20
        )
        self.right_frame.grid(
            row=0,
            column=5,
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
        characters, weapons, load_error = fetch_game_data_for_gui()
        if load_error is not None:
            messagebox.showerror(
                "游戏数据加载失败",
                f"{load_error}\n\n请确认程序目录下角色/武器 JSON 文件完整且格式正确。",
                parent=self.app,
            )
        if not characters and not weapons:
            messagebox.showwarning(
                "游戏数据为空",
                "未加载到任何角色或武器条目，界面将无法选择配装。",
                parent=self.app,
            )
        
        # 保存所有武器数据
        self.all_weapons = weapons

        # 创建角色选择面板（可滚动，避免与操作区争用高度）
        assert self.char_frame is not None, "char_frame 未初始化"
        char_select_scroll = ctk.CTkScrollableFrame(
            self.char_frame,
            fg_color="transparent",
            label_text="角色选择",
            label_font=self.small_font,
        )
        char_select_scroll.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        char_select_scroll.grid_columnconfigure(0, weight=1)
        self.char_panel = ChooseTypesStarsNamesLevels.use(
            char_select_scroll,
            characters,
            self.big_font,
        )

        # 创建武器选择面板（放在武器框架的第一行）
        assert self.weapon_frame is not None, "weapon_frame 未初始化"
        
        # 武器选择放入可滚动区域，防止词条滑块被下方「确认/模式」控件遮挡
        weapon_select_scroll = ctk.CTkScrollableFrame(
            self.weapon_frame,
            fg_color="transparent",
            label_text="武器选择",
            label_font=self.small_font,
        )
        weapon_select_scroll.grid(
            row=0,
            column=0,
            padx=5,
            pady=(5, 0),
            sticky="nsew",
        )
        weapon_select_scroll.grid_columnconfigure(0, weight=1)

        self.weapon_panel = ChooseTypesStarsNamesLevels.use(
            weapon_select_scroll,
            weapons,               # 武器数据列表
            self.big_font,          # 使用的字体
            is_weapon_panel=True   # 是否为武器面板（启用特殊能力滑块）
        )
        
        # 设置角色选择变化时的回调
        self.char_panel.selected_name.trace_add("write", self._on_char_name_change)
        
        # 根据默认选中的角色初始化武器面板
        # 角色面板初始化时已经自动选择了第一个角色，现在需要同步更新武器面板
        self._on_char_name_change()
        self._refresh_search_estimate()
        
        # 如果没有选中角色或没有可用武器，禁用武器面板
        char_data = self.char_panel.get_selected_data()
        if not char_data:
            self.weapon_panel.disable_panel()
        else:
            char_weapon_type = char_data.get("武器", "")
            filtered_weapons = [w for w in self.all_weapons if w.get("类型") == char_weapon_type]
            if not filtered_weapons:
                self.weapon_panel.disable_panel()

        # 启动后自动确认一次，填充默认角色/武器属性展示
        self._on_confirm()

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

    def _on_attribution(self) -> None:
        """打开数据来源与许可说明窗口。"""
        open_attribution_dialog(
            self.app,
            font=self.big_font,
            small_font=self.small_font,
        )

    def _resolve_selected_skill(self, char_data: Dict[str, Any]) -> tuple[str, str, float]:
        """根据当前滑块选择解析技能类型与倍率。"""
        assert self.char_panel is not None, "char_panel 未初始化"
        options = (
            ("战技", "战技倍率", self.char_panel.get_skill_1_level()),
            ("连携技", "连携技倍率", self.char_panel.get_skill_2_level()),
            ("终结技", "终结技倍率", self.char_panel.get_skill_3_level()),
        )
        for skill_name, field, level in options:
            if level <= 0:
                continue
            segments = char_data.get(field) or []
            if not isinstance(segments, list) or not segments:
                continue
            first_segment = segments[0] if isinstance(segments[0], list) else []
            index = max(0, min(level - 1, len(first_segment) - 1))
            if isinstance(first_segment, list) and first_segment:
                value = float(first_segment[index] or 0.0)
                return skill_name, skill_name, value / 100.0
        return "战技", "战技", 1.0

    def _build_control_panel(self) -> None:
        """构建「计算与搜索」列：确认、模式、遍历、多技能权重。"""
        assert self.control_scroll is not None
        panel = self.control_scroll
        panel.grid_columnconfigure(0, weight=1, minsize=120)
        panel.grid_columnconfigure(1, weight=0, minsize=80)
        row = 0

        def place(widget, *, pady: tuple[int, int] = (0, 4), sticky: str = "ew") -> None:
            nonlocal row
            widget.grid(row=row, column=0, columnspan=2, padx=8, pady=pady, sticky=sticky)
            row += 1

        def section(title: str) -> None:
            place(
                ctk.CTkLabel(
                    panel,
                    text=title,
                    font=self.big_font,
                    text_color="#FF6B6B",
                ),
                pady=(10, 2),
                sticky="w",
            )

        section("操作")
        self.confirm_btn = ctk.CTkButton(
            panel,
            text="确认选择",
            font=self.big_font,
            command=self._on_confirm,
        )
        place(self.confirm_btn, pady=(0, 6))
        self.attribution_btn = ctk.CTkButton(
            panel,
            text="数据来源与许可",
            font=self.small_font,
            fg_color="transparent",
            border_width=1,
            command=self._on_attribution,
        )
        place(self.attribution_btn, pady=(0, 10))

        section("乘区展示")
        place(
            ctk.CTkLabel(panel, text="计算模式", font=self.small_font, text_color="#CCCCCC"),
            pady=(0, 2),
            sticky="w",
        )
        self.calc_mode_menu = ctk.CTkOptionMenu(
            panel,
            values=[
                "单段伤害计算",
                "乘区快照",
                "单技能遍历(快速预览)",
                "多技能遍历(快速预览)",
            ],
            variable=self.calc_mode_var,
            font=self.small_font,
            command=lambda _v: self._on_confirm(),
        )
        place(self.calc_mode_menu, pady=(0, 8))

        section("单技能全量遍历")
        place(
            ctk.CTkLabel(panel, text="武器候选范围", font=self.small_font, text_color="#CCCCCC"),
            pady=(0, 2),
            sticky="w",
        )
        self.single_skill_scope_menu = ctk.CTkOptionMenu(
            panel,
            values=["当前武器", "同类型同星级", "同类型全部"],
            variable=self.single_skill_scope_var,
            font=self.small_font,
            command=lambda _v: self._on_confirm(),
        )
        place(self.single_skill_scope_menu)
        place(
            ctk.CTkLabel(panel, text="装备范围", font=self.small_font, text_color="#CCCCCC"),
            pady=(0, 2),
            sticky="w",
        )
        self.single_skill_equipment_scope_menu = ctk.CTkOptionMenu(
            panel,
            values=["全部装备", "仅套装装备", "仅散件装备"],
            variable=self.single_skill_equipment_scope_var,
            font=self.small_font,
            command=lambda _v: self._on_confirm(),
        )
        place(self.single_skill_equipment_scope_menu)
        place(
            ctk.CTkLabel(
                panel,
                text="遍历装备件数",
                font=self.small_font,
                text_color="#CCCCCC",
            ),
            pady=(0, 2),
            sticky="w",
        )
        self.search_varying_slots_menu = ctk.CTkOptionMenu(
            panel,
            values=["1", "2", "3", "4"],
            variable=self.search_varying_slots_var,
            font=self.small_font,
        )
        place(self.search_varying_slots_menu)
        varying_slots_hint = ctk.CTkLabel(
            panel,
            text="1=仅护甲，2=+护手，3=+配件A，4=四格全套；未遍历格固定为各部首件",
            font=self.small_font,
            text_color="#888888",
            justify="left",
            anchor="w",
        )
        place(varying_slots_hint, pady=(0, 8), sticky="ew")
        bind_wrapped_label(varying_slots_hint, panel)

        def _on_search_scope_change(_value: str = "") -> None:
            self._refresh_search_estimate()
            self._on_confirm()

        self.single_skill_scope_menu.configure(command=_on_search_scope_change)
        self.single_skill_equipment_scope_menu.configure(command=_on_search_scope_change)
        if self.search_varying_slots_menu is not None:
            self.search_varying_slots_menu.configure(command=_on_search_scope_change)

        self.search_estimate_label = ctk.CTkLabel(
            panel,
            text="预计组合数：—",
            font=self.small_font,
            text_color="#AAAAAA",
            justify="left",
            anchor="w",
        )
        place(self.search_estimate_label, pady=(0, 8), sticky="ew")
        bind_wrapped_label(self.search_estimate_label, panel)

        self.full_search_btn = ctk.CTkButton(
            panel,
            text="全量遍历(弹窗结果)",
            font=self.small_font,
            command=self._on_run_full_search,
        )
        place(self.full_search_btn, pady=(4, 4))
        self.mvp_search_btn = ctk.CTkButton(
            panel,
            text="实验：MVP搜索并导出",
            font=self.small_font,
            command=self._on_run_mvp_search,
        )
        place(self.mvp_search_btn)

        search_param_row = ctk.CTkFrame(panel, fg_color="transparent")
        search_param_row.grid(row=row, column=0, columnspan=2, padx=8, pady=(0, 4), sticky="ew")
        search_param_row.grid_columnconfigure(0, weight=1)
        search_param_row.grid_columnconfigure(1, weight=1)
        row += 1
        ctk.CTkLabel(
            search_param_row, text="并行线程", font=self.small_font, text_color="#CCCCCC"
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            search_param_row, text="Top 条数", font=self.small_font, text_color="#CCCCCC"
        ).grid(row=0, column=1, sticky="w")
        self.search_workers_menu = ctk.CTkOptionMenu(
            search_param_row,
            values=build_worker_option_labels(),
            variable=self.search_workers_var,
            font=self.small_font,
        )
        self.search_workers_menu.grid(row=1, column=0, padx=(0, 4), pady=(0, 2), sticky="ew")
        self.search_workers_menu.configure(
            command=lambda _v: (self._refresh_parallel_workers_hint(), self._refresh_search_estimate())
        )
        self.search_workers_hint_label = ctk.CTkLabel(
            panel,
            text="",
            font=self.small_font,
            text_color="#777777",
            justify="left",
            anchor="w",
        )
        place(self.search_workers_hint_label, pady=(0, 6), sticky="ew")
        bind_wrapped_label(self.search_workers_hint_label, panel)
        self._refresh_parallel_workers_hint()
        self.search_top_n_menu = ctk.CTkOptionMenu(
            search_param_row,
            values=["3", "5", "10", "20", "50"],
            variable=self.search_top_n_var,
            font=self.small_font,
        )
        self.search_top_n_menu.grid(row=1, column=1, padx=(4, 0), pady=(0, 2), sticky="ew")

        self.search_cancel_btn = ctk.CTkButton(
            panel,
            text="取消搜索",
            font=self.small_font,
            state="disabled",
            fg_color="#8B3A3A",
            hover_color="#A04848",
            command=self._on_cancel_search,
        )
        place(self.search_cancel_btn)
        self.mvp_status_label = ctk.CTkLabel(
            panel,
            text="搜索状态：未开始",
            font=self.small_font,
            text_color="#888888",
            justify="left",
            anchor="w",
        )
        place(self.mvp_status_label, pady=(0, 10), sticky="ew")
        bind_wrapped_label(self.mvp_status_label, panel)

        section("多技能次数")
        count_switch = ctk.CTkSwitch(
            panel,
            text="使用手动次数",
            variable=self.use_manual_skill_counts_var,
            font=self.small_font,
            command=self._on_confirm,
        )
        place(count_switch, sticky="w")
        self._create_skill_count_row(row=row, label_text="战技次数", value_var=self.skill_count_1_var)
        row += 1
        self._create_skill_count_row(row=row, label_text="连携技次数", value_var=self.skill_count_2_var)
        row += 1
        self._create_skill_count_row(row=row, label_text="终结技次数", value_var=self.skill_count_3_var)
        row += 1
        multi_skill_hint = ctk.CTkLabel(
            panel,
            text="提示：次数仅在「多技能遍历(快速预览)」生效；技能倍率取左侧等级",
            font=self.small_font,
            text_color="#888888",
            justify="left",
            anchor="w",
        )
        place(multi_skill_hint, pady=(0, 12), sticky="ew")
        bind_wrapped_label(multi_skill_hint, panel)

    def _set_mvp_status(self, text: str) -> None:
        """更新 MVP 搜索状态文案。"""
        if self.mvp_status_label is not None:
            self.mvp_status_label.configure(text=text)

    def _prepare_single_skill_search_job(
        self,
    ) -> Optional[SingleSkillSearchJob]:
        """收集全量单技能搜索所需上下文；失败时弹窗并返回 None。"""
        assert self.char_panel is not None, "char_panel 未初始化"
        assert self.weapon_panel is not None, "weapon_panel 未初始化"
        char_data = self.char_panel.get_selected_data()
        if not char_data:
            messagebox.showwarning("全量遍历", "请先选择有效角色。", parent=self.app)
            return None

        char_level = self.char_panel.get_level()
        weapon_level = self.weapon_panel.get_level()
        trust_level = self.char_panel.get_trust_level()
        skill_name, skill_type, skill_multiplier = self._resolve_selected_skill(char_data)
        current_weapon = self.weapon_panel.get_selected_data()
        if not current_weapon:
            messagebox.showwarning("全量遍历", "请先选择有效武器。", parent=self.app)
            return None

        equipment_catalog = self._single_skill_preview_equipment_catalog()
        job, err = prepare_single_skill_search_job(
            char_data=char_data,
            char_level=char_level,
            weapon_level=weapon_level,
            trust_level=trust_level,
            skill_name=skill_name,
            skill_type=skill_type,
            skill_multiplier=skill_multiplier,
            weapon_scope_label=self.single_skill_scope_var.get(),
            equipment_scope_label=self.single_skill_equipment_scope_var.get(),
            all_weapons=self.all_weapons,
            current_weapon=current_weapon,
            equipment_catalog=equipment_catalog,
            varying_equipment_slot_count=self._search_varying_slot_count(),
        )
        if err:
            messagebox.showwarning("全量遍历", err, parent=self.app)
            return None
        return job

    def _search_varying_slot_count(self) -> int:
        """读取 GUI「遍历装备件数」（1–4）。"""
        try:
            return max(1, min(4, int(self.search_varying_slots_var.get())))
        except (TypeError, ValueError):
            return 4

    def _set_search_buttons_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        if self.mvp_search_btn is not None:
            self.mvp_search_btn.configure(state=state)
        if self.full_search_btn is not None:
            self.full_search_btn.configure(state=state)
        if self.search_workers_menu is not None:
            self.search_workers_menu.configure(state=state)
        if self.search_top_n_menu is not None:
            self.search_top_n_menu.configure(state=state)
        if self.search_cancel_btn is not None:
            self.search_cancel_btn.configure(state="normal" if not enabled else "disabled")

    def _compute_search_estimate_text(self, job: SingleSkillSearchJob) -> str:
        """根据当前 job 计算预估文案（不弹窗）。"""
        estimate = estimate_single_skill_search(
            job,
            max_workers=resolve_parallel_workers(self.search_workers_var.get()),
            top_n=resolve_top_n(self.search_top_n_var.get()),
        )
        self._search_estimated_total_seconds = estimate.estimated_seconds
        return estimate.text

    def _refresh_parallel_workers_hint(self) -> None:
        """刷新并行线程与本机 CPU 的对应说明。"""
        if self.search_workers_hint_label is None:
            return
        info = get_cpu_parallel_info()
        workers = resolve_parallel_workers(self.search_workers_var.get())
        self.search_workers_hint_label.configure(
            text=format_parallel_workers_help(info, selected_workers=workers)
        )

    def _refresh_search_estimate(self) -> None:
        """刷新「预计组合数/耗时」标签。"""
        if self.search_estimate_label is None:
            return
        assert self.char_panel is not None
        assert self.weapon_panel is not None
        if not self.char_panel.get_selected_data() or not self.weapon_panel.get_selected_data():
            self.search_estimate_label.configure(text="预计组合数：请先选择角色和武器")
            return
        catalog = self._single_skill_preview_equipment_catalog()
        catalog_err = catalog_full_search_error(catalog)
        if catalog_err:
            self.search_estimate_label.configure(
                text=f"预计组合数：{catalog_err.split('。')[0]}"
            )
            return
        weapons = self._single_skill_preview_candidates()
        if not weapons:
            self.search_estimate_label.configure(text="预计组合数：当前武器候选为空")
            return
        char_data = self.char_panel.get_selected_data()
        skill_name, skill_type, skill_multiplier = self._resolve_selected_skill(char_data)
        preview_job, err = prepare_single_skill_search_job(
            char_data=char_data,
            char_level=self.char_panel.get_level(),
            weapon_level=self.weapon_panel.get_level(),
            trust_level=self.char_panel.get_trust_level(),
            skill_name=skill_name,
            skill_type=skill_type,
            skill_multiplier=skill_multiplier,
            weapon_scope_label=self.single_skill_scope_var.get(),
            equipment_scope_label=self.single_skill_equipment_scope_var.get(),
            all_weapons=self.all_weapons,
            current_weapon=self.weapon_panel.get_selected_data(),
            equipment_catalog=catalog,
            varying_equipment_slot_count=self._search_varying_slot_count(),
        )
        if err or preview_job is None:
            self.search_estimate_label.configure(text=f"预计组合数：{err or '无法预估'}")
            return
        estimate = estimate_single_skill_search(
            preview_job,
            max_workers=resolve_parallel_workers(self.search_workers_var.get()),
            top_n=resolve_top_n(self.search_top_n_var.get()),
        )
        self._search_estimated_total_seconds = estimate.estimated_seconds
        self.search_estimate_label.configure(text=estimate.text)

    def _on_cancel_search(self) -> None:
        """请求取消正在运行的全量/MVP 搜索。"""
        if self._search_cancel_token is not None:
            self._search_cancel_token.cancel()
            self._set_mvp_status("搜索状态：正在取消…")

    def _show_search_result_popup(
        self,
        *,
        mode_label: str,
        job: SingleSkillSearchJob,
        outcome: MvpSearchOutcome,
        export_paths: Optional[Dict[str, str]] = None,
    ) -> None:
        """在独立大窗口展示 Top 配装与导出路径。"""
        lines = build_search_results_report_lines(
            mode_label=mode_label,
            skill_label=str(job.skill_label),
            scope_labels=(str(job.weapon_scope), str(job.equipment_scope)),
            processed_combinations=int(outcome.processed_combinations),
            total_combinations=int(outcome.total_combinations),
            top_results=outcome.top_results,
            export_paths=export_paths,
            cancelled=bool(outcome.cancelled),
        )
        show_search_results_dialog(self.app, title=mode_label, lines=lines)

    def _start_search_worker(
        self,
        *,
        mode_label: str,
        export_root: Path,
        job: SingleSkillSearchJob,
        status_running: str,
        status_done_prefix: str,
    ) -> None:
        """后台执行 MVP 搜索流水线，完成后弹窗展示结果。"""
        top_n = resolve_top_n(self.search_top_n_var.get())
        max_workers = resolve_parallel_workers(self.search_workers_var.get())
        skill_type = str(job.base_context.skill_type or job.skill_label)
        config = optimizer_config_for_character(
            job.char_data,
            priority_skill_types=(skill_type,),
            varying_slot_count=job.varying_equipment_slot_count,
            top_n=top_n,
            crit_mode="non_crit",
            allow_duplicate_accessory=True,
            prune_non_beneficial=True,
            warn_on_unfiltered=False,
        )
        self._search_cancel_token = SearchCancelToken()
        progress_prefix = status_done_prefix

        estimate_text = self._compute_search_estimate_text(job)

        def _progress_callback(info: dict) -> None:
            text = format_search_progress_text(
                prefix=progress_prefix,
                processed=int(info.get("processed", 0)),
                total=int(info.get("total", 0)),
                eta_seconds=float(info.get("eta_seconds", 0.0)),
                estimated_total_seconds=self._search_estimated_total_seconds,
            )

            def _update_status() -> None:
                self._set_mvp_status(text)

            self.app.after(0, _update_status)

        self._set_search_buttons_enabled(False)
        if self.search_estimate_label is not None:
            self.search_estimate_label.configure(text=estimate_text)
        self._set_mvp_status(
            f"{status_running}\n导出目录：{export_root}\n\n{estimate_text}"
        )

        def _worker() -> None:
            try:
                outcome = run_exported_single_skill_search(
                    job,
                    export_root=export_root,
                    config=config,
                    max_workers=max_workers,
                    cancel_token=self._search_cancel_token,
                    progress_callback=_progress_callback,
                )
            except Exception as exc:
                # except 块结束后 exc 会被清除，须在嵌套函数默认参数里绑定
                def _report_failure(error: BaseException = exc) -> None:
                    self._search_cancel_token = None
                    detail = str(error)
                    self._set_mvp_status(f"{status_done_prefix}：失败\n{detail}")
                    messagebox.showerror(mode_label, detail, parent=self.app)
                    self._set_search_buttons_enabled(True)

                self.app.after(0, _report_failure)
                return

            export_paths = export_paths_to_strings(outcome.exports or {})
            export_paths["数据库"] = str(outcome.db_path)
            export_paths["导出目录"] = str(outcome.export_dir)

            def _finish() -> None:
                self._search_cancel_token = None
                suffix = "（已取消）" if outcome.cancelled else "：完成"
                self._set_mvp_status(
                    f"{status_done_prefix}{suffix}（{outcome.processed_combinations}/"
                    f"{outcome.total_combinations}）"
                )
                self._set_search_buttons_enabled(True)
                self._show_search_result_popup(
                    mode_label=mode_label,
                    job=job,
                    outcome=outcome,
                    export_paths=export_paths,
                )

            self.app.after(0, _finish)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_run_full_search(self) -> None:
        """全量遍历：使用当前候选/装备范围，结果在弹窗中展示（不要求先选导出目录）。"""
        job = self._prepare_single_skill_search_job()
        if not job:
            return
        estimate_text = self._compute_search_estimate_text(job)
        if self._search_estimated_total_seconds >= 120:
            if not messagebox.askyesno(
                "确认全量遍历",
                f"{estimate_text}\n\n组合较多，是否仍要开始？",
                parent=self.app,
            ):
                return
        export_root = allocate_search_run_directory(purpose="full_search")
        self._start_search_worker(
            mode_label="单技能全量遍历",
            export_root=export_root,
            job=job,
            status_running="全量遍历：计算中，请稍候…",
            status_done_prefix="全量遍历",
        )

    def _on_run_mvp_search(self) -> None:
        """执行 MVP 搜索、导出，并在弹窗中展示 Top 结果。"""
        job = self._prepare_single_skill_search_job()
        if not job:
            return

        output_dir = filedialog.askdirectory(
            parent=self.app,
            title="选择MVP搜索导出目录",
            initialdir=str(default_search_output_root()),
        )
        if not output_dir:
            export_root = allocate_search_run_directory(purpose="mvp_search")
        else:
            export_root = Path(output_dir)

        self._start_search_worker(
            mode_label="MVP搜索并导出",
            export_root=export_root,
            job=job,
            status_running="MVP搜索状态：计算中，请稍候...",
            status_done_prefix="MVP搜索状态",
        )

    def _on_confirm(self) -> None:
        """
        确认按钮点击事件处理函数
        
        功能：调用 confirm_selection()，根据当前选中的角色和武器
        刷新角色属性列、武器属性列；两侧数据均有效时再刷新右侧乘区。
        
        前置条件：确保所有必要组件已初始化
        """
        # 断言检查组件是否已初始化
        assert self.char_attr_scroll is not None, "char_attr_scroll 未初始化"
        assert self.weapon_attr_scroll is not None, "weapon_attr_scroll 未初始化"
        assert self.right_scroll is not None, "right_scroll 未初始化"
        assert self.char_panel is not None, "char_panel 未初始化"
        assert self.weapon_panel is not None, "weapon_panel 未初始化"
        
        # 调用确认选择函数，更新属性列与乘区显示
        confirm_selection(
            self.char_attr_scroll,   # 角色属性展示区域
            self.weapon_attr_scroll, # 武器属性展示区域
            self.right_scroll,       # 右侧显示区域（乘区数据）
            self.char_panel,     # 角色选择面板
            self.weapon_panel,   # 武器选择面板
            self.big_font,       # 大号字体
            self.small_font,     # 小号字体
            calculation_mode=self._current_calculation_mode(),
            multi_skill_manual_counts=self._manual_multi_skill_counts(),
            use_manual_multi_skill_counts=bool(self.use_manual_skill_counts_var.get()),
            preview_weapon_candidates=self._single_skill_preview_candidates(),
            preview_scope_label=self.single_skill_scope_var.get(),
            preview_equipment_catalog=self._single_skill_preview_equipment_catalog(),
            preview_equipment_scope_label=self.single_skill_equipment_scope_var.get(),
        )
        self._refresh_search_estimate()

    def _create_skill_count_row(
        self,
        *,
        row: int,
        label_text: str,
        value_var: ctk.StringVar,
    ) -> None:
        """创建单行技能次数输入（标签 + 数字框两列）。"""
        parent = self.control_scroll
        assert parent is not None
        ctk.CTkLabel(
            parent,
            text=label_text,
            font=self.small_font,
            text_color="#CCCCCC",
        ).grid(row=row, column=0, padx=8, pady=(0, 2), sticky="w")

        def _on_change(*_args: object) -> None:
            text = (value_var.get() or "").strip()
            try:
                value = max(0, int(float(text)))
            except (TypeError, ValueError):
                value = 0
            value_var.set(str(value))
            if self._current_calculation_mode() == "multi_skill_search":
                self._on_confirm()

        entry = ctk.CTkEntry(
            parent,
            textvariable=value_var,
            width=72,
            font=self.small_font,
        )
        entry.grid(row=row, column=1, padx=(4, 8), pady=(0, 2), sticky="e")
        entry.bind("<FocusOut>", _on_change)
        entry.bind("<Return>", _on_change)

    def _manual_multi_skill_counts(self) -> Dict[str, int]:
        """读取 GUI 手动技能次数。"""

        def _to_int(text: str) -> int:
            try:
                return max(0, int(float(text)))
            except (TypeError, ValueError):
                return 0

        return {
            "战技": _to_int(self.skill_count_1_var.get()),
            "连携技": _to_int(self.skill_count_2_var.get()),
            "终结技": _to_int(self.skill_count_3_var.get()),
        }

    def _single_skill_preview_candidates(self) -> List[WeaponCandidate]:
        """按候选范围生成单技能预览武器集合。"""
        assert self.char_panel is not None, "char_panel 未初始化"
        assert self.weapon_panel is not None, "weapon_panel 未初始化"
        char_data = self.char_panel.get_selected_data()
        current_weapon = self.weapon_panel.get_selected_data()
        if not char_data or not current_weapon:
            return []
        return build_weapon_candidates(
            all_weapons=self.all_weapons,
            char_data=char_data,
            current_weapon=current_weapon,
            weapon_scope_label=self.single_skill_scope_var.get(),
            char_level=self.char_panel.get_level(),
            weapon_level=self.weapon_panel.get_level(),
            trust_level=self.char_panel.get_trust_level(),
        )

    def _single_skill_preview_equipment_catalog(self) -> Dict[str, List[Dict[str, Any]]]:
        """按装备范围构建单技能预览装备目录。"""
        return get_equipment_catalog(scope_label=self.single_skill_equipment_scope_var.get())

    def _current_calculation_mode(self) -> str:
        """读取当前模式下拉框并转换为内部标识。"""
        mode_text = self.calc_mode_var.get()
        if mode_text == "单段伤害计算":
            return "single_hit"
        if mode_text == "乘区快照":
            return "zone_snapshot"
        if mode_text.startswith("单技能遍历"):
            return "single_skill_search"
        if mode_text.startswith("多技能遍历"):
            return "multi_skill_search"
        return "single_hit"

    def _on_window_resize(self, event) -> None:
        """
        窗口大小变化事件处理函数
        
        参数：
            event: Tkinter 事件对象（包含窗口大小等信息）
        
        当前功能：预留接口，可用于动态调整字体大小等高级功能
        """
        # 可以在这里添加额外的缩放逻辑
        # 例如根据窗口大小动态调整字体大小
        # 当前预留，暂不实现具体功能
        pass

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
