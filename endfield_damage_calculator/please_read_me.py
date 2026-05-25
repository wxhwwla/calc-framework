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
_VERSION = "1.19.0"
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
# TITLE: 更新 287 处文件
# BODY:
# - 变更 "docs//344/273/243/347/240/201/347/273/223/346/236/204/350/247/204/350/214/203.md"
# - 变更 "docs//344/274/232/350/257/235/346/216/245/347/273/255/346/211/213/345/206/214.md"
# - 更新文档 AGENTS.md
# - 更新文档 CONTEXT.md
# - 更新文档 docs/README.md
# - 变更 docs/adr/
# - 修改 endfield_damage_calculator/calculation/__init__.py
# - 变更 endfield_damage_calculator/calculation/abnormal/
# - 修改 endfield_damage_calculator/calculation/config.py
# - 变更 endfield_damage_calculator/calculation/core/
# - 修改 endfield_damage_calculator/calculation/curve_baker.py
# - 变更 endfield_damage_calculator/calculation/damage/
# - 修改 endfield_damage_calculator/calculation/damage_engine.py
# - 修改 endfield_damage_calculator/calculation/damage_types.py
# - 修改 endfield_damage_calculator/calculation/data_generator.py
# - 变更 endfield_damage_calculator/calculation/equipment/
# - 修改 endfield_damage_calculator/calculation/equipment_affix.py
# - 修改 endfield_damage_calculator/calculation/equipment_prune.py
# - 修改 endfield_damage_calculator/calculation/equipment_system.py
# - 修改 endfield_damage_calculator/calculation/formula.py
# - 修改 endfield_damage_calculator/calculation/in_memory_optimizer.py
# - 修改 endfield_damage_calculator/calculation/inverse.py
# - 变更 endfield_damage_calculator/calculation/loadout/
# - 修改 endfield_damage_calculator/calculation/loadout_attack_eval.py
# - 修改 endfield_damage_calculator/calculation/loadout_optimizer.py
# - 修改 endfield_damage_calculator/calculation/loadout_slot_search.py
# - 变更 endfield_damage_calculator/calculation/multi_skill/
# - 修改 endfield_damage_calculator/calculation/multi_skill_optimizer.py
# - 修改 endfield_damage_calculator/calculation/multi_skill_search_eval.py
# - 调整乘区逻辑 endfield_damage_calculator/calculation/multiplicative_zones/__init__.py
# - 调整乘区逻辑 endfield_damage_calculator/calculation/multiplicative_zones/ability_bonus_zone.py
# - 修改 endfield_damage_calculator/calculation/mvp_pipeline.py
# - 修改 endfield_damage_calculator/calculation/parallel_evaluate.py
# - 修改 endfield_damage_calculator/calculation/parallel_search.py
# - 修改 endfield_damage_calculator/calculation/physical_abnormal.py
# - 修改 endfield_damage_calculator/calculation/preview_cache.py
# - 修改 endfield_damage_calculator/calculation/result_cache.py
# - 修改 endfield_damage_calculator/calculation/result_export.py
# - 变更 endfield_damage_calculator/calculation/search/evaluate/
# - 修改 endfield_damage_calculator/calculation/search/evaluate_context.py
# - 修改 endfield_damage_calculator/calculation/search/evaluate_multi_skill.py
# - 修改 endfield_damage_calculator/calculation/search/evaluate_task.py
# - 变更 endfield_damage_calculator/calculation/search/persist/
# - 修改 endfield_damage_calculator/calculation/search/persist_store.py
# - 变更 endfield_damage_calculator/calculation/search/plan/
# - 修改 endfield_damage_calculator/calculation/search/plan_controller.py
# - 修改 endfield_damage_calculator/calculation/search/plan_estimate.py
# - 修改 endfield_damage_calculator/calculation/search/plan_job.py
# - 变更 endfield_damage_calculator/calculation/search/run/
# - 修改 endfield_damage_calculator/calculation/search/run_cancel.py
# - 修改 endfield_damage_calculator/calculation/search/run_mvp.py
# - 修改 endfield_damage_calculator/calculation/search/run_parallel.py
# - 修改 endfield_damage_calculator/calculation/search/run_runner.py
# - 修改 endfield_damage_calculator/calculation/search/run_session.py
# - 修改 endfield_damage_calculator/calculation/search/run_single_skill.py
# - 修改 endfield_damage_calculator/calculation/search_cancel.py
# - 修改 endfield_damage_calculator/calculation/search_controller.py
# - 修改 endfield_damage_calculator/calculation/search_estimate.py
# - 修改 endfield_damage_calculator/calculation/search_eval_context.py
# - 修改 endfield_damage_calculator/calculation/search_persistence.py
# - 修改 endfield_damage_calculator/calculation/search_runner.py
# - 修改 endfield_damage_calculator/calculation/search_session.py
# - 修改 endfield_damage_calculator/calculation/search_task_evaluator.py
# - 修改 endfield_damage_calculator/calculation/single_skill_search_job.py
# - 修改 endfield_damage_calculator/calculation/single_skill_search_runner.py
# - 修改 endfield_damage_calculator/calculation/skill_segments.py
# - 变更 endfield_damage_calculator/calculation/skills/
# - 修改 endfield_damage_calculator/calculation/spell_abnormal.py
# - 修改 endfield_damage_calculator/calculation/spell_abnormal_params.py
# - 修改 endfield_damage_calculator/calculation/top_n_tracker.py
# - 修改 endfield_damage_calculator/calculation/weapon_skill_selection.py
# - 修改 endfield_damage_calculator/character_weapon_equipment/character_data/add_character.py
# - 修改 endfield_damage_calculator/character_weapon_equipment/weapon_data/add_weapon.py
# - 修改 endfield_damage_calculator/data/equipment_catalog.py
# - 修改 endfield_damage_calculator/gui_design/app/confirm_orchestrator.py
# - 修改 endfield_damage_calculator/gui_design/app/display_request.py
# - 修改 endfield_damage_calculator/gui_design/app/loadout_evaluation.py
# - 修改 endfield_damage_calculator/gui_design/app/loadout_pending.py
# - 修改 endfield_damage_calculator/gui_design/app/loadout_state.py
# - 修改 endfield_damage_calculator/gui_design/calc_history.py
# - 修改 endfield_damage_calculator/gui_design/calc_mode_labels.py
# - 修改 endfield_damage_calculator/gui_design/confirm_orchestrator.py
# - 修改 endfield_damage_calculator/gui_design/confirm_refresh.py
# - 修改 endfield_damage_calculator/gui_design/controls/__init__.py
# - 变更 endfield_damage_calculator/gui_design/controls/enhancement/
# - 修改 endfield_damage_calculator/gui_design/controls/enhancement_controls.py
# - 修改 endfield_damage_calculator/gui_design/controls/enhancement_dialogs.py
# - 修改 endfield_damage_calculator/gui_design/controls/enhancement_preset.py
# - 修改 endfield_damage_calculator/gui_design/controls/enhancement_section.py
# - 修改 endfield_damage_calculator/gui_design/controls/fixed_loadout.py
# - 修改 endfield_damage_calculator/gui_design/controls/fixed_loadout_controls.py
# - 变更 endfield_damage_calculator/gui_design/controls/multi_skill/
# - 修改 endfield_damage_calculator/gui_design/controls/multi_skill_controls.py
# - 修改 endfield_damage_calculator/gui_design/controls/multi_skill_rows.py
# - 修改 endfield_damage_calculator/gui_design/controls/multi_skill_section.py
# - 变更 endfield_damage_calculator/gui_design/controls/search/
# - 修改 endfield_damage_calculator/gui_design/controls/search_actions.py
# - 修改 endfield_damage_calculator/gui_design/controls/search_controls.py
# - 修改 endfield_damage_calculator/gui_design/controls/search_section.py
# - 修改 endfield_damage_calculator/gui_design/damage_snapshot.py
# - 修改 endfield_damage_calculator/gui_design/damage_visualization.py
# - 修改 endfield_damage_calculator/gui_design/display_lines.py
# - 修改 endfield_damage_calculator/gui_design/display_request.py
# - 修改 endfield_damage_calculator/gui_design/display_view.py
# - 修改 endfield_damage_calculator/gui_design/enhancement_controls.py
# - 修改 endfield_damage_calculator/gui_design/fixed_loadout_controls.py
# - 修改 endfield_damage_calculator/gui_design/gui.py
# - 修改 endfield_damage_calculator/gui_design/gui_layout.py
# - 修改 endfield_damage_calculator/gui_design/gui_settings.py
# - 修改 endfield_damage_calculator/gui_design/label_layout.py
# - 修改 endfield_damage_calculator/gui_design/label_wrap.py
# - 变更 endfield_damage_calculator/gui_design/layout/
# - 修改 endfield_damage_calculator/gui_design/loadout_evaluation.py
# - 修改 endfield_damage_calculator/gui_design/loadout_pending.py
# - 修改 endfield_damage_calculator/gui_design/loadout_preset.py
# - 修改 endfield_damage_calculator/gui_design/loadout_state.py
# - 修改 endfield_damage_calculator/gui_design/multi_skill_controls.py
# - 修改 endfield_damage_calculator/gui_design/panel_hints.py
# - 修改 endfield_damage_calculator/gui_design/panels/special_ability_panel.py
# - 修改 endfield_damage_calculator/gui_design/panels/weapon_skill_selection.py
# - 修改 endfield_damage_calculator/gui_design/presentation/damage_snapshot.py
# - 修改 endfield_damage_calculator/gui_design/presentation/display_lines.py
# - 修改 endfield_damage_calculator/gui_design/presentation/preview_lines.py
# - 修改 endfield_damage_calculator/gui_design/presentation/search_results_lines.py
# - 修改 endfield_damage_calculator/gui_design/preset_batch_compare.py
# - 修改 endfield_damage_calculator/gui_design/preview_lines.py
# - 修改 endfield_damage_calculator/gui_design/search_controls.py
# - 修改 endfield_damage_calculator/gui_design/search_estimate_message.py
# - 修改 endfield_damage_calculator/gui_design/search_export_paths.py
# - 修改 endfield_damage_calculator/gui_design/search_results_lines.py
# - 修改 endfield_damage_calculator/gui_design/search_results_view.py
# - 修改 endfield_damage_calculator/gui_design/search_settings.py
# - 变更 endfield_damage_calculator/gui_design/search_ui/
# - 修改 endfield_damage_calculator/gui_design/selection_components.py
# - 修改 endfield_damage_calculator/gui_design/selection_panel.py
# - 变更 endfield_damage_calculator/gui_design/shared/
# - 修改 endfield_damage_calculator/gui_design/shell/app.py
# - 修改 endfield_damage_calculator/gui_design/shell/app_char_weapon_link.py
# - 修改 endfield_damage_calculator/gui_design/shell/app_control_dock.py
# - 修改 endfield_damage_calculator/gui_design/shell/app_loadout_access.py
# - 修改 endfield_damage_calculator/gui_design/shell/app_loadout_bridge.py
# - 修改 endfield_damage_calculator/gui_design/shell/app_main_layout.py
# - 修改 endfield_damage_calculator/gui_design/shell/app_selection.py
# - 修改 endfield_damage_calculator/gui_design/shell/app_window.py
# - 修改 endfield_damage_calculator/gui_design/shell/app_window_events.py
# - 修改 endfield_damage_calculator/gui_design/ui_preferences.py
# - 修改 endfield_damage_calculator/gui_design/weapon_display_text.py
# - 修改 endfield_damage_calculator/gui_design/weapon_skill_selection.py
# - 修改 endfield_damage_calculator/main.py
# - 修改 endfield_damage_calculator/please_read_me.py
# - 修改 endfield_damage_calculator/scripts/inverse_cli.py
# - 修改 endfield_damage_calculator/scripts/inverse_formula_gui.py
# - 变更 endfield_damage_calculator/tests/calculation/
# - 变更 endfield_damage_calculator/tests/character_weapon_equipment/
# - 修改 endfield_damage_calculator/tests/conftest.py
# - 变更 endfield_damage_calculator/tests/data/
# - 变更 endfield_damage_calculator/tests/fixtures/
# - 变更 endfield_damage_calculator/tests/gui_design/
# - 修改 endfield_damage_calculator/tests/gui_fixtures.py
# - 变更 endfield_damage_calculator/tests/misc_1/
# - 变更 endfield_damage_calculator/tests/misc_2/
# - 变更 endfield_damage_calculator/tests/multi_skill/
# - 变更 endfield_damage_calculator/tests/repo/
# - 修改 endfield_damage_calculator/tests/test_add_character.py
# - 修改 endfield_damage_calculator/tests/test_add_weapon.py
# - 修改 endfield_damage_calculator/tests/test_build_watchdog.py
# - 修改 endfield_damage_calculator/tests/test_bwiki_scout.py
# - 修改 endfield_damage_calculator/tests/test_calc_chain_naming_compat.py
# - 修改 endfield_damage_calculator/tests/test_calc_history.py
# - 修改 endfield_damage_calculator/tests/test_calc_mode_labels.py
# - 修改 endfield_damage_calculator/tests/test_calculation.py
# - 修改 endfield_damage_calculator/tests/test_config.py
# - 修改 endfield_damage_calculator/tests/test_confirm_orchestrator.py
# - 修改 endfield_damage_calculator/tests/test_confirm_refresh.py
# - 修改 endfield_damage_calculator/tests/test_confirm_selection_skill_levels.py
# - 修改 endfield_damage_calculator/tests/test_confirm_selection_state.py
# - 修改 endfield_damage_calculator/tests/test_confirm_suppress.py
# - 修改 endfield_damage_calculator/tests/test_control_dock_layout.py
# - 修改 endfield_damage_calculator/tests/test_coverage_boost_misc.py
# - 修改 endfield_damage_calculator/tests/test_curve_baker.py
# - 修改 endfield_damage_calculator/tests/test_damage_engine.py
# - 修改 endfield_damage_calculator/tests/test_damage_snapshot.py
# - 修改 endfield_damage_calculator/tests/test_damage_types.py
# - 修改 endfield_damage_calculator/tests/test_damage_visualization.py
# - 修改 endfield_damage_calculator/tests/test_decimal_scaling.py
# - 修改 endfield_damage_calculator/tests/test_display_lines_module.py
# - 修改 endfield_damage_calculator/tests/test_enemy_params.py
# - 修改 endfield_damage_calculator/tests/test_enhancement_integration.py
# - 修改 endfield_damage_calculator/tests/test_equipment_affix.py
# - 修改 endfield_damage_calculator/tests/test_equipment_catalog.py
# - 修改 endfield_damage_calculator/tests/test_equipment_filters.py
# - 修改 endfield_damage_calculator/tests/test_equipment_prune.py
# - 修改 endfield_damage_calculator/tests/test_equipment_sync.py
# - 修改 endfield_damage_calculator/tests/test_equipment_system.py
# - 修改 endfield_damage_calculator/tests/test_fixed_loadout_integration.py
# - 修改 endfield_damage_calculator/tests/test_fixed_loadout_selection.py
# - 修改 endfield_damage_calculator/tests/test_frozen_search_export_paths.py
# - 修改 endfield_damage_calculator/tests/test_game_data_contract.py
# - 修改 endfield_damage_calculator/tests/test_game_data_facade.py
# - 修改 endfield_damage_calculator/tests/test_github_upload_signing.py
# - 修改 endfield_damage_calculator/tests/test_gitignore_contract.py
# - 修改 endfield_damage_calculator/tests/test_gui_app_integration.py
# - 修改 endfield_damage_calculator/tests/test_gui_chart_theme.py
# - 修改 endfield_damage_calculator/tests/test_gui_data_load.py
# - 修改 endfield_damage_calculator/tests/test_gui_fonts_matplotlib.py
# - 修改 endfield_damage_calculator/tests/test_gui_import_regression.py
# - 修改 endfield_damage_calculator/tests/test_gui_layout_contract.py
# - 修改 endfield_damage_calculator/tests/test_gui_window.py
# - 修改 endfield_damage_calculator/tests/test_import_targets.py
# - 修改 endfield_damage_calculator/tests/test_inverse_refactored.py
# - 修改 endfield_damage_calculator/tests/test_label_layout.py
# - 修改 endfield_damage_calculator/tests/test_legal_attribution.py
# - 修改 endfield_damage_calculator/tests/test_loader_errors.py
# - 修改 endfield_damage_calculator/tests/test_loadout_attack_eval.py
# - 修改 endfield_damage_calculator/tests/test_loadout_evaluation.py
# - 修改 endfield_damage_calculator/tests/test_loadout_optimizer.py
# - 修改 endfield_damage_calculator/tests/test_loadout_pending.py
# - 修改 endfield_damage_calculator/tests/test_loadout_preset.py
# - 修改 endfield_damage_calculator/tests/test_loadout_state.py
# - 修改 endfield_damage_calculator/tests/test_loadout_varying_slots.py
# - 修改 endfield_damage_calculator/tests/test_manual_skill_counts_switch.py
# - 修改 endfield_damage_calculator/tests/test_migrate_weapon_skills_schema_tool.py
# - 修改 endfield_damage_calculator/tests/test_multi_skill_counts.py
# - 修改 endfield_damage_calculator/tests/test_multi_skill_full_search.py
# - 修改 endfield_damage_calculator/tests/test_multi_skill_optimizer.py
# - 修改 endfield_damage_calculator/tests/test_multi_skill_search_preview.py
# - 修改 endfield_damage_calculator/tests/test_multi_skill_segment_sync.py
# - 修改 endfield_damage_calculator/tests/test_mvp_pipeline.py
# - 修改 endfield_damage_calculator/tests/test_operation_log.py
# - 修改 endfield_damage_calculator/tests/test_optional_deps.py
# - 修改 endfield_damage_calculator/tests/test_pack_data_paths.py
# - 修改 endfield_damage_calculator/tests/test_panel_hints.py
# - 修改 endfield_damage_calculator/tests/test_parallel_evaluate.py
# - 修改 endfield_damage_calculator/tests/test_plugin_registry.py
# - 修改 endfield_damage_calculator/tests/test_preset_batch_compare.py
# - 修改 endfield_damage_calculator/tests/test_preview_cache.py
# - 修改 endfield_damage_calculator/tests/test_property_display_cache.py
# - 修改 endfield_damage_calculator/tests/test_property_display_integration.py
# - 修改 endfield_damage_calculator/tests/test_property_display_lines.py
# - 修改 endfield_damage_calculator/tests/test_readme_layers.py
# - 修改 endfield_damage_calculator/tests/test_release_layout.py
# - 修改 endfield_damage_calculator/tests/test_repo_layout.py
# - 修改 endfield_damage_calculator/tests/test_result_cache.py
# - 修改 endfield_damage_calculator/tests/test_result_export.py
# - 修改 endfield_damage_calculator/tests/test_scaling_mode.py
# - 修改 endfield_damage_calculator/tests/test_search_controller.py
# - 修改 endfield_damage_calculator/tests/test_search_controls.py
# - 修改 endfield_damage_calculator/tests/test_search_error_binding.py
# - 修改 endfield_damage_calculator/tests/test_search_estimate.py
# - 修改 endfield_damage_calculator/tests/test_search_export_paths.py
# - 修改 endfield_damage_calculator/tests/test_search_format.py
# - 修改 endfield_damage_calculator/tests/test_search_persistence.py
# - 修改 endfield_damage_calculator/tests/test_search_results_view.py
# - 修改 endfield_damage_calculator/tests/test_search_runner.py
# - 修改 endfield_damage_calculator/tests/test_search_session.py
# - 修改 endfield_damage_calculator/tests/test_search_settings.py
# - 修改 endfield_damage_calculator/tests/test_single_hit_preview.py
# - 修改 endfield_damage_calculator/tests/test_single_skill_search_job.py
# - 修改 endfield_damage_calculator/tests/test_single_skill_search_preview.py
# - 修改 endfield_damage_calculator/tests/test_single_skill_search_runner.py
# - 修改 endfield_damage_calculator/tests/test_skill_segments.py
# - 修改 endfield_damage_calculator/tests/test_skill_tables_damage_type.py
# - 修改 endfield_damage_calculator/tests/test_spell_abnormal.py
# - 修改 endfield_damage_calculator/tests/test_spell_abnormal_params.py
# - 修改 endfield_damage_calculator/tests/test_streaming_optimizer.py
# - 修改 endfield_damage_calculator/tests/test_top_n_tracker.py
# - 修改 endfield_damage_calculator/tests/test_ui_preferences.py
# - 修改 endfield_damage_calculator/tests/test_unified_data_generator.py
# - 修改 endfield_damage_calculator/tests/test_upload_meta.py
# - 修改 endfield_damage_calculator/tests/test_weapon_dual_special.py
# - 修改 endfield_damage_calculator/tests/test_weapon_panel_layout.py
# - 修改 endfield_damage_calculator/tests/test_weapon_property_display.py
# - 修改 endfield_damage_calculator/tests/test_weapon_skill_selection.py
# - 修改 endfield_damage_calculator/tests/test_weapon_special_fields.py
# - 修改 endfield_damage_calculator/tests/test_weapon_special_level.py
# - 修改 endfield_damage_calculator/tests/test_weapon_special_stack_layers.py
# - 修改 endfield_damage_calculator/tests/test_wiki_sync.py
# - 修改 endfield_damage_calculator/tests/test_window_restore.py
# - 修改 endfield_damage_calculator/tests/test_zone_snapshot.py
# - 变更 endfield_damage_calculator/tests/tools/
# - 修改 tools/bwiki_scout/equipment_wiki.py
# - 修改 tools/bwiki_scout/skill_tables.py
# - 修改 tools/bwiki_scout/weapon_wiki.py
# - 修改 tools/bwiki_scout/wiki_sync.py
# - 修改 tools/fix_search_imports.py
# - 修改 tools/layout_migrate_breaking.py
# - 修改 tools/migrate_calculation_search.py
# --- END UPLOAD_SUMMARY ---
