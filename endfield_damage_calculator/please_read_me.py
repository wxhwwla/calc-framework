#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
终末地伤害计算小工具 - 项目说明文档

项目简介：
    本工具是一个基于 CustomTkinter 开发的伤害计算辅助工具，用于游戏《明日方舟：终末地》。
    玩家可以通过选择角色和武器，查看属性面板和乘区数据，帮助优化配装和战斗策略。

功能特性：
    1. 角色选择：支持按类型、星级筛选角色
    2. 武器选择：支持按类型、星级筛选武器，包含特殊能力等级选择
    3. 属性展示：显示角色和武器的详细属性
    4. 乘区计算：实时计算能力乘区、能力值加成、攻击力等数据
"""

# ==================== 版本信息（只在此处修改） ====================
# _VERSION：项目与 pip 包版本（pyproject.toml 通过 dynamic 读取，勿在别处重复写死）
# _EXE_VERSION：窗口标题与 dist/*.exe 用户可见版本
_VERSION = "1.8.1"
_EXE_VERSION = "0.2.0-beta"
# ==============================================================

# ==================== 项目结构文档（自动生成） ====================
PROJECT_STRUCTURE = f"""
项目结构（Python 包目录 endfield_damage_calculator/）：
    ├── main.py                    # 项目入口，启动应用
    ├── pyproject.toml             # 包配置（版本读取 please_read_me._VERSION）
    ├── please_read_me.py          # 版本号与帮助文本（本文件）
    ├── build.py                   # 打包脚本
    ├── README.md                  # 开发与测试说明（首选文档）
    ├── scripts/                   # 命令行与维护脚本（反推 GUI、录入种子等）
    ├── tests/                     # pytest 单元测试（不含可交互 GUI）
    ├── gui_design/                # GUI 界面模块
    │   ├── gui.py                 # 主应用类，管理窗口和布局
    │   ├── gui_tools.py           # GUI 工具组件导出层
    │   ├── gui_settings.py        # GUI 设置初始化
    │   ├── selection_panel.py     # 选择面板类
    │   ├── selection_components.py # 选择面板组件
    │   └── property_display.py    # 属性展示函数
    ├── calculation/               # 计算逻辑模块
    │   ├── formula.py / inverse.py
    │   └── multiplicative_zones/  # 乘区链（能力、防御、攻击力等）
    │       ├── base_zone.py       # 乘区基类
    │       ├── attribute_zone.py  # 能力乘区
    │       ├── defense_zone.py     # 防御减伤区
    │       ├── ability_bonus_zone.py # 能力值加成区
    │       ├── final_attack_zone.py  # 最终攻击力区
    │       └── zone_manager.py    # 乘区管理器
    ├── data/                      # 统一数据加载层
    │   └── loader.py              # 角色和武器数据的统一加载与缓存
    ├── utils/                     # 工具函数模块
    │   └── path_utils.py          # 路径处理工具
    └── character_weapon_equipment/# 数据文件目录
        ├── character_data/        # 角色数据（JSON格式）
        └── weapon_data/           # 武器数据（JSON格式）
"""

USAGE_INFO = f"""
使用方法：
    1. 运行方式：
        python main.py

    2. 打包方式：
        pip install setuptools wheel pyinstaller
        python build.py

    3. 操作流程：
        - 在左侧选择角色类型和星级
        - 在左侧选择武器类型和星级
        - 调整等级和信赖等级（角色）
        - 调整特殊能力等级（武器）
        - 点击"确认选择"按钮查看属性和乘区数据

技术栈：
    - Python 3.10+
    - CustomTkinter 5.2.2+（GUI框架）
    - JSON（数据存储）
    - PyInstaller（打包工具）
"""

FORMULA_INFO = f"""
伤害计算公式：
    最终攻击力 = 中间攻击力 × (能力值加成 + 1)
    中间攻击力 = 攻击加成攻击力 + 附加攻击力+
    攻击加成攻击力 = 基础攻击力 × 攻击力+乘区
    能力值加成 = 主能力×0.005 + 副能力×0.002
"""

VERSION_INFO = f"""
版本信息：
    项目版本: v{_VERSION}
    EXE版本:  v{_EXE_VERSION}
"""


def get_version() -> str:
    """
    获取项目版本号

    返回：
        版本号字符串（如 "1.5.3"）
    """
    return _VERSION


def get_exe_version() -> str:
    """
    获取 EXE 版本号（用于打包发布）

    返回：
        EXE 版本号字符串（如 "1.0.0"）
    """
    return _EXE_VERSION


def get_full_intro() -> str:
    """获取完整的项目介绍文档"""
    return f"""
终末地伤害计算小工具 v{_VERSION}
{'=' * 50}
{PROJECT_STRUCTURE}
{USAGE_INFO}
{FORMULA_INFO}
{VERSION_INFO}
    """


def show_help() -> None:
    """
    显示项目帮助信息
    """
    print(f"""
============================================================
终末地伤害计算小工具 v{_VERSION}
============================================================
{PROJECT_STRUCTURE}
{USAGE_INFO}
{FORMULA_INFO}
{VERSION_INFO}
    """)

if __name__ == "__main__":
    show_help()


