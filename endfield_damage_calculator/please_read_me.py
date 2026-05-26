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
    3. 属性展示：角色属性列与武器属性列分列显示等级曲线明细
    4. 乘区计算：实时计算能力乘区、能力值加成、攻击力等数据
"""

# ==================== 版本信息（只在此处修改） ====================
# _VERSION：项目与 pip 包版本（pyproject.toml 通过 dynamic 读取，勿在别处重复写死）
# _EXE_VERSION：窗口标题与 dist/*.exe 用户可见版本（仅重新打包 exe 时手动修改；改后须重新 build.py）
_VERSION = "2.0.2"
_EXE_VERSION = "0.4.0-beta"
# ==============================================================

# ==================== GitHub 上传流程（必读） ====================
UPLOAD_WORKFLOW = """
GitHub 上传与版本号（仓库根目录执行: python github_upload_module.py）

1. 版本分工
   - _VERSION：上传脚本在有「业务改动」并 push 成功时自动递增（第三位 +1 为默认）。
   - _EXE_VERSION：仅在你重新打包 exe 前手动修改，上传脚本不会改它。
   - 第一位 MAJOR：永远只在下方 _VERSION 行手动改，脚本不会动。

2. 何时自动 bump _VERSION
   - 会：本次有新的业务文件改动，将产生新 commit 并推送到远程。
   - 不会：仅补推已有 commit、与远程已同步无改动、或使用了 --no-bump。

3. 升级幅度
   - 默认 Patch：1.8.1 → 1.8.2（第三位 +1）
   - Minor（大改动）：1.8.1 → 1.9.0（第二位 +1，第三位归零）
     · 交互：运行脚本时输入 M 或 minor
     · 非交互：python github_upload_module.py --minor
   - 不涨版本：python github_upload_module.py --no-bump

4. 提交说明（临时写在「本文件最下面」）
   - 上传前：脚本根据 git 改动自动生成 # --- UPLOAD_SUMMARY --- 块（勿手删标记行）。
   - commit 消息格式：
       v1.8.2: 一句话标题

       - 修改 xxx
       - 更新 weapons.json ...
   - push 成功后：脚本删除该总结块（_VERSION 保留）。
   - push 失败：总结块保留，版本不回滚；修好网络后可只 push 或 --no-bump 再传。

5. 常用命令
   python github_upload_module.py
   python github_upload_module.py --minor
   python github_upload_module.py --no-bump

6. 提交签名（可选，便于 GitHub 显示 Verified）
   - 若本机已配置 commit.gpgsign 或 user.signingkey，上传脚本会自动签名。
   - 未配置时脚本会打印设置提示；见 docs/操作指令集.md §1.5。

7. 从远程覆盖本地（危险，勿误点）
   - 仓库根：python github_download_module.py
   - 须完整输入确认词「覆盖本地」才会执行；会 reset --hard 并 clean 未跟踪文件。

许可与数据：LICENSE（软件）、DATA_LICENSE（游戏 JSON）、docs/数据来源与许可.md

完整操作指令（GUI、数据、测试、打包、GitHub、BWIKI、Cursor）见仓库根目录：
   docs/操作指令集.md
"""
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
    ├── gui_design/                # GUI（五列 + 底栏）
    │   ├── gui.py / confirm_orchestrator.py / search_controls.py
    │   ├── display_lines.py / display_view.py / display_request.py
    │   ├── loadout_state.py / loadout_evaluation.py / preview_lines.py
    │   └── selection_panel.py / selection_components.py
    ├── legal/                     # 许可与数据来源（GUI 对话框）
    │   └── attribution.py
    ├── calculation/               # 公式、乘区、伤害引擎、装备搜索
    │   ├── damage_engine.py / loadout_optimizer.py / mvp_pipeline.py
    │   └── multiplicative_zones/  # 能力、防御、最终攻击力等
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
    └── character_weapon_equipment/# 数据文件目录（许可见仓库根 DATA_LICENSE）
        ├── DATA_README.md         # 数据许可入口说明
        ├── character_data/        # 角色数据（JSON格式）
        └── weapon_data/           # 武器数据（JSON格式）

仓库根目录（与 [包] 并列）：
    ├── README.md / CONTEXT.md     # 门面与术语
    ├── docs/                      # 操作指令集、许可、算法与架构
    ├── tools/                     # 仓库级维护（见 tools/README.md）
    │   ├── bwiki_scout/         # BWIKI 侦察（output/ 已 gitignore）
    │   └── audit/               # 如 create_audit_issues.ps1
    ├── legacy/                  # 遗留脚本，不参与日常
    ├── LICENSE / DATA_LICENSE   # 软件与数据许可
    ├── github_upload_module.py  # 上传（版本 bump + 可选签名）
    └── github_download_module.py # 拉取覆盖（须输入「覆盖本地」）
"""

USAGE_INFO = f"""
使用方法：
    1. 运行方式：
        python main.py

    2. 打包方式（产出 dist/终末地伤害计算器/ 文件夹，exe 与 JSON 分开放置）：
        pip install -e ".[build]"
        python build.py
        全量/MVP 搜索导出在 exe 同级 search_output/（见 发布说明.txt）

    3. 操作流程：
        - 在左侧选择角色类型和星级
        - 在左侧选择武器类型和星级
        - 调整等级和信赖等级（角色）
        - 调整特殊能力等级（武器）
        - 点击「确认选择」刷新角色/武器属性列；两侧均有效时再更新右侧乘区

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
{UPLOAD_WORKFLOW}
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
{UPLOAD_WORKFLOW}
    """)

if __name__ == "__main__":
    show_help()

# --- UPLOAD_SUMMARY ---
# TITLE: 更新 8 处文件
# BODY:
# - 修改 endfield_damage_calculator/character_weapon_equipment/weapon_data/special_fields/codec.py
# - 更新 weapons.json 武器数据
# - 修改 endfield_damage_calculator/please_read_me.py
# - 修改 endfield_damage_calculator/scripts/seed_weapons.py
# - 修改 endfield_damage_calculator/tests/character_weapon_equipment/test_weapon_special_stack_layers.py
# - 修改 endfield_damage_calculator/tests/data/test_game_data_contract.py
# - 修改 endfield_damage_calculator/tests/tools/test_bwiki_scout.py
# - 修改 tools/bwiki_scout/weapon_wiki.py
# --- END UPLOAD_SUMMARY ---
