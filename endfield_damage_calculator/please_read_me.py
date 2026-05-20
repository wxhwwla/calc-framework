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
_VERSION = "1.8.0"

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

# *   **影响范围：** 🔴 **高** - 核心计算逻辑重构，新增配置和数据生成模块，影响所有数值计算和数据处理流程
# *   **关键变更：**
#     *   ✨ **新增配置模块**：集中管理属性常量、分类判断和参数验证
#     *   🆕 **新增数据生成器**：统一角色/武器属性生成接口
#     *   🔧 **重构反向计算**：提取内部辅助函数，消除重复代码，改进小数精度处理
#     *   📦 **扩展数据加载器**：支持数据类型检测和元数据管理
#     *   🧪 **增强测试覆盖**：新增配置模块和数据生成器的单元测试

# ---

# ## 2. 可视化概览（代码与逻辑映射）

# ```mermaid
# graph TD
#     subgraph "业务目标：统一配置管理与数据生成"
#         A["配置管理"] --> B["属性分类判断"]
#         A --> C["参数验证"]
#         D["数据生成"] --> E["角色属性生成"]
#         D --> F["武器属性生成"]
#     end
    
#     subgraph "config.py - 新增配置模块"
#         C1["CHARACTER_NORMAL_ATTRS"] --> C2["CHARACTER_SKILL_ATTRS"]
#         C1 --> C3["WEAPON_BASE_ATTRS"]
#         C2 --> C4["get_attribute_category()"]
#         C4 --> C5["is_character_attribute()"]
#         C4 --> C6["is_weapon_attribute()"]
#         C4 --> C7["validate_growth_params()"]
#     end
    
#     subgraph "data_generator.py - 新增数据生成器"
#         D1["generate_attributes()"] --> D2["mode='character'"]
#         D1 --> D3["mode='weapon'"]
#         D2 --> D4["generate_character_attributes()"]
#         D3 --> D5["generate_weapon_attributes()"]
#     end
    
#     subgraph "inverse.py - 重构反向计算"
#         I1["fit_attribute_formula()"] --> I2["_scale_data()"]
#         I1 --> I3["_find_best_params()"]
#         I4["fit_skill_formula()"] --> I2
#         I4 --> I3
#         I5["validate_attribute_formula()"] --> I6["calculate_growth_curve()"]
#     end
    
#     subgraph "loader.py - 扩展数据加载器"
#         L1["detect_data_type()"] --> L2["parse_percentage()"]
#         L1 --> L3["process_input_data()"]
#         L3 --> L4["restore_data()"]
#         L4 --> L5["add_metadata_to_value()"]
#         L5 --> L6["extract_value_from_metadata()"]
#     end
    
#     A -.-> C1
#     D -.-> D1
#     I1 -.-> I2
#     L1 -.-> L2
# ```

# ```mermaid
# sequenceDiagram
#     participant User as 用户代码
#     participant Config as config.py
#     participant Gen as data_generator.py
#     participant Formula as formula.py
#     participant Inverse as inverse.py
#     participant Loader as loader.py
    
#     User->>Config: 获取属性分类
#     Config-->>User: 返回分类结果
    
#     User->>Gen: 生成属性数据
#     Gen->>Formula: 调用计算函数
#     Formula-->>Gen: 返回成长曲线
#     Gen-->>User: 返回属性数据
    
#     User->>Inverse: 反推公式参数
#     Inverse->>Inverse: _scale_data() 缩放数据
#     Inverse->>Inverse: _find_best_params() 查找参数
#     Inverse-->>User: 返回拟合参数
    
#     User->>Loader: 处理输入数据
#     Loader->>Loader: detect_data_type() 检测类型
#     Loader->>Loader: process_input_data() 转换数据
#     Loader-->>User: 返回处理后的数据
# ```

# ---

# ## 3. 详细变更分析

# ### 📦 组件一：新增配置模块（`calculation/config.py`）

# **变更说明：** 新建集中配置管理模块，消除各模块中的硬编码属性名称

# **核心功能：**

# | 功能类别 | 函数/常量 | 说明 |
# |---------|----------|------|
# | **属性常量** | `CHARACTER_NORMAL_ATTRS` | 角色普通属性列表（力量、敏捷、智识、意志、基础攻击力） |
# | | `CHARACTER_SKILL_ATTRS` | 角色技能属性列表（战技倍率、连携技倍率、终结技倍率） |
# | | `WEAPON_BASE_ATTRS` | 武器基础属性列表（基础攻击力） |
# | | `WEAPON_BONUS_ATTR_SUFFIX` | 武器附加属性后缀（'+'） |
# | **分类判断** | `get_attribute_category()` | 获取属性分类（character_normal/character_skill/weapon_base/weapon_bonus/unknown） |
# | | `is_character_attribute()` | 判断是否为角色属性 |
# | | `is_weapon_attribute()` | 判断是否为武器属性 |
# | | `is_weapon_base_attribute()` | 判断是否为武器基础属性 |
# | | `is_weapon_bonus_attribute()` | 判断是否为武器附加属性 |
# | | `is_skill_attribute()` | 判断是否为技能属性 |
# | **参数管理** | `get_default_growth_params()` | 获取默认成长参数配置 |
# | | `validate_growth_params()` | 验证成长参数有效性 |

# **代码示例：**
# ```python
# # 属性分类判断
# category = get_attribute_category('敏捷+')  # 返回 'weapon_bonus'
# is_char = is_character_attribute('力量')    # 返回 True

# # 参数验证
# params = {'base': 100, 'growth': 50, 'divisor': 10}
# result = validate_growth_params(params)
# # 返回 {'valid': True, 'errors': [], 'warnings': []}
# ```

# ---

# ### 🆕 组件二：新增数据生成器（`calculation/data_generator.py`）

# **变更说明：** 新建统一数据生成器，整合角色和武器属性生成逻辑

# **核心函数：**

# | 函数名 | 参数 | 返回值 | 说明 |
# |--------|------|--------|------|
# | `generate_attributes()` | `growth_params`, `mode` | `Dict[str, List]` | 统一生成接口，通过 mode 区分角色/武器 |
# | `generate_character_attributes()` | `growth_params` | `Dict[str, List]` | 生成角色属性（普通属性90级，技能倍率12级） |
# | `generate_weapon_attributes()` | `growth_params` | `Dict[str, List]` | 生成武器属性（基础90级，附加9级） |

# **数据格式示例：**
# ```python
# # 角色属性生成
# params = {
#     '力量': {'base': 100, 'growth': 50, 'divisor': 10, 'offset': 0},
#     '战技倍率': [
#         {'base': 100, 'growth': 20, 'divisor': 10, 'special': [150, 160, 170]}
#     ]
# }
# attrs = generate_character_attributes(params)
# # 返回: {'力量': [100, 105, ..., ...], '战技倍率': [[100, 102, ..., 150, 160, 170]]}

# # 武器属性生成
# params = {
#     '基础攻击力': {'base': 34, 'growth': 31, 'divisor': 9, 'offset': 8},
#     '攻击力+': {'base': 3.0, 'growth': 12, 'divisor': 5, 'offset': 0, 'special': [23.4]}
# }
# attrs = generate_weapon_attributes(params)
# ```

# ---

# ### 🔧 组件三：重构反向计算模块（`calculation/inverse.py`）

# **变更说明：** 提取内部辅助函数，消除重复代码，改进小数精度处理

# **新增内部辅助函数：**

# | 函数名 | 功能 |
# |--------|------|
# | `_is_decimal_data(data)` | 判断数据是否包含小数 |
# | `_scale_data(data, scale_factor)` | 缩放数据（小数乘10转换为整数） |
# | `_find_best_params()` | 查找最佳拟合参数（核心算法） |

# **核心优化：**

# 1. **小数精度处理改进：**
# ```python
# # 旧代码（直接乘除）
# scaled_base = base * scale_factor

# # 新代码（使用 round 确保精度）
# scaled_base = int(round(base * scale_factor))
# ```

# 2. **验证逻辑简化：**
# ```python
# # 旧代码：手动实现计算和验证
# for lv in range(1, 91):
#     calculated = scaled_base + math.floor((growth * (lv - 1) + offset) / divisor)
#     if abs(calculated - scaled_data[lv-1]) > 0.001:
#         return False

# # 新代码：复用正向计算函数
# calculated = calculate_growth_curve(base, growth, divisor, offset)
# for i, val in enumerate(data):
#     if abs(calculated[i] - val) > 0.001:
#         return False
# ```

# 3. **消除重复代码：** 将 `fit_attribute_formula()`, `fit_skill_formula()`, `fit_skill_formula_no_special()` 中的重复拟合逻辑提取到 `_find_best_params()` 中

# ---

# ### 📊 组件四：扩展数据加载器（`data/loader.py`）

# **变更说明：** 新增数据类型处理和元数据管理功能

# **新增数据类型常量：**

# | 常量名 | 值 | 说明 |
# |--------|-----|------|
# | `DATA_TYPE_INTEGER` | `'integer'` | 整数类型 |
# | `DATA_TYPE_DECIMAL` | `'decimal'` | 小数类型 |
# | `DATA_TYPE_PERCENTAGE` | `'percentage'` | 百分比类型 |

# **新增处理函数：**

# | 函数名 | 功能 |
# |--------|------|
# | `detect_data_type(value)` | 检测单个数据类型（整数/小数/百分比） |
# | `parse_percentage(value)` | 解析百分比字符串（如 "156%" → 156） |
# | `process_input_data(data)` | 处理输入数据，根据类型转换 |
# | `restore_data(processed_value, data_type, scale_factor)` | 还原处理后的数据 |
# | `add_metadata_to_value(value)` | 为单个值添加元数据 |
# | `extract_value_from_metadata(metadata_dict)` | 从元数据字典中提取原始值 |
# | `process_list_with_metadata(data_list)` | 处理列表数据，为每个元素添加元数据 |
# | `restore_list_from_metadata(metadata_list)` | 从元数据列表中还原原始数据 |

# **数据处理规则：**

# | 数据类型 | 处理方式 | 示例 |
# |---------|---------|------|
# | 整数 | 直接返回 | `100` → `100` |
# | 小数 | 乘10转换为整数 | `3.4` → `34` |
# | 百分比（整数） | 移除%符号 | `"89%"` → `89` |
# | 百分比（小数） | 移除%符号并乘10 | `"8.9%"` → `89` |

# ---

# ### 🧮 组件五：优化正向计算模块（`calculation/formula.py`）

# **变更说明：** 改进小数数据处理精度

# **关键变更：**
# ```python
# # 旧代码
# scaled_base = base * scale_factor
# scaled_growth = growth * scale_factor
# scaled_offset = offset * scale_factor

# # 新代码（使用 round 确保浮点数精度）
# scaled_base = round(base * scale_factor)
# scaled_growth = round(growth * scale_factor)
# scaled_offset = round(offset * scale_factor)
# ```

# **影响：** 确保小数数据在缩放过程中的精度，避免浮点运算误差

# ---

# ### 📝 组件六：模块导出更新（`calculation/__init__.py`）

# **变更说明：** 导出新增模块的公共接口

# **新增导出项：**

# ```python
# # 配置模块常量
# "CHARACTER_NORMAL_ATTRS",
# "CHARACTER_SKILL_ATTRS",
# "WEAPON_BASE_ATTRS",
# "WEAPON_BONUS_ATTR_SUFFIX",
# "DEFAULT_GROWTH_PARAMS",

# # 配置模块函数
# "get_default_growth_params",
# "get_attribute_category",
# "is_character_attribute",
# "is_weapon_attribute",
# "is_weapon_base_attribute",
# "is_weapon_bonus_attribute",
# "is_skill_attribute",
# "validate_growth_params",

# # 数据生成器函数
# "generate_attributes",
# "generate_character_attributes",
# "generate_weapon_attributes",
# ```

# ---

# ### 🧪 组件七：测试模块增强

# #### 新增测试文件：`tests/test_config.py`

# **测试覆盖：**
# - ✅ 配置常量定义
# - ✅ 属性分类判断
# - ✅ 默认参数获取
# - ✅ 参数验证（有效/无效/除数为零）

# #### 新增测试文件：`tests/test_unified_data_generator.py`

# **测试覆盖：**
# - ✅ 角色属性生成（基本/带技能倍率/空参数）
# - ✅ 武器属性生成（基本/空参数）
# - ✅ 通用生成函数（角色模式/武器模式/无效模式）

# #### 新增测试文件：`tests/test_inverse_refactored.py`

# **测试覆盖：**
# - ✅ 内部辅助函数（`_is_decimal_data`, `_scale_data`, `_find_best_params`）
# - ✅ 属性公式拟合（整数数据）
# - ✅ 技能公式拟合（整数/小数数据）
# - ✅ 统一拟合接口自动检测

# #### 修改测试文件：`tests/test_calculation.py`

# **变更：** 调整断言逻辑，适应小数参数返回
# ```python
# # 旧代码
# self.assertEqual(growth, 2)
# self.assertEqual(divisor, 1)

# # 新代码（支持小数参数）
# self.assertAlmostEqual(growth / divisor, 2.0, places=5)
# ```

# #### 修改测试文件：`tests/test_decimal_scaling.py`

# **变更：** 添加注释说明测试预期行为
# ```python
# # 该数据无法用单一公式拟合，第9级作为special值
# assert special == [23.4], f"special错误: {special} != [23.4]"
# ```

# ---

# ### 🗑️ 组件八：清理文档（`please_read_me.py`）

# **变更说明：** 移除旧的文档注释内容（已注释掉的代码）

# ---

# ## 4. 影响与风险评估

# ### ⚠️ 破坏性变更

# | 变更项 | 影响 | 兼容性 |
# |--------|------|--------|
# | 新增配置模块 | 无破坏性变更，纯新增功能 | ✅ 向后兼容 |
# | 新增数据生成器 | 无破坏性变更，纯新增功能 | ✅ 向后兼容 |
# | 反向计算重构 | 内部实现变更，公共接口不变 | ✅ 向后兼容 |
# | 数据加载器扩展 | 无破坏性变更，纯新增功能 | ✅ 向后兼容 |

# ### ✅ 向后兼容性

# - ✅ 所有现有公共接口保持不变
# - ✅ 新增功能通过独立模块提供
# - ✅ 内部重构不影响外部调用
# - ✅ 测试用例已更新以适应新实现

# ### 🧪 测试建议

# **优先级 P0（必须测试）：**
# 1. **配置模块功能**：验证属性分类判断和参数验证正确性
# 2. **数据生成器**：测试角色和武器属性生成的准确性
# 3. **反向计算重构**：验证重构后的拟合算法与原实现结果一致

# **优先级 P1（建议测试）：**
# 1. **小数精度处理**：验证 `round()` 函数对计算结果的影响
# 2. **数据类型检测**：测试整数、小数、百分比数据的正确识别
# 3. **元数据管理**：验证数据添加/提取元数据的双向一致性

# **优先级 P2（可选测试）：**
# 1. 边界情况：极小/极大数值、0 值、负值
# 2. 混合数据：整数参数 + 小数特殊值
# 3. 性能测试：重构后的算法性能对比

# ---

# ## 5. 代码片段示例

# ### 配置模块使用示例

# ```python
# from calculation.config import (
#     get_attribute_category,
#     is_character_attribute,
#     validate_growth_params
# )

# # 属性分类判断
# category = get_attribute_category('敏捷+')  # 'weapon_bonus'
# is_char = is_character_attribute('力量')    # True

# # 参数验证
# params = {'base': 100, 'growth': 50, 'divisor': 10, 'offset': 0}
# result = validate_growth_params(params)
# # {'valid': True, 'errors': [], 'warnings': []}
# ```

# ### 数据生成器使用示例

# ```python
# from calculation.data_generator import generate_attributes

# # 生成角色属性
# params = {
#     '力量': {'base': 100, 'growth': 50, 'divisor': 10},
#     '战技倍率': [{'base': 100, 'growth': 20, 'divisor': 10, 'special': [150, 160, 170]}]
# }
# attrs = generate_attributes(params, mode='character')

# # 生成武器属性
# params = {
#     '基础攻击力': {'base': 34, 'growth': 31, 'divisor': 9, 'offset': 8},
#     '攻击力+': {'base': 3.0, 'growth': 12, 'divisor': 5, 'special': [23.4]}
# }
# attrs = generate_attributes(params, mode='weapon')
# ```

# ### 数据加载器使用示例

# ```python
# from data.loader import (
#     detect_data_type,
#     process_input_data,
#     restore_data
# )

# # 检测数据类型
# data_type = detect_data_type("8.9%")  # 'percentage'

# # 处理输入数据
# value, data_type, scale_factor = process_input_data("8.9%")
# # (89, 'percentage', 10)

# # 还原数据
# original = restore_data(89, 'percentage', 10)  # '8.9%'
# ```

# ---

# ## 6. 总结

# 本次变更是一次**模块化重构**，核心目标是提高代码的可维护性和可扩展性：

# **关键改进：**
# - 🎯 **配置集中化**：消除硬编码，统一管理属性常量和配置
# - 🆕 **功能模块化**：新增独立的数据生成器模块
# - 🔧 **代码重构**：提取公共逻辑，消除重复代码
# - 📊 **数据类型支持**：完善数据类型检测和转换机制
# - 🧪 **测试增强**：新增全面的单元测试覆盖

# **架构优化：**
# - 清晰的模块职责划分
# - 统一的接口设计
# - 完善的错误处理和验证机制

# **注意事项：**
# - 所有变更均为向后兼容，无需修改现有调用代码
# - 建议运行完整测试套件验证重构正确性
# - 新增功能可通过导入相应模块直接使用