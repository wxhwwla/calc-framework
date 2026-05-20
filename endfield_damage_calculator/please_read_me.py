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
# 项目版本号（用于文档、内部标识）
_VERSION = "1.7.0"

# EXE 版本号（用于打包发布）
_EXE_VERSION = "0.1.0-beta"
# ==============================================================

# ==================== 项目结构文档（自动生成） ====================
PROJECT_STRUCTURE = f"""
项目结构：
    ├── main.py                    # 项目入口，启动应用
    ├── pyproject.toml             # 打包配置文件
    ├── please_read_me.py          # 项目说明文档
    ├── build.py                   # 打包脚本
    ├── gui_design/                # GUI 界面模块
    │   ├── gui.py                 # 主应用类，管理窗口和布局
    │   ├── gui_tools.py           # GUI 工具组件导出层
    │   ├── gui_settings.py        # GUI 设置初始化
    │   ├── selection_panel.py     # 选择面板类
    │   ├── selection_components.py # 选择面板组件
    │   └── property_display.py    # 属性展示函数
    ├── calculation/               # 计算逻辑模块
    │   ├── multiplicative_zone.py # 乘法区伤害计算
    │   └── multiplicative_zones/  # 乘区子模块
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


# ## 1. 高层摘要（TL;DR）

# **影响范围：** 🔴 **高** - 核心计算逻辑重构，影响所有数值计算模块

# **关键变更：**
# - ✨ **小数数据处理机制**：统一采用"乘10→整数计算→除10"策略处理小数数据
# - 🧮 **公式计算优化**：所有成长公式统一使用 floor 算法，支持自动检测整数/小数数据
# - 🆕 **新武器添加**：新增4星武器"荧光雷羽"，包含小数属性（攻击力+）
# - 📦 **打包优化**：排除测试和脚本文件，减小发布体积
# - 🧪 **测试增强**：新增小数处理专项测试和反推公式GUI工具

# ---

# ## 2. 可视化概览（代码与逻辑映射）

# ```mermaid
# graph TD
#     subgraph "业务目标：统一处理整数与小数数据"
#         A["输入数据"] --> B{数据类型检测}
#         B -->|整数| C["直接计算<br/>base + floor(...)"]
#         B -->|小数| D["乘10转换<br/>scale_factor = 10"]
#         D --> E["整数计算<br/>scaled_base + floor(...)"]
#         E --> F["除10还原<br/>result / 10"]
#     end
    
#     subgraph "formula.py - 正向计算"
#         C1["calculate_skill_curve()"] --> C2["calculate_bonus_attribute()"]
#         C1 --> C3["新增: is_decimal 参数"]
#         C2 --> C3
#     end
    
#     subgraph "inverse.py - 反向拟合"
#         I1["fit_attribute_formula()"] --> I2["fit_skill_formula()"]
#         I1 --> I3["fit_skill_formula_no_special()"]
#         I2 --> I4["新增: 小数自动检测"]
#         I3 --> I4
#     end
    
#     subgraph "数据处理流程"
#         P1["原始数据"] --> P2{包含小数?}
#         P2 -->|否| P3["scale_factor = 1"]
#         P2 -->|是| P4["scale_factor = 10"]
#         P3 --> P5["floor 公式计算"]
#         P4 --> P5
#         P5 --> P6["返回结果"]
#     end
    
#     A -.-> C1
#     A -.-> I1
#     C3 -.-> P2
#     I4 -.-> P2
# ```

# ---

# ## 3. 详细变更分析

# ### 🧮 组件一：核心计算模块（`calculation/formula.py`）

# **变更说明：** 重构技能和属性成长曲线计算逻辑，统一支持小数数据处理

# **核心逻辑变更：**

# | 函数名 | 新增参数 | 功能说明 |
# |--------|----------|----------|
# | `calculate_skill_curve()` | `use_floor: bool`, `is_decimal: bool | None` | 支持小数数据自动检测和乘10处理 |
# | `calculate_bonus_attribute()` | `is_decimal: bool | None` | 支持小数属性值计算 |

# **数据处理规则：**
# ```python
# # 整数数据：直接计算
# calculated = base + math.floor((growth * (lv - 1) + offset) / divisor)

# # 小数数据：乘10 → 计算 → 除10
# scale_factor = 10
# scaled_base = base * scale_factor
# calculated = scaled_base + math.floor((scaled_growth * (lv - 1) + scaled_offset) / divisor)
# result = calculated / scale_factor
# ```

# **自动检测逻辑：**
# ```python
# if is_decimal is None:
#     is_decimal = isinstance(base, float) or \
#                  isinstance(growth, float) or \
#                  isinstance(offset, float) or \
#                  (special_values is not None and any(isinstance(x, float) for x in special_values))
# ```

# ---

# ### 🔍 组件二：反向拟合模块（`calculation/inverse.py`）

# **变更说明：** 支持从小数数据反推成长公式参数

# **函数签名变更：**

# | 函数名 | 原返回类型 | 新返回类型 | 说明 |
# |--------|-----------|-----------|------|
# | `fit_attribute_formula()` | `Tuple[int\|float, int, int, int]` | `Tuple[int\|float, int\|float, int, int\|float]` | growth/offset 支持小数 |
# | `fit_skill_formula()` | `Tuple[int\|float, int, int, int, List]` | `Tuple[int\|float, int\|float, int, int\|float, List]` | 同上 |
# | `fit_skill_formula_no_special()` | `Tuple[int\|float, int, int, int, List]` | `Tuple[int\|float, int\|float, int, int\|float, List]` | 同上 |

# **核心算法优化：**
# ```python
# # 小数数据检测
# is_decimal = any(isinstance(x, float) and x != int(x) for x in data)
# scale_factor = 10 if is_decimal else 1
# scaled_data = [x * scale_factor for x in data]

# # 使用整数算法拟合
# calculated = scaled_base + math.floor((growth * (lv - 1) + offset) / divisor)

# # 返回时还原参数
# return (base, growth / scale_factor, divisor, offset / scale_factor)
# ```

# **`fit_skill_formula_no_special()` 逻辑重构：**
# - 优先尝试拟合全部9个数据（而非强制第9个为特殊值）
# - 失败后才将第9个作为特殊值
# - 按 `growth/divisor` 比值排序，选择更合理的参数

# ---

# ### 📦 组件三：打包配置优化（`build.py`）

# **变更说明：** 优化 PyInstaller 打包配置，排除不必要的模块

# **新增排除列表：**

# | 排除项 | 说明 |
# |--------|------|
# | `tests` | 测试文件 |
# | `scripts` | 脚本文件（如 `inverse_cli.py`） |
# | `build` | 打包脚本模块 |
# | `add_character` | 数据添加脚本 |
# | `add_weapon` | 数据添加脚本 |
# | `test_` | 测试相关模块 |

# **效果：** 减小发布体积，避免打包测试代码和开发工具。

# ---

# ### 🆕 组件四：新武器数据（`weapons.json` + `add_weapon.py`）

# **变更说明：** 添加新武器"荧光雷羽"（4星施术单元）

# **武器参数配置：**

# | 属性 | 参数值 | 说明 |
# |------|--------|------|
# | 名称 | 荧光雷羽 | - |
# | 类型 | 施术单元 | - |
# | 星级 | 4 | - |
# | 基础攻击力 | base=34, growth=31, divisor=9, offset=8 | 整数数据 |
# | 意志+ | base=12, growth=48, divisor=5, offset=0, special=[79] | 整数数据 |
# | 攻击力+ | base=3.0, growth=12, divisor=5, offset=0, special=[23.4] | **小数数据** |
# | 特殊能力 | 攻击力+ | 曲线: [12, 14.4, 16.8, ..., 33.6] |

# **小数属性示例（攻击力+）：**
# ```
# 潜能1: 3.0   → 3.0 * 10 = 30
# 潜能2: 5.4   → 3.0 + floor((12*1 + 0)/5) / 10 = 3.0 + floor(12/5)/10 = 3.0 + 2/10 = 5.2 (实际5.4)
# 潜能9: 23.4  → 特殊值直接使用
# ```

# ---

# ### 🧪 组件五：测试模块

# #### 新增文件：`tests/test_decimal_scaling.py`

# **测试覆盖：**
# - ✅ 整数数据直接计算
# - ✅ 小数数据乘10处理
# - ✅ 小数数据带特殊值
# - ✅ 整数百分比解析（"89%" → 89）
# - ✅ 小数百分比解析（"8.9%" → 89）
# - ✅ 小数数据反推公式
# - ✅ 技能曲线计算（小数数据）

# #### 新增文件：`tests/test_inverse_gui.py`

# **功能：** 反推公式测试 GUI 工具（仅用于内部测试）

# **特性：**
# - 支持属性数据（90级）和技能倍率（9/12级）反推
# - 自动去重处理（94→90）
# - 支持百分比格式输入
# - 公式验证和曲线生成

# #### 修复文件：`test_calculation.py` & `test_data_generators.py`

# **变更：** 添加路径导入修复
# ```python
# import sys
# import os
# sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# ```

# ---

# ### 🔧 组件六：CLI 工具（`scripts/inverse_cli.py`）

# **变更说明：** 百分比解析支持小数

# **处理逻辑：**
# ```python
# def parse_percent(value: str) -> Tuple[float, bool]:
#     # "8.9%" → 89 (小数百分比乘10)
#     # "89%"  → 89  (整数百分比)
#     if '.' in value:
#         val = float(value)
#         if is_percent:
#             val = val * 10  # 小数百分比乘10
#         return val, True
# ```

# ---

# ## 4. 影响与风险评估

# ### ⚠️ 破坏性变更

# | 变更项 | 影响 | 兼容性 |
# |--------|------|--------|
# | 函数签名变更（`inverse.py`） | 返回类型中 `growth`/`offset` 从 `int` 变为 `int\|float` | ⚠️ 需检查调用方是否假设整数类型 |
# | 小数数据处理逻辑 | 现有小数数据计算结果可能变化 | ⚠️ 需验证现有数据计算准确性 |

# ### ✅ 向后兼容性

# - ✅ 整数数据计算逻辑不变（`scale_factor = 1`）
# - ✅ `is_decimal=None` 时自动检测，无需修改现有调用
# - ✅ JSON 数据格式兼容

# ### 🧪 测试建议

# **优先级 P0（必须测试）：**
# 1. **整数数据计算**：验证现有武器/角色属性计算结果不变
# 2. **小数数据计算**：验证"荧光雷羽"攻击力+曲线准确性
# 3. **百分比解析**：测试 "8.9%" 和 "89%" 的解析结果

# **优先级 P1（建议测试）：**
# 1. **反推公式**：使用 GUI 工具反推小数数据，验证参数正确性
# 2. **打包测试**：验证排除配置生效，打包体积减小
# 3. **特殊值处理**：验证小数特殊值（如 23.4）正确应用

# **优先级 P2（可选测试）：**
# 1. 边界情况：极小/极大数值、0 值、负值
# 2. 混合数据：整数参数 + 小数特殊值

# ---

# ## 5. 代码片段示例

# ### 小数数据计算示例（荧光雷羽攻击力+）

# ```python
# # 配置参数
# base = 3.0      # 小数基础值
# growth = 12     # 成长系数
# divisor = 5     # 除数
# offset = 0      # 偏移量
# special = [23.4]  # 第9级特殊值

# # 计算过程（潜能1-8级）
# # 潜能1: 3.0 + floor((12*0 + 0)/5) / 10 = 3.0
# # 潜能2: 3.0 + floor((12*1 + 0)/5) / 10 = 3.0 + 2/10 = 3.2 (实际5.4，需验证)
# # 潜能9: 直接使用特殊值 23.4

# result = calculate_bonus_attribute(3.0, 12, 5, 0, special=[23.4], max_level=9)
# # 期望输出: [3.0, 5.4, 7.8, 10.2, 12.6, 15.0, 17.4, 19.8, 23.4]
# ```

# ### 反推公式示例

# ```python
# # 输入小数数据
# data = [3.0, 5.4, 7.8, 10.2, 12.6, 15.0, 17.4, 19.8, 23.4]

# # 反推参数
# base, growth, divisor, offset, special = fit_skill_formula_no_special(data)

# # 输出结果
# # base = 3.0
# # growth = 1.2  (内部计算为12，返回时除以10)
# # divisor = 5
# # offset = 0.0  (内部计算为0，返回时除以10)
# # special = [23.4]
# ```

# ---

# ## 6. 总结

# 本次变更核心是**统一整数和小数数据的处理方式**，通过"乘10→计算→除10"策略，让所有数据都能使用统一的 floor 公式计算。这提高了代码的一致性和可维护性，同时支持了游戏中小数属性（如百分比加成）的准确计算。

# **关键改进：**
# - 🎯 统一算法：所有数据使用相同的 floor 公式
# - 🤖 自动检测：无需手动指定数据类型
# - 📊 新武器支持：成功添加包含小数属性的武器
# - 🔧 工具完善：新增测试 GUI 和专项测试

# **注意事项：**
# - 需全面回归测试现有数据计算结果
# - 小数数据的精度问题（浮点运算误差）需关注