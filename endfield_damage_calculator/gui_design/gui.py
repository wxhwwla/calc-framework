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
- gui_design.display_model: GUI 展示层入口
- data.loader: 数据加载模块
"""

# 导入必要的模块
import customtkinter as ctk  # CustomTkinter GUI 库
from tkinter import filedialog, messagebox
from typing import Optional, List, Dict, Any   # 类型提示支持
from pathlib import Path
import threading
import hashlib
import os
from gui_design.display_model import (
    gui_settings,
    confirm_selection,
    ChooseTypesStarsNamesLevels,
)
from data.loader import fetch_game_data_for_gui  # 数据加载（含失败信息）
from data.loader import get_equipments, DataLoadError
from please_read_me import get_exe_version  # EXE版本号
from legal.attribution import open_attribution_dialog
from calculation.damage_engine import DamageContext
from calculation.loadout_optimizer import OptimizerConfig, WeaponCandidate
from calculation.mvp_pipeline import run_mvp_search_pipeline
from calculation.equipment_system import load_equipment_catalog_from_wiki_draft
from calculation.equipment_system import build_equipment_catalog_from_local_rows
from calculation.multiplicative_zones.final_attack_zone import calculate_final_attack_with_details

# 列 0/1/3/5：选择区与属性区（最小宽度）；列 7：右侧乘区（占满剩余宽度）
APP_COLUMN_WEIGHTS = (0, 0, 0, 0, 0, 0, 0, 1)


class DamageCalculatorApp:
    """
    终末地伤害计算小工具主应用类
    
    包含完整的 GUI 界面，提供角色和武器选择功能，支持窗口缩放自适应。
    
    界面布局（主窗口 8 列 grid，列 2/4/6 为间隙；选择列与属性列 weight=0，乘区列 weight=1）：
    ┌──────────────────────────────────────────────────────────────────────────┐
    │ 角色选择 │ 武器选择 │ 角色属性 │ 武器属性 │        右侧乘区（可伸缩）      │
    │ +确认按钮│ +滑块    │ 明细数值 │ 明细数值 │        乘区数据               │
    └──────────────────────────────────────────────────────────────────────────┘
    
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

        # 设置窗口初始大小（宽度x高度）
        self.app.geometry("1200x720")
        
        # 设置窗口标题（包含 EXE 版本号）
        self.app.title(f"终末地伤害计算小工具 v{get_exe_version()}")
        
        # 设置窗口最小尺寸（防止用户拖得太小）
        self.app.minsize(900, 600)
        
        # 绑定窗口大小变化事件，用于自适应缩放
        self.app.bind("<Configure>", self._on_window_resize)

        # 初始化字体配置
        self.big_font: ctk.CTkFont = ctk.CTkFont(
            family="微软雅黑",  # 字体名称
            size=14,           # 字体大小
            weight="bold"      # 字体粗细（粗体）
        )
        self.small_font: ctk.CTkFont = ctk.CTkFont(
            family="微软雅黑",  # 字体名称
            size=12            # 字体大小（常规）
        )

        # 初始化 UI 组件引用为 None（后续在 _setup_ui 中创建）
        self.char_frame: Optional[ctk.CTkFrame] = None
        self.weapon_frame: Optional[ctk.CTkFrame] = None
        self.confirm_btn: Optional[ctk.CTkButton] = None
        self.attribution_btn: Optional[ctk.CTkButton] = None
        self.mvp_search_btn: Optional[ctk.CTkButton] = None
        self.mvp_status_label: Optional[ctk.CTkLabel] = None
        self.calc_mode_var: ctk.StringVar = ctk.StringVar(value="single_hit")
        self.calc_mode_menu: Optional[ctk.CTkOptionMenu] = None
        self.use_manual_weights_var: ctk.BooleanVar = ctk.BooleanVar(value=False)
        self.single_skill_scope_var: ctk.StringVar = ctk.StringVar(value="当前武器")
        self.single_skill_scope_menu: Optional[ctk.CTkOptionMenu] = None
        self.single_skill_equipment_scope_var: ctk.StringVar = ctk.StringVar(value="全部装备")
        self.single_skill_equipment_scope_menu: Optional[ctk.CTkOptionMenu] = None
        self.skill_weight_1_var: ctk.StringVar = ctk.StringVar(value="1.0")
        self.skill_weight_2_var: ctk.StringVar = ctk.StringVar(value="0.0")
        self.skill_weight_3_var: ctk.StringVar = ctk.StringVar(value="0.0")
        self.skill_weight_1_slider: Optional[ctk.CTkSlider] = None
        self.skill_weight_2_slider: Optional[ctk.CTkSlider] = None
        self.skill_weight_3_slider: Optional[ctk.CTkSlider] = None
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
            - 主窗口分为 8 列，使用权重分配空间
            - 第0列：角色选择区
            - 第1列：武器选择区（含确认按钮）
            - 第3列：角色属性展示区
            - 第5列：武器属性展示区
            - 第7列：右侧乘区数据计算区
        
        实现步骤：
            1. 配置主窗口 grid 布局的行和列权重（见 APP_COLUMN_WEIGHTS）
            2. 创建角色选择框架并放置在第 0 列
            3. 创建武器选择框架并放置在第 1 列（包含确认按钮）
            4. 创建角色属性展示框架并放置在第 3 列
            5. 创建武器属性展示框架并放置在第 5 列
            6. 创建右侧乘区数据框架并放置在第 7 列
            7. 调用 _load_data_and_create_panels 加载数据并创建选择面板
        """
        # 配置主窗口 grid 布局的行权重（只有 1 行，权重为 1 表示占满垂直空间）
        self.app.grid_rowconfigure(0, weight=1)
        
        # 配置主窗口 grid 布局的列权重（按比例分配宽度）
        # 注：CTkFrame 有内置最小宽度限制，设置 weight=0 让组件仅占用最小尺寸
        for idx, weight in enumerate(APP_COLUMN_WEIGHTS):
            self.app.grid_columnconfigure(idx, weight=weight)

        # ==================== 角色选择区（左侧）====================
        self.char_frame = ctk.CTkFrame(
            self.app,           # 父容器
            corner_radius=20    # 圆角半径（美化）
        )
        # 将角色框架放置在第 0 行第 0 列
        self.char_frame.grid(
            row=0,              # 行号
            column=0,           # 列号
            padx=(10, 5),      # 水平内边距（左边10，右边5）
            pady=10,            # 垂直内边距
            sticky="nsew"       # 四边拉伸（north, south, east, west）
        )

        # ==================== 武器选择区（角色选择右侧）====================
        self.weapon_frame = ctk.CTkFrame(
            self.app,           # 父容器
            corner_radius=20    # 圆角半径（美化）
        )
        # 将武器框架放置在第 0 行第 1 列
        self.weapon_frame.grid(
            row=0,              # 行号
            column=1,           # 列号
            padx=5,             # 水平内边距
            pady=10,            # 垂直内边距
            sticky="nsew"       # 四边拉伸（north, south, east, west）
        )
        
        # 确认按钮（放在武器选择区下方）
        self.confirm_btn = ctk.CTkButton(
            self.weapon_frame,        # 父容器（放在武器框架内）
            text="确认选择",          # 按钮文本
            font=self.big_font,       # 使用大号字体
            command=self._on_confirm  # 点击事件处理函数
        )
        # 第 0 行仅放武器选择滚动区，避免与下方按钮/模式下拉重叠
        self.weapon_frame.grid_rowconfigure(0, weight=1, minsize=280)
        self.weapon_frame.grid_rowconfigure(1, weight=0)
        self.weapon_frame.grid_rowconfigure(2, weight=0)
        self.weapon_frame.grid_rowconfigure(3, weight=0)
        self.weapon_frame.grid_rowconfigure(4, weight=0)
        self.weapon_frame.grid_rowconfigure(5, weight=0)
        self.weapon_frame.grid_rowconfigure(6, weight=0)
        self.weapon_frame.grid_rowconfigure(7, weight=0)
        self.weapon_frame.grid_rowconfigure(8, weight=0)
        self.weapon_frame.grid_rowconfigure(9, weight=0)
        self.weapon_frame.grid_rowconfigure(10, weight=0)
        self.weapon_frame.grid_rowconfigure(11, weight=0)
        self.weapon_frame.grid_rowconfigure(12, weight=0)
        self.weapon_frame.grid_rowconfigure(13, weight=0)
        self.weapon_frame.grid_rowconfigure(14, weight=0)
        self.weapon_frame.grid_rowconfigure(15, weight=0)
        self.weapon_frame.grid_columnconfigure(0, weight=1)

        self.confirm_btn.grid(
            row=1,
            column=0,
            padx=10,
            pady=(10, 4),
            sticky="ew",
        )

        self.attribution_btn = ctk.CTkButton(
            self.weapon_frame,
            text="数据来源与许可",
            font=self.small_font,
            fg_color="transparent",
            border_width=1,
            command=self._on_attribution,
        )
        self.attribution_btn.grid(
            row=2,
            column=0,
            padx=10,
            pady=(4, 10),
            sticky="ew",
        )

        self.mvp_search_btn = ctk.CTkButton(
            self.weapon_frame,
            text="实验：MVP搜索并导出",
            font=self.small_font,
            command=self._on_run_mvp_search,
        )
        self.mvp_search_btn.grid(
            row=3,
            column=0,
            padx=10,
            pady=(0, 4),
            sticky="ew",
        )
        self.mvp_status_label = ctk.CTkLabel(
            self.weapon_frame,
            text="MVP搜索状态：未开始",
            font=self.small_font,
            text_color="#888888",
            justify="left",
        )
        self.mvp_status_label.grid(
            row=4,
            column=0,
            padx=10,
            pady=(0, 4),
            sticky="w",
        )
        mode_title = ctk.CTkLabel(
            self.weapon_frame,
            text="计算模式",
            font=self.small_font,
            text_color="#CCCCCC",
        )
        mode_title.grid(
            row=5,
            column=0,
            padx=10,
            pady=(0, 2),
            sticky="w",
        )
        self.calc_mode_menu = ctk.CTkOptionMenu(
            self.weapon_frame,
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
        self.calc_mode_menu.grid(
            row=6,
            column=0,
            padx=10,
            pady=(0, 4),
            sticky="ew",
        )
        scope_title = ctk.CTkLabel(
            self.weapon_frame,
            text="单技能候选范围",
            font=self.small_font,
            text_color="#CCCCCC",
        )
        scope_title.grid(
            row=7,
            column=0,
            padx=10,
            pady=(0, 2),
            sticky="w",
        )
        self.single_skill_scope_menu = ctk.CTkOptionMenu(
            self.weapon_frame,
            values=[
                "当前武器",
                "同类型同星级",
                "同类型全部",
            ],
            variable=self.single_skill_scope_var,
            font=self.small_font,
            command=lambda _v: self._on_confirm(),
        )
        self.single_skill_scope_menu.grid(
            row=8,
            column=0,
            padx=10,
            pady=(0, 4),
            sticky="ew",
        )
        equip_scope_title = ctk.CTkLabel(
            self.weapon_frame,
            text="单技能装备范围",
            font=self.small_font,
            text_color="#CCCCCC",
        )
        equip_scope_title.grid(
            row=9,
            column=0,
            padx=10,
            pady=(0, 2),
            sticky="w",
        )
        self.single_skill_equipment_scope_menu = ctk.CTkOptionMenu(
            self.weapon_frame,
            values=[
                "全部装备",
                "仅套装装备",
                "仅散件装备",
            ],
            variable=self.single_skill_equipment_scope_var,
            font=self.small_font,
            command=lambda _v: self._on_confirm(),
        )
        self.single_skill_equipment_scope_menu.grid(
            row=10,
            column=0,
            padx=10,
            pady=(0, 4),
            sticky="ew",
        )
        weight_switch = ctk.CTkSwitch(
            self.weapon_frame,
            text="多技能使用手动权重",
            variable=self.use_manual_weights_var,
            font=self.small_font,
            command=self._on_confirm,
        )
        weight_switch.grid(
            row=11,
            column=0,
            padx=10,
            pady=(0, 4),
            sticky="w",
        )
        self.skill_weight_1_slider = self._create_weight_row(
            row=12,
            label_text="战技权重",
            value_var=self.skill_weight_1_var,
            default_value=1.0,
        )
        self.skill_weight_2_slider = self._create_weight_row(
            row=13,
            label_text="连携技权重",
            value_var=self.skill_weight_2_var,
            default_value=0.0,
        )
        self.skill_weight_3_slider = self._create_weight_row(
            row=14,
            label_text="终结技权重",
            value_var=self.skill_weight_3_var,
            default_value=0.0,
        )
        weight_tip = ctk.CTkLabel(
            self.weapon_frame,
            text="提示：仅在“多技能遍历(快速预览)”模式生效",
            font=self.small_font,
            text_color="#888888",
        )
        weight_tip.grid(
            row=15,
            column=0,
            padx=10,
            pady=(0, 10),
            sticky="w",
        )

        # ==================== 角色属性展示区 ====================
        self.char_attr_frame = ctk.CTkFrame(
            self.app,
            corner_radius=20
        )
        self.char_attr_frame.grid(
            row=0,
            column=3,
            padx=5,
            pady=10,
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
            column=5,
            padx=5,
            pady=10,
            sticky="nsew"
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
            column=7,
            padx=(5, 10),  # 左边距5，右边距10
            pady=10,
            sticky="nsew"
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

        # 创建角色选择面板
        assert self.char_frame is not None, "char_frame 未初始化"
        self.char_panel = ChooseTypesStarsNamesLevels.use(
            self.char_frame,  # 父框架
            characters,       # 角色数据列表
            self.big_font     # 使用的字体
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

    def _build_weapon_candidates(
        self,
        *,
        char_data: Dict[str, Any],
        char_level: int,
        weapon_level: int,
        trust_level: int,
    ) -> list[WeaponCandidate]:
        """按当前角色与等级生成候选武器最终攻击力。"""
        weapon_type = char_data.get("武器", "")
        candidates: list[WeaponCandidate] = []
        for weapon in self.all_weapons:
            if weapon.get("类型") != weapon_type:
                continue
            details = calculate_final_attack_with_details(
                character=char_data,
                weapon=weapon,
                char_level=char_level,
                weapon_level=weapon_level,
                trust_level=trust_level,
            )
            candidates.append(
                WeaponCandidate(
                    name=str(weapon.get("名称", "")),
                    final_attack=float(details.get("final_attack", 0.0)),
                )
            )
        return candidates

    def _set_mvp_status(self, text: str) -> None:
        """更新 MVP 搜索状态文案。"""
        if self.mvp_status_label is not None:
            self.mvp_status_label.configure(text=text)

    def _on_run_mvp_search(self) -> None:
        """执行实验性 MVP 搜索并导出结果。"""
        assert self.char_panel is not None, "char_panel 未初始化"
        assert self.weapon_panel is not None, "weapon_panel 未初始化"
        char_data = self.char_panel.get_selected_data()
        if not char_data:
            messagebox.showwarning("MVP搜索", "请先选择有效角色。", parent=self.app)
            return

        output_dir = filedialog.askdirectory(parent=self.app, title="选择MVP搜索导出目录")
        if not output_dir:
            return

        pkg_root = Path(__file__).resolve().parent.parent
        draft_path = pkg_root.parent / "tools" / "bwiki_scout" / "output" / "parsed" / "equipment.json"
        try:
            local_equipments = get_equipments()
        except DataLoadError:
            local_equipments = []
        equipment_catalog = build_equipment_catalog_from_local_rows(local_equipments)
        if not equipment_catalog["chest"] or not equipment_catalog["gloves"] or not equipment_catalog["accessories"]:
            if not draft_path.is_file():
                messagebox.showwarning(
                    "MVP搜索",
                    "未找到本地装备数据（equipments.json）或装备草案（output/parsed/equipment.json）。\n"
                    "请先执行：python tools/bwiki_scout/parse_draft.py\n"
                    "再执行：python tools/bwiki_scout/sync_equipments.py --apply",
                    parent=self.app,
                )
                return
            equipment_catalog = load_equipment_catalog_from_wiki_draft(draft_path)
        if not equipment_catalog["chest"] or not equipment_catalog["gloves"] or not equipment_catalog["accessories"]:
            messagebox.showwarning(
                "MVP搜索",
                "装备草案未包含完整的护甲/护手/配件数据，无法搜索。",
                parent=self.app,
            )
            return

        char_level = self.char_panel.get_level()
        weapon_level = self.weapon_panel.get_level()
        trust_level = self.char_panel.get_trust_level()
        skill_name, skill_type, skill_multiplier = self._resolve_selected_skill(char_data)
        weapon_candidates = self._build_weapon_candidates(
            char_data=char_data,
            char_level=char_level,
            weapon_level=weapon_level,
            trust_level=trust_level,
        )
        if not weapon_candidates:
            messagebox.showwarning("MVP搜索", "当前角色对应武器候选为空。", parent=self.app)
            return

        signature_seed = (
            f"{char_data.get('名称','')}-lv{char_level}-wlv{weapon_level}-trust{trust_level}-"
            f"{skill_name}-w{len(weapon_candidates)}"
        )
        run_signature = hashlib.sha1(signature_seed.encode("utf-8")).hexdigest()[:16]
        export_root = Path(output_dir)
        db_path = export_root / "search_runs.db"
        export_dir = export_root / "mvp_exports"
        base_context = DamageContext(
            final_attack=0.0,
            skill_multiplier=skill_multiplier,
            skill_type=skill_type,
            enemy_defense=100.0,
        )
        config = OptimizerConfig(top_n=10, crit_mode="non_crit", allow_duplicate_accessory=True)

        if self.mvp_search_btn is not None:
            self.mvp_search_btn.configure(state="disabled")
        self._set_mvp_status("MVP搜索状态：计算中，请稍候...")

        def _worker() -> None:
            try:
                result = run_mvp_search_pipeline(
                    db_path=db_path,
                    export_dir=export_dir,
                    run_signature=run_signature,
                    base_context=base_context,
                    weapons=weapon_candidates,
                    equipment_catalog=equipment_catalog,
                    config=config,
                    max_workers=max(1, (os.cpu_count() or 1) - 1),
                )
            except Exception as exc:
                self.app.after(
                    0,
                    lambda: (
                        self._set_mvp_status("MVP搜索状态：失败"),
                        messagebox.showerror("MVP搜索失败", str(exc), parent=self.app),
                        self.mvp_search_btn.configure(state="normal") if self.mvp_search_btn else None,
                    ),
                )
                return

            def _finish() -> None:
                self._set_mvp_status(
                    f"MVP搜索状态：完成（{result['processed_combinations']}/{result['total_combinations']}）"
                )
                if self.mvp_search_btn is not None:
                    self.mvp_search_btn.configure(state="normal")
                messagebox.showinfo(
                    "MVP搜索完成",
                    "已完成搜索并导出结果：\n"
                    f"- 数据库：{db_path}\n"
                    f"- 导出目录：{export_dir}\n"
                    f"- 已处理组合：{result['processed_combinations']}/{result['total_combinations']}",
                    parent=self.app,
                )

            self.app.after(0, _finish)

        threading.Thread(target=_worker, daemon=True).start()

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
            multi_skill_manual_weights=self._manual_multi_skill_weights(),
            use_manual_multi_skill_weights=bool(self.use_manual_weights_var.get()),
            preview_weapon_candidates=self._single_skill_preview_candidates(),
            preview_scope_label=self.single_skill_scope_var.get(),
            preview_equipment_catalog=self._single_skill_preview_equipment_catalog(),
            preview_equipment_scope_label=self.single_skill_equipment_scope_var.get(),
        )

    def _create_weight_row(
        self,
        *,
        row: int,
        label_text: str,
        value_var: ctk.StringVar,
        default_value: float,
    ) -> ctk.CTkSlider:
        """创建单行权重滑块。"""
        title = ctk.CTkLabel(
            self.weapon_frame,
            text=f"{label_text}: {value_var.get()}",
            font=self.small_font,
            text_color="#CCCCCC",
        )
        title.grid(row=row, column=0, padx=10, pady=(0, 2), sticky="w")

        def _on_change(raw: float) -> None:
            value = round(float(raw), 1)
            value_var.set(f"{value:.1f}")
            title.configure(text=f"{label_text}: {value_var.get()}")
            if self._current_calculation_mode() == "multi_skill_search":
                self._on_confirm()

        slider = ctk.CTkSlider(
            self.weapon_frame,
            from_=0.0,
            to=5.0,
            number_of_steps=50,
            command=_on_change,
        )
        slider.grid(row=row, column=0, padx=(120, 10), pady=(0, 2), sticky="ew")
        slider.set(default_value)
        return slider

    def _manual_multi_skill_weights(self) -> Dict[str, float]:
        """读取 GUI 手动权重。"""
        def _to_float(text: str) -> float:
            try:
                return max(0.0, float(text))
            except (TypeError, ValueError):
                return 0.0

        return {
            "战技": _to_float(self.skill_weight_1_var.get()),
            "连携技": _to_float(self.skill_weight_2_var.get()),
            "终结技": _to_float(self.skill_weight_3_var.get()),
        }

    def _single_skill_preview_candidates(self) -> List[WeaponCandidate]:
        """按候选范围生成单技能预览武器集合。"""
        assert self.char_panel is not None, "char_panel 未初始化"
        assert self.weapon_panel is not None, "weapon_panel 未初始化"
        char_data = self.char_panel.get_selected_data()
        current_weapon = self.weapon_panel.get_selected_data()
        if not char_data or not current_weapon:
            return []

        scope = self.single_skill_scope_var.get()
        char_level = self.char_panel.get_level()
        weapon_level = self.weapon_panel.get_level()
        trust_level = self.char_panel.get_trust_level()
        weapon_type = str(char_data.get("武器", ""))
        current_star = current_weapon.get("星级")

        candidates: List[WeaponCandidate] = []
        for weapon in self.all_weapons:
            if weapon.get("类型") != weapon_type:
                continue
            if scope == "同类型同星级" and weapon.get("星级") != current_star:
                continue
            if scope == "当前武器" and weapon.get("名称") != current_weapon.get("名称"):
                continue
            details = calculate_final_attack_with_details(
                character=char_data,
                weapon=weapon,
                char_level=char_level,
                weapon_level=weapon_level,
                trust_level=trust_level,
            )
            candidates.append(
                WeaponCandidate(
                    name=str(weapon.get("名称", "")),
                    final_attack=float(details.get("final_attack", 0.0)),
                )
            )
        return candidates

    def _single_skill_preview_equipment_catalog(self) -> Dict[str, List[Dict[str, Any]]]:
        """按装备范围构建单技能预览装备目录。"""
        try:
            rows = get_equipments()
        except DataLoadError:
            return {"chest": [], "gloves": [], "accessories": []}
        scope = self.single_skill_equipment_scope_var.get()
        filtered: List[Dict[str, Any]] = []
        for row in rows:
            set_name = str(row.get("套装") or "").strip()
            if scope == "仅套装装备" and not set_name:
                continue
            if scope == "仅散件装备" and set_name:
                continue
            filtered.append(row)
        return build_equipment_catalog_from_local_rows(filtered)

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
