#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""

终末地伤害计算小工具 - 项目说明文档



项目简介：

    本工具是一个基于 PySide6 开发的伤害计算辅助工具，用于游戏《明日方舟：终末地》。

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

_VERSION = "3.18.10"

_EXE_VERSION = "0.6.0-beta"

# ==============================================================



# ==================== GitHub 上传流程（必读） ====================

UPLOAD_WORKFLOW = """

GitHub 上传与版本号（仓库根目录执行: python github_upload_module.py）



1. 版本分工

   - _VERSION：上传脚本在有「业务改动」并 push 成功时自动递增（第三位 +1 为默认）。commit 消息使用此版本。

   - _EXE_VERSION：GUI 窗口标题与 exe 版本号，仅你手动修改。**git 标签使用此版本**（`--tag` 时）。

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

       v3.11.21: 一句话标题



       - 修改 xxx

       - 更新 weapons.json ...

   - push 成功后：脚本删除该总结块（_VERSION 保留）。

   - push 失败：总结块保留，版本不回滚；修好网络后可只 push 或 --no-bump 再传。



5. 发布标签（Tag）

   - `python github_upload_module.py --tag` 会创建并推送 git 标签。

   - 标签版本使用 **`_EXE_VERSION`**（如 `v0.6.0-beta`），触发 GitHub Actions 自动构建发行版。

   - 确保标签被 SSH 签名（需配置签名密钥并添加到 GitHub Signing keys）。



6. 常用命令

   python github_upload_module.py

   python github_upload_module.py --minor

   python github_upload_module.py --no-bump

   python github_upload_module.py --tag         # 正常推送 + 创建发行版标签

   python github_upload_module.py --no-bump --tag   # 不 bump 版本 + 创建标签



7. 提交签名（推荐，GitHub Verified）

   - 若已配置 commit.gpgsign 和 SSH 签名密钥，commit 和 tag 均会自动签名。

   - 未配置时脚本会打印设置提示；见 docs/操作指令集.md §1.5。



8. 从远程覆盖本地（危险，勿误点）

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

    ├── gui/                       # GUI（五列 + 底栏）

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

    - PySide6（GUI框架）

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
    """获取项目版本号。"""
    return _VERSION





def get_exe_version() -> str:
    """获取 EXE 版本号。"""
    return _EXE_VERSION





def get_full_intro() -> str:
    """获取完整的项目介绍文档。"""
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
    """显示项目帮助信息。"""
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





import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _path_setup import ensure_root
ensure_root()

if __name__ == "__main__":

    show_help()

# --- UPLOAD_SUMMARY ---
# TITLE: 更新 266 处文件
# BODY:
# - 变更 "docs//344/274/232/350/257/235/346/216/245/347/273/255/346/211/213/345/206/214.md"
# - 修改 batch_docstring.py
# - 修改 framework/src/calc_framework/config/adapter.py
# - 修改 framework/src/calc_framework/config/file_watcher.py
# - 修改 framework/src/calc_framework/config/manager.py
# - 修改 framework/src/calc_framework/config/watcher.py
# - 修改 framework/src/calc_framework/dag/engine.py
# - 修改 framework/src/calc_framework/dag/sandbox.py
# - 修改 framework/src/calc_framework/dag/serializer.py
# - 修改 framework/src/calc_framework/dag/state.py
# - 修改 framework/src/calc_framework/data/schema.py
# - 修改 framework/src/calc_framework/editor/editor.py
# - 修改 framework/src/calc_framework/graph_editor/graph_editor_widget.py
# - 修改 framework/src/calc_framework/graph_editor/help_dialog.py
# - 修改 framework/src/calc_framework/graph_editor/package_manager.py
# - 修改 framework/src/calc_framework/graph_editor/ports.py
# - 修改 framework/src/calc_framework/graph_editor/serializer.py
# - 修改 framework/src/calc_framework/graph_editor/wire.py
# - 修改 framework/src/calc_framework/inverse/base.py
# - 修改 framework/src/calc_framework/inverse/registry.py
# - 修改 framework/src/calc_framework/logging.py
# - 修改 framework/src/calc_framework/plugin/base.py
# - 修改 framework/src/calc_framework/plugin/builtin.py
# - 修改 framework/src/calc_framework/plugin/registry.py
# - 修改 framework/src/calc_framework/publish/catalog.py
# - 修改 framework/src/calc_framework/search/cancel.py
# - 修改 framework/src/calc_framework/search/parallel.py
# - 修改 framework/src/calc_framework/search/persist.py
# - 修改 framework/src/calc_framework/search/session.py
# - 修改 framework/src/calc_framework/search/tracker.py
# - 修改 framework/src/calc_framework/ui/controls.py
# - 修改 framework/src/calc_framework/ui/launcher/runtime.py
# - 修改 framework/src/calc_framework/ui/layout.py
# - 修改 framework/src/calc_framework/ui/theme.py
# - 修改 framework/src/calc_framework/ui/viewer_plugin_manager.py
# - 修改 framework/tests/benchmark/test_dag_benchmark.py
# - 修改 games/__init__.py
# - 修改 games/arknights/calc/dag_adapter/adapter.py
# - 修改 games/arknights/calc/dag_adapter/loader.py
# - 修改 games/arknights/calc/skill_parser.py
# - 修改 games/arknights/gui/ArknightsApp.py
# - 修改 games/arknights/gui/ArknightsDamageApp.py
# - 修改 games/arknights/gui/__init__.py
# - 修改 games/arknights/operator_catalog.py
# - 更新文档 games/endfield/README.md
# - 修改 games/endfield/_replace_imports.py
# - 修改 games/endfield/calc/character_stats.py
# - 修改 games/endfield/calc/core/result_cache.py
# - 修改 games/endfield/calc/core/result_export.py
# - 修改 games/endfield/calc/dag_adapter/_subgraph_builders.py
# - 修改 games/endfield/calc/dag_adapter/adapter.py
# - 修改 games/endfield/calc/dag_adapter/config.py
# - 修改 games/endfield/calc/dag_adapter/loader.py
# - 修改 games/endfield/calc/damage/abnormal_attached.py
# - 修改 games/endfield/calc/damage/corrosion.py
# - 修改 games/endfield/calc/damage/engine/calculate.py
# - 修改 games/endfield/calc/damage/execute.py
# - 修改 games/endfield/calc/damage/imbalance.py
# - 修改 games/endfield/calc/damage/physical_abnormal_state.py
# - 修改 games/endfield/calc/equipment/affix.py
# - 修改 games/endfield/calc/equipment/prune.py
# - 修改 games/endfield/calc/equipment/system.py
# - 修改 games/endfield/calc/loadout/in_memory_optimizer.py
# - 修改 games/endfield/calc/loadout/slot_search.py
# - 修改 games/endfield/calc/manual_buff/abnormal_matrix.py
# - 修改 games/endfield/calc/manual_buff/consumable_presets.py
# - 修改 games/endfield/calc/manual_buff/model.py
# - 修改 games/endfield/calc/manual_buff/physical.py
# - 修改 games/endfield/calc/manual_buff/spell.py
# - 修改 games/endfield/calc/multi_skill/optimizer/types.py
# - 调整乘区逻辑 games/endfield/calc/multiplicative_zones/_attribute_zone_bonus.py
# - 调整乘区逻辑 games/endfield/calc/multiplicative_zones/ability_bonus_calc.py
# - 调整乘区逻辑 games/endfield/calc/multiplicative_zones/ability_bonus_details.py
# - 调整乘区逻辑 games/endfield/calc/multiplicative_zones/attribute_zone.py
# - 调整乘区逻辑 games/endfield/calc/multiplicative_zones/base_zone.py
# - 调整乘区逻辑 games/endfield/calc/multiplicative_zones/final_attack_zone.py
# - 修改 games/endfield/calc/search/adapter.py
# - 修改 games/endfield/calc/search/evaluate/multi_skill.py
# - 修改 games/endfield/calc/search/evaluate/task.py
# - 修改 games/endfield/calc/search/persist/store.py
# - 修改 games/endfield/calc/search/run/parallel.py
# - 修改 games/endfield/calc/search/run/runner.py
# - 修改 games/endfield/calc/search/run/session.py
# - 修改 games/endfield/calc/skills/segments.py
# - 修改 games/endfield/calc/skills/weapon_selection.py
# - 修改 games/endfield/data_loading/enemy_eval_params.py
# - 修改 games/endfield/data_loading/enemy_params.py
# - 修改 games/endfield/data_loading/equipment_filters.py
# - 修改 games/endfield/data_loading/loader.py
# - 修改 games/endfield/data_loading/plugin_registry.py
# - 修改 games/endfield/data_loading/web_loadout_bridge.py
# - 修改 games/endfield/gui/app/display_request.py
# - 修改 games/endfield/gui/app/loadout_evaluation.py
# - 修改 games/endfield/gui/app/loadout_preset.py
# - 修改 games/endfield/gui/app/loadout_state.py
# - 修改 games/endfield/gui/controls/enemy/qt_enemy_panel.py
# - 修改 games/endfield/gui/controls/enhancement/qt_dialogs.py
# - 修改 games/endfield/gui/controls/manual_buff/qt_window.py
# - 修改 games/endfield/gui/controls/ocr/__init__.py
# - 修改 games/endfield/gui/controls/search/qt_actions.py
# - 修改 games/endfield/gui/controls/search/qt_search_browser.py
# - 修改 games/endfield/gui/controls/survival/qt_survival_dialog.py
# - 修改 games/endfield/gui/designer/data_browser_tab.py
# - 修改 games/endfield/gui/designer/data_editor_tab.py
# - 修改 games/endfield/gui/designer/designer_main.py
# - 修改 games/endfield/gui/designer/inverse_tab.py
# - 修改 games/endfield/gui/endfield_app.py
# - 修改 games/endfield/gui/legal/attribution_content.py
# - 修改 games/endfield/gui/panels/selection/qt_ability_panel.py
# - 修改 games/endfield/gui/panels/selection/qt_panel.py
# - 修改 games/endfield/gui/panels/selection/qt_panel_getters_mixin.py
# - 修改 games/endfield/gui/panels/selection/qt_subpanels.py
# - 修改 games/endfield/gui/presentation/damage_snapshot.py
# - 修改 games/endfield/gui/presentation/display/single_hit.py
# - 修改 games/endfield/gui/presentation/preview/multi_skill.py
# - 修改 games/endfield/gui/presentation/preview/single_skill.py
# - 修改 games/endfield/gui/presentation/search_results_lines.py
# - 修改 games/endfield/gui/presentation/total_damage_panel.py
# - 修改 games/endfield/gui/shared/calc_history.py
# - 修改 games/endfield/gui/shared/damage_visualization.py
# - 修改 games/endfield/gui/shared/display_view/qt_columns.py
# - 修改 games/endfield/gui/shared/preset_batch_compare.py
# - 修改 games/endfield/gui/shared/ui_preferences.py
# - 修改 games/endfield/gui/shell/__init__.py
# - 修改 games/endfield/gui/shell/qt_app.py
# - 修改 games/endfield/gui/shell/qt_app_confirm_mixin.py
# - 修改 games/endfield/gui/shell/qt_app_dialog_mixin.py
# - 修改 games/endfield/gui/shell/qt_app_search_mixin.py
# - 修改 games/endfield/gui/shell/qt_control_dock.py
# - 修改 games/endfield/gui/shell/qt_control_dock_builders.py
# - 修改 games/endfield/gui/shell/qt_control_dock_widgets.py
# - 修改 games/endfield/gui/shell/qt_worker.py
# - 修改 games/endfield/tests/calculation/damage/engine/test_damage_visualization.py
# - 修改 games/endfield/tests/calculation/search/plan/single_skill/test_search_settings.py
# - 修改 games/endfield/tests/gui_design/controls/search/test_qt_search_browser_dialog.py
# - 修改 games/endfield/tests/gui_design/presentation/display/test_display_lines_module.py
# - 修改 games/endfield/tests/test_qt_imports.py
# - 修改 games/endfield/upload_meta.py
# - 修改 installer/build_installer.py
# - 修改 scan_docstrings.py
# - 修改 scripts/devtool.py
# - 修改 scripts/github_download_module.py
# - 修改 scripts/github_upload_module.py
# - 修改 scripts/main_build.py
# - 修改 scripts/main_launcher.py
# - 修改 scripts/please_read_me.py
# - 修改 scripts/upload_meta.py
# - 修改 tools/__init__.py
# - 修改 tools/arknights_scout/api.py
# - 修改 tools/arknights_scout/gallery.py
# - 修改 tools/arknights_scout/json_scan.py
# - 修改 tools/arknights_scout/local_schema.py
# - 修改 tools/arknights_scout/names.py
# - 修改 tools/arknights_scout/parse_operator.py
# - 修改 tools/arknights_scout/report.py
# - 修改 tools/arknights_scout/scout.py
# - 修改 tools/arknights_scout/storage.py
# - 修改 tools/arknights_scout/sync_operators.py
# - 修改 tools/bwiki_scout/__init__.py
# - 修改 tools/bwiki_scout/api.py
# - 修改 tools/bwiki_scout/backfill_weapon_max_stack.py
# - 修改 tools/bwiki_scout/bump_data_version.py
# - 修改 tools/bwiki_scout/compare_stats.py
# - 修改 tools/bwiki_scout/detail_levels.py
# - 修改 tools/bwiki_scout/equipment_sync.py
# - 修改 tools/bwiki_scout/equipment_wiki.py
# - 修改 tools/bwiki_scout/gallery.py
# - 修改 tools/bwiki_scout/local_schema.py
# - 修改 tools/bwiki_scout/migrate_weapon_special_json.py
# - 修改 tools/bwiki_scout/parse_draft.py
# - 修改 tools/bwiki_scout/pkg_bootstrap.py
# - 修改 tools/bwiki_scout/report.py
# - 修改 tools/bwiki_scout/scout.py
# - 修改 tools/bwiki_scout/seed_persist.py
# - 修改 tools/bwiki_scout/skill_tables.py
# - 修改 tools/bwiki_scout/storage.py
# - 修改 tools/bwiki_scout/sync_all.py
# - 修改 tools/bwiki_scout/sync_equipments.py
# - 修改 tools/bwiki_scout/sync_operators.py
# - 修改 tools/bwiki_scout/sync_weapons.py
# - 修改 tools/bwiki_scout/weapon_wiki.py
# - 修改 tools/bwiki_scout/wiki_sync.py
# - 修改 tools/check_code_origin.py
# - 修改 tools/check_layout.py
# - 修改 tools/check_optional_deps.py
# - 修改 tools/data_pipeline/cli.py
# - 修改 tools/data_pipeline/diff.py
# - 修改 tools/data_pipeline/readers/__init__.py
# - 修改 tools/data_pipeline/readers/csv_reader.py
# - 修改 tools/data_pipeline/transformers/__init__.py
# - 修改 tools/data_pipeline/transformers/from_legacy_endfield.py
# - 修改 tools/data_pipeline/transformers/to_standard.py
# - 修改 tools/data_pipeline/validators/__init__.py
# - 修改 tools/data_pipeline/validators/schema_check.py
# - 修改 tools/data_sandbox/reporter.py
# - 修改 tools/data_sandbox/sandbox.py
# - 修改 tools/data_sandbox/tester.py
# - 修改 tools/data_sandbox/validator.py
# - 修改 tools/designer/app.py
# - 修改 tools/designer/data_editor/__init__.py
# - 修改 tools/designer/data_editor/panel.py
# - 修改 tools/designer/data_editor/profiles.py
# - 修改 tools/designer/exporter.py
# - 修改 tools/designer/layout_editor/__init__.py
# - 修改 tools/designer/layout_editor/canvas.py
# - 修改 tools/designer/theme_editor/__init__.py
# - 修改 tools/designer/theme_editor/panel.py
# - 修改 tools/endfield_designer/__init__.py
# - 修改 tools/endfield_designer/data_browser_tab.py
# - 修改 tools/endfield_designer/data_editor_tab.py
# - 修改 tools/endfield_designer/designer_main.py
# - 修改 tools/endfield_designer/inverse_tab.py
# - 修改 tools/endfield_designer/seed_tab.py
# - 修改 tools/endfield_scripts/__init__.py
# - 修改 tools/endfield_scripts/build.py
# - 修改 tools/endfield_scripts/editor_app.py
# - 修改 tools/endfield_scripts/inverse_formula_gui.py
# - 修改 tools/endfield_scripts/seed_characters.py
# - 修改 tools/endfield_scripts/seed_weapons.py
# - 修改 tools/export_sample_calcpacks.py
# - 修改 tools/framework_publish.py
# - 修改 tools/gen_architecture_review_html.py
# - 修改 tools/generate_endfield_zone_package.py
# - 修改 tools/migrate_weapon_skills_schema.py
# - 修改 tools/ocr/__init__.py
# - 修改 tools/ocr/cli.py
# - 修改 tools/ocr/collector.py
# - 修改 tools/ocr/detector.py
# - 修改 tools/ocr/download_models.py
# - 修改 tools/ocr/label.py
# - 修改 tools/ocr/mapper.py
# - 修改 tools/ocr/recognizer.py
# - 修改 tools/ocr/train.py
# - 修改 tools/plugin_pack.py
# - 修改 tools/rename_pkg.py
# - 修改 tools/replace_adapters_imports.py
# - 修改 tools/replace_docs.py
# - 修改 tools/replace_paths.py
# - 修改 tools/run_scancode.py
# - 修改 tools/scaffold.py
# - 修改 tools/sync_hub_catalog.py
# - 修改 tools/validate_layout_sync.py
# - 修改 web/backend/api/adapter_assets.py
# - 修改 web/backend/api/adapters.py
# - 修改 web/backend/api/arknights.py
# - 修改 web/backend/api/compute.py
# - 修改 web/backend/api/contribute.py
# - 修改 web/backend/api/data.py
# - 修改 web/backend/api/data_mutations.py
# - 修改 web/backend/api/data_profiles.py
# - 修改 web/backend/api/download_client.py
# - 修改 web/backend/api/history.py
# - 修改 web/backend/api/hub.py
# - 修改 web/backend/api/layout.py
# - 修改 web/backend/api/loadout_schemas.py
# - 修改 web/backend/api/manual_buff.py
# - 修改 web/backend/api/ocr.py
# - 修改 web/backend/api/pack.py
# - 修改 web/backend/api/persistent_store.py
# - 修改 web/backend/api/search.py
# - 修改 web/backend/api/survival.py
# - 修改 web/backend/hub/storage.py
# - 修改 web/backend/main.py
# - 修改 web/backend/run_packaged_main.py
# - 修改 web/backend/tests/test_arknights_data_fallback.py
# - 修改 web/backend/tests/test_enemy_choices_api.py
# --- END UPLOAD_SUMMARY ---
