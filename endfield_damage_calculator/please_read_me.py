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
_VERSION = "1.8.1"

# EXE 版本号（用于打包发布）
_EXE_VERSION = "0.2.0-beta"
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

# *   **影响范围：** 🟢 **低** - 主要是文档完善和类型注解改进，核心逻辑无重大变更
# *   **关键变更：**
#     *   📝 **新增项目文档**：添加 `PROJECT_DOCUMENTATION.md` 和 `README.md` 完整项目文档
#     *   🔧 **类型注解优化**：更新 `data_generator.py` 的返回类型注解，支持嵌套列表
#     *   📄 **文档字符串修正**：修正 `formula.py` 中 special 参数的说明
#     *   ⚠️ **错误处理改进**：`loader.py` 中解析失败时抛出异常而非静默返回
#     *   🧹 **代码清理**：移除 `please_read_me.py` 中大量注释掉的文档内容
#     *   📋 **.gitignore 重组**：重新组织并添加更多忽略规则分类

# ---

# ## 2. 可视化概览（代码与逻辑映射）

# ```mermaid
# graph TD
#     subgraph "业务目标：文档完善与代码质量提升"
#         A["文档完善"] --> B["新增项目文档"]
#         A --> C["新增README"]
#         D["代码质量"] --> E["类型注解优化"]
#         D --> F["错误处理改进"]
#         D --> G["代码清理"]
#     end
    
#     subgraph "data_generator.py - 类型注解优化"
#         E1["generate_weapon_attributes()"] --> E2["返回类型更新"]
#         E2 --> E3["Dict[str, Union[List[float], List[List[float]]]]"]
#     end
    
#     subgraph "formula.py - 文档修正"
#         F1["calculate_bonus_attribute()"] --> F2["special参数说明"]
#         F2 --> F3["修正为'第9级的特殊值'"]
#     end
    
#     subgraph "loader.py - 错误处理改进"
#         G1["process_input_data()"] --> G2["解析失败处理"]
#         G2 --> G3["抛出ValueError异常"]
#     end
    
#     A -.-> B
#     A -.-> C
#     D -.-> E1
#     D -.-> F1
#     D -.-> G1
# ```

# ```mermaid
# sequenceDiagram
#     participant User as 用户代码
#     participant Loader as loader.py
#     participant Gen as data_generator.py
#     participant Formula as formula.py
    
#     User->>Loader: 处理输入数据
#     alt 数据解析失败
#         Loader-->>User: 抛出 ValueError 异常
#     else 数据解析成功
#         Loader-->>User: 返回处理后的数据
#     end
    
#     User->>Gen: 生成武器属性
#     Gen->>Gen: 返回嵌套列表类型
#     Gen-->>User: Dict[str, Union[List[float], List[List[float]]]]
    
#     User->>Formula: 计算附加属性
#     Formula-->>User: 返回计算结果（文档已更新）
# ```

# ---

# ## 3. 详细变更分析

# ### 📝 组件一：新增项目文档

# #### 新增文件：`PROJECT_DOCUMENTATION.md`

# **变更说明：** 新建完整的项目文档，包含项目结构、核心功能、使用指南等内容

# **主要章节：**
# | 章节 | 内容 |
# |------|------|
# | **项目概述** | 项目简介和目标 |
# | **项目结构** | 目录结构说明 |
# | **核心功能模块** | 计算引擎、角色武器数据、数据加载器等 |
# | **使用指南** | CLI、编程方式、GUI 三种使用方法 |
# | **数据格式规范** | 属性数据和技能倍率格式 |
# | **测试运行** | 测试命令和覆盖范围 |
# | **环境要求** | Python 版本和依赖说明 |
# | **常见问题** | FAQ 和解决方案 |
# | **开发指南** | 添加新角色/武器的步骤 |

# #### 新增文件：`endfield_damage_calculator/README.md`

# **变更说明：** 为项目添加用户友好的 README 文档

# **主要内容包括：**
# - 🌟 项目简介和功能特性表
# - 📁 详细的项目结构树
# - 🚀 快速开始指南（环境要求、安装、运行、打包）
# - 📖 使用指南（基本操作流程、公式反推工具）
# - 🧮 核心算法说明（成长公式、小数数据处理、伤害计算公式）
# - 🔧 API 文档（计算模块函数表）
# - 🧪 测试说明和运行命令
# - 📦 数据格式示例（角色和武器 JSON 格式）
# - 📝 开发指南和代码规范

# ---

# ### 🔧 组件二：类型注解优化

# #### 文件：`endfield_damage_calculator/calculation/data_generator.py`

# **变更说明：** 更新 `generate_weapon_attributes()` 函数的返回类型注解

# **代码变更：**
# ```python
# # 旧代码
# def generate_weapon_attributes(
#     growth_params: Dict[str, Any]
# ) -> Dict[str, List[float]]:
#     attributes: Dict[str, List[float]] = {}

# # 新代码
# def generate_weapon_attributes(
#     growth_params: Dict[str, Any]
# ) -> Dict[str, Union[List[float], List[List[float]]]]:
#     attributes: Dict[str, Union[List[float], List[List[float]]]] = {}
# ```

# **原因：** 武器属性可能包含嵌套列表（如技能倍率），需要支持 `List[List[float]]` 类型

# ---

# ### 📄 组件三：文档字符串修正

# #### 文件：`endfield_damage_calculator/calculation/formula.py`

# **变更说明：** 修正 `calculate_bonus_attribute()` 函数的文档字符串

# **代码变更：**
# ```python
# # 旧代码
# special: 特殊值列表（第9级及以后的特殊值），如 [79] 表示第9级使用79（支持整数和小数）

# # 新代码
# special: 特殊值列表（第9级的特殊值），如 [23.4] 表示第9级使用23.4（支持整数和小数）
# ```

# **影响：** 文档更准确地描述了 special 参数的含义和用途

# ---

# ### ⚠️ 组件四：错误处理改进

# #### 文件：`endfield_damage_calculator/data/loader.py`

# **变更说明：** 改进 `process_input_data()` 函数的错误处理逻辑

# **代码变更：**
# ```python
# # 旧代码
# try:
#     # 解析逻辑...
# except ValueError:
#     return (data, DATA_TYPE_INTEGER, 1)  # 静默返回原始数据

# # 新代码
# try:
#     # 解析逻辑...
# except ValueError:
#     raise ValueError(f"无法解析数据: {data}")  # 抛出异常
# ```

# **影响：** 
# - ✅ 更好的错误提示，帮助开发者快速定位问题
# - ✅ 避免静默失败导致的数据不一致
# - ⚠️ 破坏性变更：调用方需要处理异常

# ---

# ### 🧹 组件五：代码清理

# #### 文件：`endfield_damage_calculator/please_read_me.py`

# **变更说明：** 删除了大量注释掉的文档内容（约 460 行）

# **删除内容：**
# - 完整的代码审查报告（已注释）
# - Mermaid 流程图代码
# - 详细的变更分析表格
# - 影响与风险评估
# - 代码片段示例

# **原因：** 这些内容已移至独立的项目文档文件中，避免代码文件过于冗长

# ---

# ### 📋 组件六：.gitignore 重组

# #### 文件：`.gitignore`

# **变更说明：** 重新组织 gitignore 文件，添加分类注释和更多忽略规则

# **新增分类：**
# | 分类 | 新增内容 |
# |------|----------|
# | **IDE 配置** | `.idea/`, `.trae/` |
# | **Skills 锁文件** | `skills-lock.json` |
# | **Python 缓存** | `*.egg-info/` |
# | **虚拟环境** | `.venv/` |
# | **测试缓存** | `.pytest_cache/` |
# | **构建输出** | `build/`, `dist/`, `*.spec` |
# | **日志** | `debug.log` |
# | **IDE 上传模块** | `github_upload_module.py`, `github_download_module.py`（SSH，勿提交 Token） |
# | **压缩文件** | `*.zip` |

# **移除内容：**
# - ❌ `*.md`（不再忽略所有 markdown 文件）

# ---

# ## 4. 影响与风险评估

# ### ⚠️ 破坏性变更

# | 变更项 | 影响 | 兼容性 |
# |--------|------|--------|
# | `loader.py` 错误处理 | 调用方需要捕获 `ValueError` 异常 | ⚠️ 需要更新调用代码 |

# ### ✅ 向后兼容性

# - ✅ 类型注解变更不影响运行时行为
# - ✅ 文档字符串修正不影响功能
# - ✅ 新增文档文件不影响现有代码
# - ✅ .gitignore 变更不影响代码逻辑

# ### 🧪 测试建议

# **优先级 P0（必须测试）：**
# 1. **错误处理测试**：验证 `process_input_data()` 在解析失败时正确抛出异常
# 2. **类型注解测试**：验证 `generate_weapon_attributes()` 返回类型符合预期

# **优先级 P1（建议测试）：**
# 1. **文档完整性**：检查新增文档的链接和示例是否正确
# 2. **gitignore 有效性**：验证新增的忽略规则是否生效

# ---

# ## 5. 代码片段示例

# ### 类型注解使用示例

# ```python
# from typing import Dict, List, Union
# from calculation.data_generator import generate_weapon_attributes

# # 武器属性生成（支持嵌套列表）
# params = {
#     '基础攻击力': {'base': 34, 'growth': 31, 'divisor': 9, 'offset': 8},
#     '攻击力+': {'base': 3.0, 'growth': 12, 'divisor': 5, 'special': [23.4]}
# }

# attrs = generate_weapon_attributes(params)
# # 返回类型: Dict[str, Union[List[float], List[List[float]]]]
# # '基础攻击力' -> List[float] (90个值)
# # '攻击力+' -> List[float] (9个值)
# ```

# ### 错误处理示例

# ```python
# from data.loader import process_input_data

# try:
#     value, data_type, scale_factor = process_input_data("invalid_data")
# except ValueError as e:
#     print(f"数据解析失败: {e}")
#     # 输出: 数据解析失败: 无法解析数据: invalid_data
# ```

# ---

# ## 6. 总结

# 本次变更是一次**文档完善和代码质量提升**，核心目标是：

# **关键改进：**
# - 📝 **文档完善**：新增完整的项目文档和用户 README
# - 🔧 **类型注解优化**：更准确地描述函数返回类型
# - ⚠️ **错误处理改进**：提供更清晰的错误提示
# - 🧹 **代码清理**：移除冗余的注释内容

# **架构优化：**
# - 文档与代码分离，提高可维护性
# - 类型注解更准确，便于 IDE 智能提示
# - 错误处理更严格，避免静默失败

# **注意事项：**
# - ⚠️ `loader.py` 的错误处理变更需要调用方更新异常处理逻辑
# - ✅ 其他变更均为向后兼容，无需修改现有调用代码