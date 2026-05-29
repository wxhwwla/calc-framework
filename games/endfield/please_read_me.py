#!/usr/bin/env python3
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
_VERSION = "3.7.9"
_EXE_VERSION = "0.5.0-beta"
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
PROJECT_STRUCTURE = """
项目结构（Python 包目录 games/endfield/）：
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

USAGE_INFO = """
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

FORMULA_INFO = """
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
{"=" * 50}
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
# TITLE: 更新 349 处文件
# BODY:
# - 变更 "docs//344/274/232/350/257/235/346/216/245/347/273/255/346/211/213/345/206/214.md"
# - 变更 "docs//346/223/215/344/275/234/346/214/207/344/273/244/351/233/206.md"
# - 更新文档 CONTEXT.md
# - 更新文档 README.md
# - 修改 build.py
# - 修改 dag_main.py
# - 修改 designer_main.py
# - 更新文档 games/endfield/README.md
# - 修改 games/endfield/__init__.py
# - 修改 games/endfield/build.py
# - 修改 games/endfield/calculation/__init__.py
# - 修改 games/endfield/calculation/core/__init__.py
# - 修改 games/endfield/calculation/core/config.py
# - 修改 games/endfield/calculation/core/curve_baker.py
# - 修改 games/endfield/calculation/core/data_generator.py
# - 修改 games/endfield/calculation/core/parallel_evaluate.py
# - 修改 games/endfield/calculation/core/preview_cache.py
# - 修改 games/endfield/calculation/core/result_cache.py
# - 修改 games/endfield/calculation/core/result_export.py
# - 修改 games/endfield/calculation/core/top_n_tracker.py
# - 修改 games/endfield/calculation/damage/__init__.py
# - 修改 games/endfield/calculation/damage/engine/__init__.py
# - 修改 games/endfield/calculation/damage/engine/calculate.py
# - 修改 games/endfield/calculation/damage/engine/helpers.py
# - 修改 games/endfield/calculation/damage/engine/types.py
# - 修改 games/endfield/calculation/damage/formula.py
# - 修改 games/endfield/calculation/damage/inverse/__init__.py
# - 修改 games/endfield/calculation/damage/inverse/api.py
# - 修改 games/endfield/calculation/damage/inverse/attribute.py
# - 修改 games/endfield/calculation/damage/inverse/fit_core.py
# - 修改 games/endfield/calculation/damage/inverse/skill.py
# - 修改 games/endfield/calculation/damage/types.py
# - 修改 games/endfield/calculation/equipment/__init__.py
# - 修改 games/endfield/calculation/equipment/affix.py
# - 修改 games/endfield/calculation/equipment/prune.py
# - 修改 games/endfield/calculation/equipment/system.py
# - 修改 games/endfield/calculation/loadout/__init__.py
# - 修改 games/endfield/calculation/loadout/attack_eval.py
# - 修改 games/endfield/calculation/loadout/in_memory_optimizer.py
# - 修改 games/endfield/calculation/loadout/optimizer/__init__.py
# - 修改 games/endfield/calculation/loadout/optimizer/catalog.py
# - 修改 games/endfield/calculation/loadout/optimizer/evaluate.py
# - 修改 games/endfield/calculation/loadout/optimizer/plan.py
# - 修改 games/endfield/calculation/loadout/optimizer/search.py
# - 修改 games/endfield/calculation/loadout/optimizer/tasks.py
# - 修改 games/endfield/calculation/loadout/optimizer/types.py
# - 修改 games/endfield/calculation/loadout/slot_search.py
# - 修改 games/endfield/calculation/manual_buff/__init__.py
# - 修改 games/endfield/calculation/manual_buff/model.py
# - 修改 games/endfield/calculation/manual_buff/physical.py
# - 修改 games/endfield/calculation/manual_buff/spell.py
# - 修改 games/endfield/calculation/manual_buff/spell_params.py
# - 修改 games/endfield/calculation/multi_skill/__init__.py
# - 修改 games/endfield/calculation/multi_skill/optimizer/__init__.py
# - 修改 games/endfield/calculation/multi_skill/optimizer/search.py
# - 修改 games/endfield/calculation/multi_skill/optimizer/types.py
# - 调整乘区逻辑 games/endfield/calculation/multiplicative_zones/__init__.py
# - 调整乘区逻辑 games/endfield/calculation/multiplicative_zones/_attribute_zone_bonus.py
# - 调整乘区逻辑 games/endfield/calculation/multiplicative_zones/ability_bonus_calc.py
# - 调整乘区逻辑 games/endfield/calculation/multiplicative_zones/ability_bonus_details.py
# - 调整乘区逻辑 games/endfield/calculation/multiplicative_zones/attribute_zone.py
# - 调整乘区逻辑 games/endfield/calculation/multiplicative_zones/base_zone.py
# - 调整乘区逻辑 games/endfield/calculation/multiplicative_zones/dag/__init__.py
# - 调整乘区逻辑 games/endfield/calculation/multiplicative_zones/dag/__main__.py
# - 调整乘区逻辑 games/endfield/calculation/multiplicative_zones/dag/_subgraph_builders.py
# - 调整乘区逻辑 games/endfield/calculation/multiplicative_zones/dag/adapter.py
# - 调整乘区逻辑 games/endfield/calculation/multiplicative_zones/dag/config.py
# - 调整乘区逻辑 games/endfield/calculation/multiplicative_zones/dag/loader.py
# - 调整乘区逻辑 games/endfield/calculation/multiplicative_zones/final_attack_zone.py
# - 调整乘区逻辑 games/endfield/calculation/multiplicative_zones/zone_manager.py
# - 调整乘区逻辑 games/endfield/calculation/multiplicative_zones/zone_snapshot.py
# - 修改 games/endfield/calculation/search/__init__.py
# - 修改 games/endfield/calculation/search/adapter.py
# - 修改 games/endfield/calculation/search/evaluate/__init__.py
# - 修改 games/endfield/calculation/search/evaluate/context.py
# - 修改 games/endfield/calculation/search/evaluate/multi_skill.py
# - 修改 games/endfield/calculation/search/evaluate/task.py
# - 修改 games/endfield/calculation/search/persist/__init__.py
# - 修改 games/endfield/calculation/search/persist/store.py
# - 修改 games/endfield/calculation/search/plan/__init__.py
# - 修改 games/endfield/calculation/search/plan/controller.py
# - 修改 games/endfield/calculation/search/plan/estimate.py
# - 修改 games/endfield/calculation/search/plan/job.py
# - 修改 games/endfield/calculation/search/run/__init__.py
# - 修改 games/endfield/calculation/search/run/cancel.py
# - 修改 games/endfield/calculation/search/run/mvp.py
# - 修改 games/endfield/calculation/search/run/parallel.py
# - 修改 games/endfield/calculation/search/run/runner.py
# - 修改 games/endfield/calculation/search/run/session.py
# - 修改 games/endfield/calculation/search/run/single_skill.py
# - 修改 games/endfield/calculation/skills/__init__.py
# - 修改 games/endfield/calculation/skills/segments.py
# - 修改 games/endfield/calculation/skills/weapon_selection.py
# - 更新文档 games/endfield/character_weapon_equipment/DATA_README.md
# - 修改 games/endfield/character_weapon_equipment/__init__.py
# - 修改 games/endfield/character_weapon_equipment/character_data/__init__.py
# - 修改 games/endfield/character_weapon_equipment/character_data/add_character.py
# - 更新 characters.json 角色数据
# - 变更 games/endfield/character_weapon_equipment/equipment_data/equipments.json
# - 修改 games/endfield/character_weapon_equipment/weapon_data/__init__.py
# - 修改 games/endfield/character_weapon_equipment/weapon_data/add_weapon.py
# - 修改 games/endfield/character_weapon_equipment/weapon_data/special_fields/__init__.py
# - 修改 games/endfield/character_weapon_equipment/weapon_data/special_fields/codec.py
# - 修改 games/endfield/character_weapon_equipment/weapon_data/special_fields/name_utils.py
# - 修改 games/endfield/character_weapon_equipment/weapon_data/special_fields/runtime_bonus.py
# - 修改 games/endfield/character_weapon_equipment/weapon_data/special_fields/skills_schema.py
# - 修改 games/endfield/character_weapon_equipment/weapon_data/special_fields/slots_io.py
# - 更新 weapons.json 武器数据
# - 修改 games/endfield/dag_main.py
# - 修改 games/endfield/data/__init__.py
# - 修改 games/endfield/data/enemy_params.py
# - 修改 games/endfield/data/equipment_catalog.py
# - 修改 games/endfield/data/equipment_filters.py
# - 修改 games/endfield/data/game_data_facade.py
# - 修改 games/endfield/data/loader.py
# - 修改 games/endfield/data/plugin_registry.py
# - 修改 games/endfield/designer/__init__.py
# - 修改 games/endfield/designer/__main__.py
# - 修改 games/endfield/designer/data_browser_tab.py
# - 修改 games/endfield/designer/data_editor_tab.py
# - 修改 games/endfield/designer/designer_main.py
# - 修改 games/endfield/designer/inverse_tab.py
# - 修改 games/endfield/designer_main.py
# - 修改 games/endfield/editor_app.py
# - 修改 games/endfield/gui_design/__init__.py
# - 修改 games/endfield/gui_design/app/__init__.py
# - 修改 games/endfield/gui_design/app/confirm_refresh.py
# - 修改 games/endfield/gui_design/app/display_request.py
# - 修改 games/endfield/gui_design/app/loadout_evaluation.py
# - 修改 games/endfield/gui_design/app/loadout_preset.py
# - 修改 games/endfield/gui_design/app/loadout_state.py
# - 修改 games/endfield/gui_design/controls/__init__.py
# - 修改 games/endfield/gui_design/controls/enemy/__init__.py
# - 修改 games/endfield/gui_design/controls/enemy/qt_enemy_panel.py
# - 修改 games/endfield/gui_design/controls/enhancement/__init__.py
# - 修改 games/endfield/gui_design/controls/enhancement/qt_dialogs.py
# - 修改 games/endfield/gui_design/controls/manual_buff/__init__.py
# - 修改 games/endfield/gui_design/controls/manual_buff/qt_window.py
# - 修改 games/endfield/gui_design/controls/multi_skill/__init__.py
# - 修改 games/endfield/gui_design/controls/search/__init__.py
# - 修改 games/endfield/gui_design/controls/search/qt_actions.py
# - 修改 games/endfield/gui_design/controls/search/search_estimate_message.py
# - 修改 games/endfield/gui_design/controls/search/search_settings.py
# - 修改 games/endfield/gui_design/designer/data_browser_tab.py
# - 修改 games/endfield/gui_design/designer/data_editor_tab.py
# - 修改 games/endfield/gui_design/designer/designer_main.py
# - 修改 games/endfield/gui_design/designer/inverse_tab.py
# - 修改 games/endfield/gui_design/layout/__init__.py
# - 修改 games/endfield/gui_design/layout/gui_layout.py
# - 修改 games/endfield/gui_design/legal/__init__.py
# - 修改 games/endfield/gui_design/legal/attribution_content.py
# - 修改 games/endfield/gui_design/legal/donation_content.py
# - 修改 games/endfield/gui_design/legal/donation_qt.py
# - 修改 games/endfield/gui_design/panels/__init__.py
# - 修改 games/endfield/gui_design/panels/selection/__init__.py
# - 修改 games/endfield/gui_design/panels/selection/qt_ability_panel.py
# - 修改 games/endfield/gui_design/panels/selection/qt_panel.py
# - 修改 games/endfield/gui_design/panels/selection/qt_panel_getters_mixin.py
# - 修改 games/endfield/gui_design/panels/selection/qt_subpanels.py
# - 修改 games/endfield/gui_design/panels/special_ability/__init__.py
# - 修改 games/endfield/gui_design/presentation/__init__.py
# - 修改 games/endfield/gui_design/presentation/damage_snapshot.py
# - 修改 games/endfield/gui_design/presentation/display/__init__.py
# - 修改 games/endfield/gui_design/presentation/display/character.py
# - 修改 games/endfield/gui_design/presentation/display/format.py
# - 修改 games/endfield/gui_design/presentation/display/single_hit.py
# - 修改 games/endfield/gui_design/presentation/display/skill_resolve.py
# - 修改 games/endfield/gui_design/presentation/display_lines.py
# - 修改 games/endfield/gui_design/presentation/preview/__init__.py
# - 修改 games/endfield/gui_design/presentation/preview/multi_skill.py
# - 修改 games/endfield/gui_design/presentation/preview/single_skill.py
# - 修改 games/endfield/gui_design/presentation/preview_lines.py
# - 修改 games/endfield/gui_design/presentation/search_results_lines.py
# - 修改 games/endfield/gui_design/presentation/total_damage_panel.py
# - 修改 games/endfield/gui_design/shared/__init__.py
# - 修改 games/endfield/gui_design/shared/calc_history.py
# - 修改 games/endfield/gui_design/shared/calc_mode_labels.py
# - 修改 games/endfield/gui_design/shared/damage_visualization.py
# - 修改 games/endfield/gui_design/shared/display_view/qt_columns.py
# - 修改 games/endfield/gui_design/shared/preset_batch_compare.py
# - 修改 games/endfield/gui_design/shared/ui_preferences.py
# - 修改 games/endfield/gui_design/shared/weapon_display_text.py
# - 修改 games/endfield/gui_design/shell/__init__.py
# - 修改 games/endfield/gui_design/shell/qt_app.py
# - 修改 games/endfield/gui_design/shell/qt_app_confirm_mixin.py
# - 修改 games/endfield/gui_design/shell/qt_app_dialog_mixin.py
# - 修改 games/endfield/gui_design/shell/qt_app_search_mixin.py
# - 修改 games/endfield/gui_design/shell/qt_control_dock.py
# - 修改 games/endfield/gui_design/shell/qt_control_dock_builders.py
# - 修改 games/endfield/gui_design/shell/qt_control_dock_widgets.py
# - 修改 games/endfield/gui_design/shell/qt_factory.py
# - 修改 games/endfield/gui_design/shell/qt_worker.py
# - 修改 games/endfield/legal/__init__.py
# - 修改 games/endfield/legal/attribution_content.py
# - 修改 games/endfield/legal/donation_content.py
# - 修改 games/endfield/legal/donation_qt.py
# - 变更 games/endfield/legal/wechat_reward.jpg
# - 修改 games/endfield/main.py
# - 修改 games/endfield/please_read_me.py
# - 更新文档 games/endfield/plugins/README.md
# - 变更 games/endfield/pyproject.toml
# - 修改 games/endfield/release_bundle/__init__.py
# - 修改 games/endfield/release_bundle/platform_win32_patch.py
# - 修改 games/endfield/release_bundle/pyinstaller_entry.py
# - 修改 games/endfield/release_bundle/release_layout.py
# - 修改 games/endfield/scripts/__init__.py
# - 修改 games/endfield/scripts/build.py
# - 修改 games/endfield/scripts/editor_app.py
# - 修改 games/endfield/scripts/inverse_cli.py
# - 修改 games/endfield/scripts/inverse_formula_gui.py
# - 修改 games/endfield/scripts/seed_characters.py
# - 修改 games/endfield/scripts/seed_weapons.py
# - 修改 games/endfield/tests/calculation/core/test_result_cache.py
# - 修改 games/endfield/tests/calculation/damage/engine/test_calculation.py
# - 修改 games/endfield/tests/calculation/damage/engine/test_damage_engine.py
# - 修改 games/endfield/tests/calculation/damage/engine/test_damage_types.py
# - 修改 games/endfield/tests/calculation/damage/engine/test_damage_visualization.py
# - 修改 games/endfield/tests/calculation/damage/engine/test_decimal_scaling.py
# - 修改 games/endfield/tests/calculation/damage/engine/test_manual_buff.py
# - 修改 games/endfield/tests/calculation/damage/engine/test_scaling_mode.py
# - 修改 games/endfield/tests/calculation/damage/zones/test_calc_chain_naming_compat.py
# - 修改 games/endfield/tests/calculation/damage/zones/test_curve_baker.py
# - 修改 games/endfield/tests/calculation/damage/zones/test_dag_adapter.py
# - 修改 games/endfield/tests/calculation/damage/zones/test_damage_snapshot.py
# - 修改 games/endfield/tests/calculation/damage/zones/test_damage_snapshot_manual_buff.py
# - 修改 games/endfield/tests/calculation/damage/zones/test_inverse_refactored.py
# - 修改 games/endfield/tests/calculation/damage/zones/test_result_export.py
# - 修改 games/endfield/tests/calculation/damage/zones/test_zone_snapshot.py
# - 修改 games/endfield/tests/calculation/equipment/test_equipment_affix.py
# - 修改 games/endfield/tests/calculation/equipment/test_equipment_catalog.py
# - 修改 games/endfield/tests/calculation/equipment/test_equipment_filters.py
# - 修改 games/endfield/tests/calculation/equipment/test_equipment_prune.py
# - 修改 games/endfield/tests/calculation/equipment/test_equipment_sync.py
# - 修改 games/endfield/tests/calculation/equipment/test_equipment_system.py
# - 修改 games/endfield/tests/calculation/loadout/optimizer/test_fixed_loadout_selection.py
# - 修改 games/endfield/tests/calculation/loadout/optimizer/test_loadout_optimizer.py
# - 修改 games/endfield/tests/calculation/loadout/optimizer/test_loadout_varying_slots.py
# - 修改 games/endfield/tests/calculation/loadout/optimizer/test_streaming_optimizer.py
# - 修改 games/endfield/tests/calculation/loadout/state/test_loadout_attack_eval.py
# - 修改 games/endfield/tests/calculation/loadout/state/test_loadout_evaluation.py
# - 修改 games/endfield/tests/calculation/loadout/state/test_loadout_preset.py
# - 修改 games/endfield/tests/calculation/loadout/state/test_loadout_state.py
# - 修改 games/endfield/tests/calculation/loadout/state/test_weapon_skill_selection.py
# - 修改 games/endfield/tests/calculation/manual_buff/test_abnormal_manual_buff.py
# - 修改 games/endfield/tests/calculation/manual_buff/test_manual_buff_model.py
# - 修改 games/endfield/tests/calculation/manual_buff/test_spell_abnormal.py
# - 修改 games/endfield/tests/calculation/manual_buff/test_spell_abnormal_params.py
# - 修改 games/endfield/tests/calculation/multi_skill/test_multi_skill_counts.py
# - 修改 games/endfield/tests/calculation/multi_skill/test_multi_skill_optimizer.py
# - 修改 games/endfield/tests/calculation/search/plan/single_skill/test_search_settings.py
# - 修改 games/endfield/tests/calculation/search/plan/single_skill/test_single_skill_search_job.py
# - 修改 games/endfield/tests/calculation/search/plan/single_skill/test_single_skill_search_preview.py
# - 修改 games/endfield/tests/calculation/search/plan/test_search_controller.py
# - 修改 games/endfield/tests/calculation/search/plan/test_search_controls.py
# - 修改 games/endfield/tests/calculation/search/plan/test_search_error_binding.py
# - 修改 games/endfield/tests/calculation/search/plan/test_search_estimate.py
# - 修改 games/endfield/tests/calculation/search/plan/test_search_export_paths.py
# - 修改 games/endfield/tests/calculation/search/plan/test_search_format.py
# - 修改 games/endfield/tests/calculation/search/run/test_multi_skill_full_search.py
# - 修改 games/endfield/tests/calculation/search/run/test_mvp_pipeline.py
# - 修改 games/endfield/tests/calculation/search/run/test_parallel_evaluate.py
# - 修改 games/endfield/tests/calculation/search/run/test_search_persistence.py
# - 修改 games/endfield/tests/calculation/search/run/test_search_results_view.py
# - 修改 games/endfield/tests/calculation/search/run/test_search_runner.py
# - 修改 games/endfield/tests/calculation/search/run/test_search_session.py
# - 修改 games/endfield/tests/calculation/search/run/test_single_skill_search_runner.py
# - 修改 games/endfield/tests/calculation/search/run/test_top_n_tracker.py
# - 修改 games/endfield/tests/calculation/skills/test_skill_segments.py
# - 修改 games/endfield/tests/calculation/skills/test_skill_tables_damage_type.py
# - 修改 games/endfield/tests/character_weapon_equipment/test_add_character.py
# - 修改 games/endfield/tests/character_weapon_equipment/test_add_weapon.py
# - 修改 games/endfield/tests/character_weapon_equipment/test_weapon_dual_special.py
# - 修改 games/endfield/tests/character_weapon_equipment/test_weapon_property_display.py
# - 修改 games/endfield/tests/character_weapon_equipment/test_weapon_special_fields.py
# - 修改 games/endfield/tests/character_weapon_equipment/test_weapon_special_level.py
# - 修改 games/endfield/tests/character_weapon_equipment/test_weapon_special_stack_layers.py
# - 修改 games/endfield/tests/conftest.py
# - 修改 games/endfield/tests/data/test_enemy_params.py
# - 修改 games/endfield/tests/data/test_game_data_contract.py
# - 修改 games/endfield/tests/data/test_game_data_facade.py
# - 修改 games/endfield/tests/data/test_gui_data_load.py
# - 修改 games/endfield/tests/data/test_loader_errors.py
# - 修改 games/endfield/tests/data/test_pack_data_paths.py
# - 修改 games/endfield/tests/data/test_plugin_registry.py
# - 修改 games/endfield/tests/data/test_unified_data_generator.py
# - 修改 games/endfield/tests/framework/test_endfield_dag_integration.py
# - 修改 games/endfield/tests/gui_design/app/test_confirm_orchestrator.py
# - 修改 games/endfield/tests/gui_design/app/test_confirm_refresh.py
# - 修改 games/endfield/tests/gui_design/app/test_confirm_selection_skill_levels.py
# - 修改 games/endfield/tests/gui_design/app/test_confirm_selection_state.py
# - 修改 games/endfield/tests/gui_design/controls/test_frozen_search_export_paths.py
# - 修改 games/endfield/tests/gui_design/presentation/test_display_lines_module.py
# - 修改 games/endfield/tests/gui_design/presentation/test_multi_skill_search_preview.py
# - 修改 games/endfield/tests/gui_design/presentation/test_preview_cache.py
# - 修改 games/endfield/tests/gui_design/presentation/test_property_display_cache.py
# - 修改 games/endfield/tests/gui_design/presentation/test_property_display_lines.py
# - 修改 games/endfield/tests/gui_design/presentation/test_single_hit_preview.py
# - 修改 games/endfield/tests/gui_design/shared/test_calc_history.py
# - 修改 games/endfield/tests/gui_design/shared/test_calc_mode_labels.py
# - 修改 games/endfield/tests/gui_design/shared/test_operation_log.py
# - 修改 games/endfield/tests/gui_design/shared/test_preset_batch_compare.py
# - 修改 games/endfield/tests/gui_design/shared/test_ui_preferences.py
# - 修改 games/endfield/tests/gui_design/shell/test_gui_layout_contract.py
# - 修改 games/endfield/tests/gui_design/shell/test_weapon_panel_layout.py
# - 修改 games/endfield/tests/repo/test_build_watchdog.py
# - 修改 games/endfield/tests/repo/test_config.py
# - 修改 games/endfield/tests/repo/test_coverage_boost_misc.py
# - 修改 games/endfield/tests/repo/test_gitignore_contract.py
# - 修改 games/endfield/tests/repo/test_legal_attribution.py
# - 修改 games/endfield/tests/repo/test_optional_deps.py
# - 修改 games/endfield/tests/repo/test_readme_layers.py
# - 修改 games/endfield/tests/repo/test_release_layout.py
# - 修改 games/endfield/tests/repo/test_repo_layout.py
# - 修改 games/endfield/tests/repo/test_repo_release_layout.py
# - 修改 games/endfield/tests/test_qt_imports.py
# - 修改 games/endfield/tests/tools/test_bwiki_scout.py
# - 修改 games/endfield/tests/tools/test_github_upload_signing.py
# - 修改 games/endfield/tests/tools/test_import_targets.py
# - 修改 games/endfield/tests/tools/test_migrate_weapon_skills_schema_tool.py
# - 修改 games/endfield/tests/tools/test_upload_meta.py
# - 修改 games/endfield/tests/tools/test_wiki_sync.py
# - 修改 games/endfield/tests/utils/test_gui_window.py
# - 变更 games/endfield/ui_preferences.json
# - 修改 games/endfield/upload_meta.py
# - 修改 games/endfield/utils/__init__.py
# - 修改 games/endfield/utils/app_paths.py
# - 修改 games/endfield/utils/gui_chart_theme.py
# - 修改 games/endfield/utils/gui_fonts.py
# - 修改 games/endfield/utils/gui_window.py
# - 修改 games/endfield/utils/operation_log.py
# - 修改 games/endfield/utils/optional_deps.py
# - 修改 games/endfield/utils/path_utils.py
# - 修改 games/endfield/utils/platform_win32_patch.py
# - 修改 games/endfield/utils/search_format.py
# - 变更 games/framework/src/calc_framework/configs/endfield_full.dag.json
# - 修改 github_upload_module.py
# - 修改 main.py
# - 修改 tools/bwiki_scout/backfill_weapon_max_stack.py
# - 修改 tools/bwiki_scout/config.py
# - 修改 tools/bwiki_scout/migrate_weapon_special_json.py
# - 修改 tools/bwiki_scout/pkg_bootstrap.py
# - 修改 tools/bwiki_scout/skill_tables.py
# - 修改 tools/bwiki_scout/sync_all.py
# - 修改 tools/bwiki_scout/sync_equipments.py
# - 修改 tools/bwiki_scout/sync_operators.py
# - 修改 tools/bwiki_scout/sync_weapons.py
# - 修改 tools/bwiki_scout/weapon_wiki.py
# - 修改 tools/check_layout.py
# - 修改 tools/check_optional_deps.py
# --- END UPLOAD_SUMMARY ---
