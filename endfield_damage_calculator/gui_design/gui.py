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
from tkinter import messagebox
from typing import Optional, List, Dict, Any   # 类型提示支持
from gui_design.display_model import (
    gui_settings,
    confirm_selection,
    ChooseTypesStarsNamesLevels,
)
from data.loader import fetch_game_data_for_gui  # 数据加载（含失败信息）
from please_read_me import get_exe_version  # EXE版本号
from legal.attribution import open_attribution_dialog

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
        self.weapon_frame.grid_rowconfigure(0, weight=1)
        self.weapon_frame.grid_rowconfigure(1, weight=0)
        self.weapon_frame.grid_rowconfigure(2, weight=0)
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
        
        # 创建武器子框架（放在武器框架的第一行）
        weapon_inner_frame = ctk.CTkFrame(
            self.weapon_frame,
            fg_color="transparent"
        )
        weapon_inner_frame.grid(
            row=0,
            column=0,
            padx=5,
            pady=5,
            sticky="nsew"
        )
        
        self.weapon_panel = ChooseTypesStarsNamesLevels.use(
            weapon_inner_frame,     # 父框架（武器框架内的子框架）
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
            self.small_font      # 小号字体
        )

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
