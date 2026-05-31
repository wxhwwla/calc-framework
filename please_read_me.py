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

_VERSION = "3.13.0"

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
# TITLE: 更新 798 处文件
# BODY:
# - 变更 "docs//344/273/243/347/240/201/347/273/223/346/236/204/350/247/204/350/214/203.md"
# - 变更 "docs//344/274/232/350/257/235/346/216/245/347/273/255/346/211/213/345/206/214.md"
# - 变更 "docs//346/225/260/346/215/256/346/235/245/346/272/220/344/270/216/350/256/270/345/217/257.md"
# - 变更 "docs//346/241/206/346/236/266/351/200/202/351/205/215/346/226/260/346/270/270/346/210/217/346/214/207/345/215/227.md"
# - 变更 "docs//351/241/271/347/233/256/347/233/256/346/240/207.md"
# - 变更 .cursorrules
# - 变更 .github/workflows/ci.yml
# - 变更 .github/workflows/layout-sync.yml
# - 变更 .github/workflows/release.yml
# - 修改 _rename_pkg.py
# - 修改 _replace_adapters_imports.py
# - 修改 _replace_docs.py
# - 修改 _replace_paths.py
# - 修改 adapters/endfield/calc/core/config.py
# - 修改 adapters/endfield/calc/core/curve_baker.py
# - 修改 adapters/endfield/calc/core/data_generator.py
# - 修改 adapters/endfield/calc/core/parallel_evaluate.py
# - 修改 adapters/endfield/calc/core/preview_cache.py
# - 修改 adapters/endfield/calc/core/result_cache.py
# - 修改 adapters/endfield/calc/core/result_export.py
# - 修改 adapters/endfield/calc/core/top_n_tracker.py
# - 修改 adapters/endfield/calc/damage/engine/calculate.py
# - 修改 adapters/endfield/calc/damage/engine/helpers.py
# - 修改 adapters/endfield/calc/damage/engine/types.py
# - 修改 adapters/endfield/calc/damage/formula.py
# - 修改 adapters/endfield/calc/damage/inverse/api.py
# - 修改 adapters/endfield/calc/damage/inverse/attribute.py
# - 修改 adapters/endfield/calc/damage/inverse/fit_core.py
# - 修改 adapters/endfield/calc/damage/inverse/skill.py
# - 修改 adapters/endfield/calc/damage/types.py
# - 修改 adapters/endfield/calc/equipment/affix.py
# - 修改 adapters/endfield/calc/equipment/prune.py
# - 修改 adapters/endfield/calc/equipment/system.py
# - 修改 adapters/endfield/calc/loadout/attack_eval.py
# - 修改 adapters/endfield/calc/loadout/in_memory_optimizer.py
# - 修改 adapters/endfield/calc/loadout/optimizer/catalog.py
# - 修改 adapters/endfield/calc/loadout/optimizer/evaluate.py
# - 修改 adapters/endfield/calc/loadout/optimizer/plan.py
# - 修改 adapters/endfield/calc/loadout/optimizer/search.py
# - 修改 adapters/endfield/calc/loadout/optimizer/tasks.py
# - 修改 adapters/endfield/calc/loadout/optimizer/types.py
# - 修改 adapters/endfield/calc/loadout/slot_search.py
# - 修改 adapters/endfield/calc/manual_buff/model.py
# - 修改 adapters/endfield/calc/manual_buff/physical.py
# - 修改 adapters/endfield/calc/manual_buff/spell.py
# - 修改 adapters/endfield/calc/manual_buff/spell_params.py
# - 修改 adapters/endfield/calc/multi_skill/optimizer/search.py
# - 修改 adapters/endfield/calc/multi_skill/optimizer/types.py
# - 调整乘区逻辑 adapters/endfield/calc/multiplicative_zones/_attribute_zone_bonus.py
# - 调整乘区逻辑 adapters/endfield/calc/multiplicative_zones/ability_bonus_calc.py
# - 调整乘区逻辑 adapters/endfield/calc/multiplicative_zones/ability_bonus_details.py
# - 调整乘区逻辑 adapters/endfield/calc/multiplicative_zones/attribute_zone.py
# - 调整乘区逻辑 adapters/endfield/calc/multiplicative_zones/base_zone.py
# - 调整乘区逻辑 adapters/endfield/calc/multiplicative_zones/dag/__main__.py
# - 调整乘区逻辑 adapters/endfield/calc/multiplicative_zones/dag/_subgraph_builders.py
# - 调整乘区逻辑 adapters/endfield/calc/multiplicative_zones/dag/adapter.py
# - 调整乘区逻辑 adapters/endfield/calc/multiplicative_zones/dag/config.py
# - 调整乘区逻辑 adapters/endfield/calc/multiplicative_zones/dag/loader.py
# - 调整乘区逻辑 adapters/endfield/calc/multiplicative_zones/final_attack_zone.py
# - 调整乘区逻辑 adapters/endfield/calc/multiplicative_zones/zone_manager.py
# - 调整乘区逻辑 adapters/endfield/calc/multiplicative_zones/zone_snapshot.py
# - 修改 adapters/endfield/calc/search/adapter.py
# - 修改 adapters/endfield/calc/search/evaluate/context.py
# - 修改 adapters/endfield/calc/search/evaluate/multi_skill.py
# - 修改 adapters/endfield/calc/search/evaluate/task.py
# - 修改 adapters/endfield/calc/search/persist/store.py
# - 修改 adapters/endfield/calc/search/plan/controller.py
# - 修改 adapters/endfield/calc/search/plan/estimate.py
# - 修改 adapters/endfield/calc/search/plan/job.py
# - 修改 adapters/endfield/calc/search/run/cancel.py
# - 修改 adapters/endfield/calc/search/run/mvp.py
# - 修改 adapters/endfield/calc/search/run/parallel.py
# - 修改 adapters/endfield/calc/search/run/runner.py
# - 修改 adapters/endfield/calc/search/run/session.py
# - 修改 adapters/endfield/calc/search/run/single_skill.py
# - 修改 adapters/endfield/calc/skills/segments.py
# - 修改 adapters/endfield/calc/skills/special_fields/codec.py
# - 修改 adapters/endfield/calc/skills/special_fields/name_utils.py
# - 修改 adapters/endfield/calc/skills/special_fields/runtime_bonus.py
# - 修改 adapters/endfield/calc/skills/special_fields/skills_schema.py
# - 修改 adapters/endfield/calc/skills/special_fields/slots_io.py
# - 修改 adapters/endfield/calc/skills/weapon_selection.py
# - 修改 adapters/endfield/data_loading/enemy_params.py
# - 修改 adapters/endfield/data_loading/equipment_catalog.py
# - 修改 adapters/endfield/data_loading/equipment_filters.py
# - 修改 adapters/endfield/data_loading/game_data_facade.py
# - 修改 adapters/endfield/data_loading/loader.py
# - 修改 adapters/endfield/data_loading/plugin_registry.py
# - 修改 adapters/endfield/tests/calculation/core/test_result_cache.py
# - 修改 adapters/endfield/tests/calculation/damage/engine/test_calculation.py
# - 修改 adapters/endfield/tests/calculation/damage/engine/test_damage_engine.py
# - 修改 adapters/endfield/tests/calculation/damage/engine/test_damage_types.py
# - 修改 adapters/endfield/tests/calculation/damage/engine/test_damage_visualization.py
# - 修改 adapters/endfield/tests/calculation/damage/engine/test_decimal_scaling.py
# - 修改 adapters/endfield/tests/calculation/damage/engine/test_manual_buff.py
# - 修改 adapters/endfield/tests/calculation/damage/engine/test_scaling_mode.py
# - 修改 adapters/endfield/tests/calculation/damage/zones/test_calc_chain_naming_compat.py
# - 修改 adapters/endfield/tests/calculation/damage/zones/test_curve_baker.py
# - 修改 adapters/endfield/tests/calculation/damage/zones/test_dag_adapter.py
# - 修改 adapters/endfield/tests/calculation/damage/zones/test_damage_snapshot.py
# - 修改 adapters/endfield/tests/calculation/damage/zones/test_damage_snapshot_manual_buff.py
# - 修改 adapters/endfield/tests/calculation/damage/zones/test_inverse_refactored.py
# - 修改 adapters/endfield/tests/calculation/damage/zones/test_result_export.py
# - 修改 adapters/endfield/tests/calculation/damage/zones/test_zone_snapshot.py
# - 修改 adapters/endfield/tests/calculation/equipment/test_equipment_affix.py
# - 修改 adapters/endfield/tests/calculation/equipment/test_equipment_catalog.py
# - 修改 adapters/endfield/tests/calculation/equipment/test_equipment_filters.py
# - 修改 adapters/endfield/tests/calculation/equipment/test_equipment_prune.py
# - 修改 adapters/endfield/tests/calculation/equipment/test_equipment_sync.py
# - 修改 adapters/endfield/tests/calculation/equipment/test_equipment_system.py
# - 修改 adapters/endfield/tests/calculation/loadout/optimizer/test_fixed_loadout_selection.py
# - 修改 adapters/endfield/tests/calculation/loadout/optimizer/test_loadout_optimizer.py
# - 修改 adapters/endfield/tests/calculation/loadout/optimizer/test_loadout_varying_slots.py
# - 修改 adapters/endfield/tests/calculation/loadout/optimizer/test_optimizer_types.py
# - 修改 adapters/endfield/tests/calculation/loadout/optimizer/test_streaming_optimizer.py
# - 修改 adapters/endfield/tests/calculation/loadout/state/test_loadout_attack_eval.py
# - 修改 adapters/endfield/tests/calculation/loadout/state/test_loadout_evaluation.py
# - 修改 adapters/endfield/tests/calculation/loadout/state/test_loadout_preset.py
# - 修改 adapters/endfield/tests/calculation/loadout/state/test_loadout_state.py
# - 修改 adapters/endfield/tests/calculation/loadout/state/test_weapon_skill_selection.py
# - 修改 adapters/endfield/tests/calculation/manual_buff/test_abnormal_manual_buff.py
# - 修改 adapters/endfield/tests/calculation/manual_buff/test_manual_buff_model.py
# - 修改 adapters/endfield/tests/calculation/manual_buff/test_spell_abnormal.py
# - 修改 adapters/endfield/tests/calculation/manual_buff/test_spell_abnormal_params.py
# - 修改 adapters/endfield/tests/calculation/multi_skill/test_multi_skill_counts.py
# - 修改 adapters/endfield/tests/calculation/multi_skill/test_multi_skill_optimizer.py
# - 修改 adapters/endfield/tests/calculation/search/plan/single_skill/test_search_settings.py
# - 修改 adapters/endfield/tests/calculation/search/plan/single_skill/test_single_skill_search_job.py
# - 修改 adapters/endfield/tests/calculation/search/plan/single_skill/test_single_skill_search_preview.py
# - 修改 adapters/endfield/tests/calculation/search/plan/test_search_controller.py
# - 修改 adapters/endfield/tests/calculation/search/plan/test_search_controls.py
# - 修改 adapters/endfield/tests/calculation/search/plan/test_search_error_binding.py
# - 修改 adapters/endfield/tests/calculation/search/plan/test_search_estimate.py
# - 修改 adapters/endfield/tests/calculation/search/plan/test_search_export_paths.py
# - 修改 adapters/endfield/tests/calculation/search/plan/test_search_format.py
# - 修改 adapters/endfield/tests/calculation/search/run/test_multi_skill_full_search.py
# - 修改 adapters/endfield/tests/calculation/search/run/test_mvp_pipeline.py
# - 修改 adapters/endfield/tests/calculation/search/run/test_parallel_evaluate.py
# - 修改 adapters/endfield/tests/calculation/search/run/test_search_persistence.py
# - 修改 adapters/endfield/tests/calculation/search/run/test_search_results_view.py
# - 修改 adapters/endfield/tests/calculation/search/run/test_search_runner.py
# - 修改 adapters/endfield/tests/calculation/search/run/test_search_session.py
# - 修改 adapters/endfield/tests/calculation/search/run/test_single_skill_search_runner.py
# - 修改 adapters/endfield/tests/calculation/search/run/test_top_n_tracker.py
# - 修改 adapters/endfield/tests/calculation/skills/test_skill_segments.py
# - 修改 adapters/endfield/tests/calculation/skills/test_skill_tables_damage_type.py
# - 修改 adapters/endfield/tests/character_weapon_equipment/test_add_character.py
# - 修改 adapters/endfield/tests/character_weapon_equipment/test_add_weapon.py
# - 修改 adapters/endfield/tests/character_weapon_equipment/test_weapon_dual_special.py
# - 修改 adapters/endfield/tests/character_weapon_equipment/test_weapon_property_display.py
# - 修改 adapters/endfield/tests/character_weapon_equipment/test_weapon_special_fields.py
# - 修改 adapters/endfield/tests/character_weapon_equipment/test_weapon_special_level.py
# - 修改 adapters/endfield/tests/character_weapon_equipment/test_weapon_special_stack_layers.py
# - 修改 adapters/endfield/tests/data/test_enemy_params.py
# - 修改 adapters/endfield/tests/data/test_game_data_contract.py
# - 修改 adapters/endfield/tests/data/test_game_data_facade.py
# - 修改 adapters/endfield/tests/data/test_gui_data_load.py
# - 修改 adapters/endfield/tests/data/test_loader_errors.py
# - 修改 adapters/endfield/tests/data/test_pack_data_paths.py
# - 修改 adapters/endfield/tests/data/test_plugin_registry.py
# - 修改 adapters/endfield/tests/data/test_unified_data_generator.py
# - 修改 adapters/endfield/tests/framework/test_endfield_dag_integration.py
# - 修改 adapters/endfield/tests/gui_design/app/test_confirm_orchestrator.py
# - 修改 adapters/endfield/tests/gui_design/app/test_confirm_refresh.py
# - 修改 adapters/endfield/tests/gui_design/app/test_confirm_selection_skill_levels.py
# - 修改 adapters/endfield/tests/gui_design/app/test_confirm_selection_state.py
# - 修改 adapters/endfield/tests/gui_design/controls/search/test_qt_actions.py
# - 修改 adapters/endfield/tests/gui_design/controls/search/test_qt_actions_extended.py
# - 修改 adapters/endfield/tests/gui_design/controls/search/test_qt_search_browser.py
# - 修改 adapters/endfield/tests/gui_design/controls/search/test_qt_search_browser_dialog.py
# - 修改 adapters/endfield/tests/gui_design/controls/search/test_search_browser_sqlite.py
# - 修改 adapters/endfield/tests/gui_design/controls/search/test_search_estimate_message.py
# - 修改 adapters/endfield/tests/gui_design/controls/search/test_search_settings.py
# - 修改 adapters/endfield/tests/gui_design/controls/search/test_search_worker_run.py
# - 修改 adapters/endfield/tests/gui_design/controls/test_frozen_search_export_paths.py
# - 修改 adapters/endfield/tests/gui_design/legal/test_donation_qt.py
# - 修改 adapters/endfield/tests/gui_design/panels/selection/__init__.py
# - 修改 adapters/endfield/tests/gui_design/panels/selection/test_qt_panel_getters.py
# - 修改 adapters/endfield/tests/gui_design/panels/selection/test_qt_subpanels.py
# - 修改 adapters/endfield/tests/gui_design/presentation/display/test_display_character_detail.py
# - 修改 adapters/endfield/tests/gui_design/presentation/display/test_display_format_coverage.py
# - 修改 adapters/endfield/tests/gui_design/presentation/display/test_display_lines_module.py
# - 修改 adapters/endfield/tests/gui_design/presentation/display/test_display_skill_resolve_detail.py
# - 修改 adapters/endfield/tests/gui_design/presentation/display/test_property_display_lines.py
# - 修改 adapters/endfield/tests/gui_design/presentation/preview/test_multi_skill_search_preview.py
# - 修改 adapters/endfield/tests/gui_design/presentation/preview/test_preview_cache.py
# - 修改 adapters/endfield/tests/gui_design/presentation/preview/test_single_hit_preview.py
# - 修改 adapters/endfield/tests/gui_design/presentation/test_gui_damage_snapshot.py
# - 修改 adapters/endfield/tests/gui_design/presentation/test_property_display_cache.py
# - 修改 adapters/endfield/tests/gui_design/presentation/test_search_results_lines.py
# - 修改 adapters/endfield/tests/gui_design/presentation/test_total_damage_panel.py
# - 修改 adapters/endfield/tests/gui_design/shared/preset/test_preset_batch_compare.py
# - 修改 adapters/endfield/tests/gui_design/shared/preset/test_preset_batch_coverage.py
# - 修改 adapters/endfield/tests/gui_design/shared/test_calc_history.py
# - 修改 adapters/endfield/tests/gui_design/shared/test_calc_mode_labels.py
# - 修改 adapters/endfield/tests/gui_design/shared/test_gui_damage_visualization.py
# - 修改 adapters/endfield/tests/gui_design/shared/test_gui_layout_detail.py
# - 修改 adapters/endfield/tests/gui_design/shared/test_operation_log.py
# - 修改 adapters/endfield/tests/gui_design/shared/test_weapon_display_remaining.py
# - 修改 adapters/endfield/tests/gui_design/shared/test_weapon_display_text_detail.py
# - 修改 adapters/endfield/tests/gui_design/shared/ui/test_ui_preferences.py
# - 修改 adapters/endfield/tests/gui_design/shared/ui/test_ui_preferences_detail.py
# - 修改 adapters/endfield/tests/gui_design/shell/test_gui_layout_contract.py
# - 修改 adapters/endfield/tests/gui_design/shell/test_qt_control_dock_widgets.py
# - 修改 adapters/endfield/tests/gui_design/shell/test_qt_factory.py
# - 修改 adapters/endfield/tests/gui_design/shell/test_qt_worker.py
# - 修改 adapters/endfield/tests/gui_design/shell/test_shell_init.py
# - 修改 adapters/endfield/tests/gui_design/shell/test_weapon_panel_layout.py
# - 修改 adapters/endfield/tests/repo/test_build_watchdog.py
# - 修改 adapters/endfield/tests/repo/test_config.py
# - 修改 adapters/endfield/tests/repo/test_coverage_boost_misc.py
# - 修改 adapters/endfield/tests/repo/test_gitignore_contract.py
# - 修改 adapters/endfield/tests/repo/test_legal_attribution.py
# - 修改 adapters/endfield/tests/repo/test_optional_deps.py
# - 修改 adapters/endfield/tests/repo/test_readme_layers.py
# - 修改 adapters/endfield/tests/repo/test_release_layout.py
# - 修改 adapters/endfield/tests/repo/test_repo_layout.py
# - 修改 adapters/endfield/tests/repo/test_repo_release_layout.py
# - 修改 adapters/endfield/tests/test_qt_imports.py
# - 修改 adapters/endfield/tests/tools/test_bwiki_scout.py
# - 修改 adapters/endfield/tests/tools/test_github_upload_signing.py
# - 修改 adapters/endfield/tests/tools/test_import_targets.py
# - 修改 adapters/endfield/tests/tools/test_migrate_weapon_skills_schema_tool.py
# - 修改 adapters/endfield/tests/tools/test_upload_meta.py
# - 修改 adapters/endfield/tests/tools/test_wiki_sync.py
# - 修改 adapters/endfield/tests/utils/test_extra_coverage.py
# - 修改 adapters/endfield/tests/utils/test_gui_window.py
# - 修改 adapters/endfield/tests/utils/test_platform_win32_patch.py
# - 修改 adapters/endfield/tests/utils/test_remaining_coverage.py
# - 修改 adapters/endfield/tests/utils/test_utils_optional_deps.py
# - 修改 adapters/endfield/tests/utils/test_utils_search_format.py
# - 修改 build.py
# - 修改 calc_engine/__init__.py
# - 修改 calc_engine/endfield/__init__.py
# - 修改 calc_engine/endfield/_replace_imports.py
# - 修改 calc_engine/endfield/calc/__init__.py
# - 修改 calc_engine/endfield/calc/core/__init__.py
# - 修改 calc_engine/endfield/calc/core/config.py
# - 修改 calc_engine/endfield/calc/core/curve_baker.py
# - 修改 calc_engine/endfield/calc/core/data_generator.py
# - 修改 calc_engine/endfield/calc/core/parallel_evaluate.py
# - 修改 calc_engine/endfield/calc/core/preview_cache.py
# - 修改 calc_engine/endfield/calc/core/result_cache.py
# - 修改 calc_engine/endfield/calc/core/result_export.py
# - 修改 calc_engine/endfield/calc/core/top_n_tracker.py
# - 修改 calc_engine/endfield/calc/damage/__init__.py
# - 修改 calc_engine/endfield/calc/damage/engine/__init__.py
# - 修改 calc_engine/endfield/calc/damage/engine/calculate.py
# - 修改 calc_engine/endfield/calc/damage/engine/helpers.py
# - 修改 calc_engine/endfield/calc/damage/engine/types.py
# - 修改 calc_engine/endfield/calc/damage/formula.py
# - 修改 calc_engine/endfield/calc/damage/inverse/__init__.py
# - 修改 calc_engine/endfield/calc/damage/inverse/api.py
# - 修改 calc_engine/endfield/calc/damage/inverse/attribute.py
# - 修改 calc_engine/endfield/calc/damage/inverse/fit_core.py
# - 修改 calc_engine/endfield/calc/damage/inverse/skill.py
# - 修改 calc_engine/endfield/calc/damage/types.py
# - 修改 calc_engine/endfield/calc/equipment/__init__.py
# - 修改 calc_engine/endfield/calc/equipment/affix.py
# - 修改 calc_engine/endfield/calc/equipment/prune.py
# - 修改 calc_engine/endfield/calc/equipment/system.py
# - 修改 calc_engine/endfield/calc/loadout/__init__.py
# - 修改 calc_engine/endfield/calc/loadout/attack_eval.py
# - 修改 calc_engine/endfield/calc/loadout/in_memory_optimizer.py
# - 修改 calc_engine/endfield/calc/loadout/optimizer/__init__.py
# - 修改 calc_engine/endfield/calc/loadout/optimizer/catalog.py
# - 修改 calc_engine/endfield/calc/loadout/optimizer/evaluate.py
# - 修改 calc_engine/endfield/calc/loadout/optimizer/plan.py
# - 修改 calc_engine/endfield/calc/loadout/optimizer/search.py
# - 修改 calc_engine/endfield/calc/loadout/optimizer/tasks.py
# - 修改 calc_engine/endfield/calc/loadout/optimizer/types.py
# - 修改 calc_engine/endfield/calc/loadout/slot_search.py
# - 修改 calc_engine/endfield/calc/manual_buff/__init__.py
# - 修改 calc_engine/endfield/calc/manual_buff/model.py
# - 修改 calc_engine/endfield/calc/manual_buff/physical.py
# - 修改 calc_engine/endfield/calc/manual_buff/spell.py
# - 修改 calc_engine/endfield/calc/manual_buff/spell_params.py
# - 修改 calc_engine/endfield/calc/multi_skill/__init__.py
# - 修改 calc_engine/endfield/calc/multi_skill/optimizer/__init__.py
# - 修改 calc_engine/endfield/calc/multi_skill/optimizer/search.py
# - 修改 calc_engine/endfield/calc/multi_skill/optimizer/types.py
# - 调整乘区逻辑 calc_engine/endfield/calc/multiplicative_zones/__init__.py
# - 调整乘区逻辑 calc_engine/endfield/calc/multiplicative_zones/_attribute_zone_bonus.py
# - 调整乘区逻辑 calc_engine/endfield/calc/multiplicative_zones/ability_bonus_calc.py
# - 调整乘区逻辑 calc_engine/endfield/calc/multiplicative_zones/ability_bonus_details.py
# - 调整乘区逻辑 calc_engine/endfield/calc/multiplicative_zones/attribute_zone.py
# - 调整乘区逻辑 calc_engine/endfield/calc/multiplicative_zones/base_zone.py
# - 调整乘区逻辑 calc_engine/endfield/calc/multiplicative_zones/dag/__init__.py
# - 调整乘区逻辑 calc_engine/endfield/calc/multiplicative_zones/dag/__main__.py
# - 调整乘区逻辑 calc_engine/endfield/calc/multiplicative_zones/dag/_subgraph_builders.py
# - 调整乘区逻辑 calc_engine/endfield/calc/multiplicative_zones/dag/adapter.py
# - 调整乘区逻辑 calc_engine/endfield/calc/multiplicative_zones/dag/config.py
# - 调整乘区逻辑 calc_engine/endfield/calc/multiplicative_zones/dag/loader.py
# - 调整乘区逻辑 calc_engine/endfield/calc/multiplicative_zones/final_attack_zone.py
# - 调整乘区逻辑 calc_engine/endfield/calc/multiplicative_zones/zone_manager.py
# - 调整乘区逻辑 calc_engine/endfield/calc/multiplicative_zones/zone_snapshot.py
# - 修改 calc_engine/endfield/calc/search/__init__.py
# - 修改 calc_engine/endfield/calc/search/adapter.py
# - 修改 calc_engine/endfield/calc/search/evaluate/__init__.py
# - 修改 calc_engine/endfield/calc/search/evaluate/context.py
# - 修改 calc_engine/endfield/calc/search/evaluate/multi_skill.py
# - 修改 calc_engine/endfield/calc/search/evaluate/task.py
# - 修改 calc_engine/endfield/calc/search/persist/__init__.py
# - 修改 calc_engine/endfield/calc/search/persist/store.py
# - 修改 calc_engine/endfield/calc/search/plan/__init__.py
# - 修改 calc_engine/endfield/calc/search/plan/controller.py
# - 修改 calc_engine/endfield/calc/search/plan/estimate.py
# - 修改 calc_engine/endfield/calc/search/plan/job.py
# - 修改 calc_engine/endfield/calc/search/run/__init__.py
# - 修改 calc_engine/endfield/calc/search/run/cancel.py
# - 修改 calc_engine/endfield/calc/search/run/mvp.py
# - 修改 calc_engine/endfield/calc/search/run/parallel.py
# - 修改 calc_engine/endfield/calc/search/run/runner.py
# - 修改 calc_engine/endfield/calc/search/run/session.py
# - 修改 calc_engine/endfield/calc/search/run/single_skill.py
# - 修改 calc_engine/endfield/calc/skills/__init__.py
# - 修改 calc_engine/endfield/calc/skills/segments.py
# - 修改 calc_engine/endfield/calc/skills/special_fields/__init__.py
# - 修改 calc_engine/endfield/calc/skills/special_fields/codec.py
# - 修改 calc_engine/endfield/calc/skills/special_fields/name_utils.py
# - 修改 calc_engine/endfield/calc/skills/special_fields/runtime_bonus.py
# - 修改 calc_engine/endfield/calc/skills/special_fields/skills_schema.py
# - 修改 calc_engine/endfield/calc/skills/special_fields/slots_io.py
# - 修改 calc_engine/endfield/calc/skills/weapon_selection.py
# - 更新文档 calc_engine/endfield/data/DATA_README.md
# - 更新 characters.json 角色数据
# - 变更 calc_engine/endfield/data/equipments.json
# - 更新 weapons.json 武器数据
# - 修改 calc_engine/endfield/data_loading/__init__.py
# - 修改 calc_engine/endfield/data_loading/enemy_params.py
# - 修改 calc_engine/endfield/data_loading/equipment_catalog.py
# - 修改 calc_engine/endfield/data_loading/equipment_filters.py
# - 修改 calc_engine/endfield/data_loading/game_data_facade.py
# - 修改 calc_engine/endfield/data_loading/loader.py
# - 修改 calc_engine/endfield/data_loading/plugin_registry.py
# - 修改 calc_engine/endfield/tests/calculation/core/test_result_cache.py
# - 修改 calc_engine/endfield/tests/calculation/damage/engine/test_calculation.py
# - 修改 calc_engine/endfield/tests/calculation/damage/engine/test_damage_engine.py
# - 修改 calc_engine/endfield/tests/calculation/damage/engine/test_damage_types.py
# - 修改 calc_engine/endfield/tests/calculation/damage/engine/test_damage_visualization.py
# - 修改 calc_engine/endfield/tests/calculation/damage/engine/test_decimal_scaling.py
# - 修改 calc_engine/endfield/tests/calculation/damage/engine/test_manual_buff.py
# - 修改 calc_engine/endfield/tests/calculation/damage/engine/test_scaling_mode.py
# - 修改 calc_engine/endfield/tests/calculation/damage/zones/test_calc_chain_naming_compat.py
# - 修改 calc_engine/endfield/tests/calculation/damage/zones/test_curve_baker.py
# - 修改 calc_engine/endfield/tests/calculation/damage/zones/test_dag_adapter.py
# - 修改 calc_engine/endfield/tests/calculation/damage/zones/test_damage_snapshot.py
# - 修改 calc_engine/endfield/tests/calculation/damage/zones/test_damage_snapshot_manual_buff.py
# - 修改 calc_engine/endfield/tests/calculation/damage/zones/test_inverse_refactored.py
# - 修改 calc_engine/endfield/tests/calculation/damage/zones/test_result_export.py
# - 修改 calc_engine/endfield/tests/calculation/damage/zones/test_zone_snapshot.py
# - 修改 calc_engine/endfield/tests/calculation/equipment/test_equipment_affix.py
# - 修改 calc_engine/endfield/tests/calculation/equipment/test_equipment_catalog.py
# - 修改 calc_engine/endfield/tests/calculation/equipment/test_equipment_filters.py
# - 修改 calc_engine/endfield/tests/calculation/equipment/test_equipment_prune.py
# - 修改 calc_engine/endfield/tests/calculation/equipment/test_equipment_sync.py
# - 修改 calc_engine/endfield/tests/calculation/equipment/test_equipment_system.py
# - 修改 calc_engine/endfield/tests/calculation/loadout/optimizer/test_fixed_loadout_selection.py
# - 修改 calc_engine/endfield/tests/calculation/loadout/optimizer/test_loadout_optimizer.py
# - 修改 calc_engine/endfield/tests/calculation/loadout/optimizer/test_loadout_varying_slots.py
# - 修改 calc_engine/endfield/tests/calculation/loadout/optimizer/test_optimizer_types.py
# - 修改 calc_engine/endfield/tests/calculation/loadout/optimizer/test_streaming_optimizer.py
# - 修改 calc_engine/endfield/tests/calculation/loadout/state/test_loadout_attack_eval.py
# - 修改 calc_engine/endfield/tests/calculation/loadout/state/test_loadout_evaluation.py
# - 修改 calc_engine/endfield/tests/calculation/loadout/state/test_loadout_preset.py
# - 修改 calc_engine/endfield/tests/calculation/loadout/state/test_loadout_state.py
# - 修改 calc_engine/endfield/tests/calculation/loadout/state/test_weapon_skill_selection.py
# - 修改 calc_engine/endfield/tests/calculation/manual_buff/test_abnormal_manual_buff.py
# - 修改 calc_engine/endfield/tests/calculation/manual_buff/test_manual_buff_model.py
# - 修改 calc_engine/endfield/tests/calculation/manual_buff/test_spell_abnormal.py
# - 修改 calc_engine/endfield/tests/calculation/manual_buff/test_spell_abnormal_params.py
# - 修改 calc_engine/endfield/tests/calculation/multi_skill/test_multi_skill_counts.py
# - 修改 calc_engine/endfield/tests/calculation/multi_skill/test_multi_skill_optimizer.py
# - 修改 calc_engine/endfield/tests/calculation/search/plan/single_skill/test_search_settings.py
# - 修改 calc_engine/endfield/tests/calculation/search/plan/single_skill/test_single_skill_search_job.py
# - 修改 calc_engine/endfield/tests/calculation/search/plan/single_skill/test_single_skill_search_preview.py
# - 修改 calc_engine/endfield/tests/calculation/search/plan/test_search_controller.py
# - 修改 calc_engine/endfield/tests/calculation/search/plan/test_search_controls.py
# - 修改 calc_engine/endfield/tests/calculation/search/plan/test_search_error_binding.py
# - 修改 calc_engine/endfield/tests/calculation/search/plan/test_search_estimate.py
# - 修改 calc_engine/endfield/tests/calculation/search/plan/test_search_export_paths.py
# - 修改 calc_engine/endfield/tests/calculation/search/plan/test_search_format.py
# - 修改 calc_engine/endfield/tests/calculation/search/run/test_multi_skill_full_search.py
# - 修改 calc_engine/endfield/tests/calculation/search/run/test_mvp_pipeline.py
# - 修改 calc_engine/endfield/tests/calculation/search/run/test_parallel_evaluate.py
# - 修改 calc_engine/endfield/tests/calculation/search/run/test_search_persistence.py
# - 修改 calc_engine/endfield/tests/calculation/search/run/test_search_results_view.py
# - 修改 calc_engine/endfield/tests/calculation/search/run/test_search_runner.py
# - 修改 calc_engine/endfield/tests/calculation/search/run/test_search_session.py
# - 修改 calc_engine/endfield/tests/calculation/search/run/test_single_skill_search_runner.py
# - 修改 calc_engine/endfield/tests/calculation/search/run/test_top_n_tracker.py
# - 修改 calc_engine/endfield/tests/calculation/skills/test_skill_segments.py
# - 修改 calc_engine/endfield/tests/calculation/skills/test_skill_tables_damage_type.py
# - 修改 calc_engine/endfield/tests/character_weapon_equipment/test_add_character.py
# - 修改 calc_engine/endfield/tests/character_weapon_equipment/test_add_weapon.py
# - 修改 calc_engine/endfield/tests/character_weapon_equipment/test_weapon_dual_special.py
# - 修改 calc_engine/endfield/tests/character_weapon_equipment/test_weapon_property_display.py
# - 修改 calc_engine/endfield/tests/character_weapon_equipment/test_weapon_special_fields.py
# - 修改 calc_engine/endfield/tests/character_weapon_equipment/test_weapon_special_level.py
# - 修改 calc_engine/endfield/tests/character_weapon_equipment/test_weapon_special_stack_layers.py
# - 修改 calc_engine/endfield/tests/conftest.py
# - 修改 calc_engine/endfield/tests/data/test_enemy_params.py
# - 修改 calc_engine/endfield/tests/data/test_game_data_contract.py
# - 修改 calc_engine/endfield/tests/data/test_game_data_facade.py
# - 修改 calc_engine/endfield/tests/data/test_gui_data_load.py
# - 修改 calc_engine/endfield/tests/data/test_loader_errors.py
# - 修改 calc_engine/endfield/tests/data/test_pack_data_paths.py
# - 修改 calc_engine/endfield/tests/data/test_plugin_registry.py
# - 修改 calc_engine/endfield/tests/data/test_unified_data_generator.py
# - 修改 calc_engine/endfield/tests/framework/test_endfield_dag_integration.py
# - 修改 calc_engine/endfield/tests/gui_design/app/test_confirm_orchestrator.py
# - 修改 calc_engine/endfield/tests/gui_design/app/test_confirm_refresh.py
# - 修改 calc_engine/endfield/tests/gui_design/app/test_confirm_selection_skill_levels.py
# - 修改 calc_engine/endfield/tests/gui_design/app/test_confirm_selection_state.py
# - 修改 calc_engine/endfield/tests/gui_design/controls/search/__init__.py
# - 修改 calc_engine/endfield/tests/gui_design/controls/search/test_qt_actions.py
# - 修改 calc_engine/endfield/tests/gui_design/controls/search/test_qt_actions_extended.py
# - 修改 calc_engine/endfield/tests/gui_design/controls/search/test_qt_search_browser.py
# - 修改 calc_engine/endfield/tests/gui_design/controls/search/test_qt_search_browser_dialog.py
# - 修改 calc_engine/endfield/tests/gui_design/controls/search/test_search_browser_sqlite.py
# - 修改 calc_engine/endfield/tests/gui_design/controls/search/test_search_estimate_message.py
# - 修改 calc_engine/endfield/tests/gui_design/controls/search/test_search_settings.py
# - 修改 calc_engine/endfield/tests/gui_design/controls/search/test_search_worker_run.py
# - 修改 calc_engine/endfield/tests/gui_design/controls/test_frozen_search_export_paths.py
# - 修改 calc_engine/endfield/tests/gui_design/legal/test_donation_qt.py
# - 修改 calc_engine/endfield/tests/gui_design/panels/selection/__init__.py
# - 修改 calc_engine/endfield/tests/gui_design/panels/selection/test_qt_panel_getters.py
# - 修改 calc_engine/endfield/tests/gui_design/panels/selection/test_qt_subpanels.py
# - 修改 calc_engine/endfield/tests/gui_design/presentation/display/test_display_character_detail.py
# - 修改 calc_engine/endfield/tests/gui_design/presentation/display/test_display_format_coverage.py
# - 修改 calc_engine/endfield/tests/gui_design/presentation/display/test_display_lines_module.py
# - 修改 calc_engine/endfield/tests/gui_design/presentation/display/test_display_skill_resolve_detail.py
# - 修改 calc_engine/endfield/tests/gui_design/presentation/display/test_property_display_lines.py
# - 修改 calc_engine/endfield/tests/gui_design/presentation/preview/test_multi_skill_search_preview.py
# - 修改 calc_engine/endfield/tests/gui_design/presentation/preview/test_preview_cache.py
# - 修改 calc_engine/endfield/tests/gui_design/presentation/preview/test_single_hit_preview.py
# - 修改 calc_engine/endfield/tests/gui_design/presentation/test_gui_damage_snapshot.py
# - 修改 calc_engine/endfield/tests/gui_design/presentation/test_property_display_cache.py
# - 修改 calc_engine/endfield/tests/gui_design/presentation/test_search_results_lines.py
# - 修改 calc_engine/endfield/tests/gui_design/presentation/test_total_damage_panel.py
# - 修改 calc_engine/endfield/tests/gui_design/shared/preset/test_preset_batch_compare.py
# - 修改 calc_engine/endfield/tests/gui_design/shared/preset/test_preset_batch_coverage.py
# - 修改 calc_engine/endfield/tests/gui_design/shared/test_calc_history.py
# - 修改 calc_engine/endfield/tests/gui_design/shared/test_calc_mode_labels.py
# - 修改 calc_engine/endfield/tests/gui_design/shared/test_gui_damage_visualization.py
# - 修改 calc_engine/endfield/tests/gui_design/shared/test_gui_layout_detail.py
# - 修改 calc_engine/endfield/tests/gui_design/shared/test_operation_log.py
# - 修改 calc_engine/endfield/tests/gui_design/shared/test_weapon_display_remaining.py
# - 修改 calc_engine/endfield/tests/gui_design/shared/test_weapon_display_text_detail.py
# - 修改 calc_engine/endfield/tests/gui_design/shared/ui/test_ui_preferences.py
# - 修改 calc_engine/endfield/tests/gui_design/shared/ui/test_ui_preferences_detail.py
# - 修改 calc_engine/endfield/tests/gui_design/shell/test_gui_layout_contract.py
# - 修改 calc_engine/endfield/tests/gui_design/shell/test_qt_control_dock_widgets.py
# - 修改 calc_engine/endfield/tests/gui_design/shell/test_qt_factory.py
# - 修改 calc_engine/endfield/tests/gui_design/shell/test_qt_worker.py
# - 修改 calc_engine/endfield/tests/gui_design/shell/test_shell_init.py
# - 修改 calc_engine/endfield/tests/gui_design/shell/test_weapon_panel_layout.py
# - 修改 calc_engine/endfield/tests/repo/test_build_watchdog.py
# - 修改 calc_engine/endfield/tests/repo/test_config.py
# - 修改 calc_engine/endfield/tests/repo/test_coverage_boost_misc.py
# - 修改 calc_engine/endfield/tests/repo/test_gitignore_contract.py
# - 修改 calc_engine/endfield/tests/repo/test_legal_attribution.py
# - 修改 calc_engine/endfield/tests/repo/test_optional_deps.py
# - 修改 calc_engine/endfield/tests/repo/test_readme_layers.py
# - 修改 calc_engine/endfield/tests/repo/test_release_layout.py
# - 修改 calc_engine/endfield/tests/repo/test_repo_layout.py
# - 修改 calc_engine/endfield/tests/repo/test_repo_release_layout.py
# - 修改 calc_engine/endfield/tests/test_qt_imports.py
# - 修改 calc_engine/endfield/tests/tools/test_bwiki_scout.py
# - 修改 calc_engine/endfield/tests/tools/test_github_upload_signing.py
# - 修改 calc_engine/endfield/tests/tools/test_import_targets.py
# - 修改 calc_engine/endfield/tests/tools/test_migrate_weapon_skills_schema_tool.py
# - 修改 calc_engine/endfield/tests/tools/test_upload_meta.py
# - 修改 calc_engine/endfield/tests/tools/test_wiki_sync.py
# - 修改 calc_engine/endfield/tests/utils/test_extra_coverage.py
# - 修改 calc_engine/endfield/tests/utils/test_gui_window.py
# - 修改 calc_engine/endfield/tests/utils/test_platform_win32_patch.py
# - 修改 calc_engine/endfield/tests/utils/test_remaining_coverage.py
# - 修改 calc_engine/endfield/tests/utils/test_utils_optional_deps.py
# - 修改 calc_engine/endfield/tests/utils/test_utils_search_format.py
# - 修改 devtool.py
# - 更新文档 docs/adr/0003-generic-calc-framework.md
# - 更新文档 docs/adr/0004-project-blueprint.md
# - 更新文档 docs/adr/0010-universal-game-framework-roadmap.md
# - 更新文档 docs/adr/0013-generic-inverse-engine.md
# - 更新文档 docs/adr/0016-refactor-rename-adapters-to-calc-engine.md
# - 更新文档 docs/adr/0017-gui-bridge-layer.md
# - 更新文档 docs/adr/0018-graph-editor-dag-unidirectional.md
# - 更新文档 docs/adr/0019-split-viewer-py-responsibilities.md
# - 更新文档 docs/quickstart.md
# - 更新文档 framework/README.md
# - 修改 framework/adapters/card_rpg/functions.py
# - 修改 framework/adapters/card_rpg/loader.py
# - 修改 framework/adapters/endfield/functions.py
# - 修改 framework/adapters/fps/functions.py
# - 修改 framework/adapters/fps/loader.py
# - 修改 framework/adapters/moba/functions.py
# - 修改 framework/adapters/moba/loader.py
# - 修改 framework/src/calc_framework/config/adapter.py
# - 修改 framework/src/calc_framework/config/file_watcher.py
# - 修改 framework/src/calc_framework/config/manager.py
# - 修改 framework/src/calc_framework/config/watcher.py
# - 修改 framework/src/calc_framework/dag/debugger.py
# - 修改 framework/src/calc_framework/dag/debugger_cli.py
# - 修改 framework/src/calc_framework/dag/debugger_gui.py
# - 修改 framework/src/calc_framework/dag/engine.py
# - 修改 framework/src/calc_framework/dag/errors.py
# - 修改 framework/src/calc_framework/dag/sandbox.py
# - 修改 framework/src/calc_framework/dag/schema.py
# - 修改 framework/src/calc_framework/dag/serializer.py
# - 修改 framework/src/calc_framework/dag/service.py
# - 修改 framework/src/calc_framework/dag/state.py
# - 修改 framework/src/calc_framework/dag/subgraph.py
# - 修改 framework/src/calc_framework/dag/templates.py
# - 修改 framework/src/calc_framework/data/attr_schema.py
# - 修改 framework/src/calc_framework/data/context.py
# - 修改 framework/src/calc_framework/data/loader.py
# - 修改 framework/src/calc_framework/data/schema.py
# - 修改 framework/src/calc_framework/editor/__main__.py
# - 修改 framework/src/calc_framework/editor/editor.py
# - 修改 framework/src/calc_framework/editor/gui.py
# - 修改 framework/src/calc_framework/graph_editor/__main__.py
# - 修改 framework/src/calc_framework/graph_editor/compiler.py
# - 修改 framework/src/calc_framework/graph_editor/dag_service_factory.py
# - 修改 framework/src/calc_framework/graph_editor/file_actions.py
# - 修改 framework/src/calc_framework/graph_editor/graph_editor_widget.py
# - 修改 framework/src/calc_framework/graph_editor/help_content.py
# - 修改 framework/src/calc_framework/graph_editor/help_dialog.py
# - 修改 framework/src/calc_framework/graph_editor/node_panel.py
# - 修改 framework/src/calc_framework/graph_editor/package_manager.py
# - 修改 framework/src/calc_framework/graph_editor/ports.py
# - 修改 framework/src/calc_framework/graph_editor/prop_panel.py
# - 修改 framework/src/calc_framework/graph_editor/registry.py
# - 修改 framework/src/calc_framework/graph_editor/schema.py
# - 修改 framework/src/calc_framework/graph_editor/serializer.py
# - 修改 framework/src/calc_framework/graph_editor/wire.py
# - 修改 framework/src/calc_framework/inverse/advanced.py
# - 修改 framework/src/calc_framework/inverse/base.py
# - 修改 framework/src/calc_framework/inverse/engine.py
# - 修改 framework/src/calc_framework/inverse/registry.py
# - 修改 framework/src/calc_framework/launcher.py
# - 修改 framework/src/calc_framework/logging.py
# - 修改 framework/src/calc_framework/plugin/base.py
# - 修改 framework/src/calc_framework/plugin/builtin.py
# - 修改 framework/src/calc_framework/plugin/registry.py
# - 修改 framework/src/calc_framework/publish/catalog.py
# - 修改 framework/src/calc_framework/publish/schema.py
# - 修改 framework/src/calc_framework/search/cancel.py
# - 修改 framework/src/calc_framework/search/engine.py
# - 修改 framework/src/calc_framework/search/parallel.py
# - 修改 framework/src/calc_framework/search/persist.py
# - 修改 framework/src/calc_framework/search/result.py
# - 修改 framework/src/calc_framework/search/session.py
# - 修改 framework/src/calc_framework/search/tracker.py
# - 修改 framework/src/calc_framework/ui/__main__.py
# - 修改 framework/src/calc_framework/ui/compute_sheet.py
# - 修改 framework/src/calc_framework/ui/controls.py
# - 修改 framework/src/calc_framework/ui/format.py
# - 修改 framework/src/calc_framework/ui/layout.py
# - 修改 framework/src/calc_framework/ui/theme.py
# - 修改 framework/src/calc_framework/ui/viewer.py
# - 修改 framework/src/calc_framework/ui/viewer_help_content.py
# - 修改 framework/src/calc_framework/ui/viewer_pack_utils.py
# - 修改 framework/src/calc_framework/ui/viewer_plugin_manager.py
# - 修改 framework/tests/adapters/test_card_rpg_adapter.py
# - 修改 framework/tests/adapters/test_moba_fps.py
# - 修改 framework/tests/config/test_adapter.py
# - 修改 framework/tests/config/test_adapter_extra.py
# - 修改 framework/tests/config/test_dag_review.py
# - 修改 framework/tests/config/test_file_watcher.py
# - 修改 framework/tests/config/test_manager.py
# - 修改 framework/tests/config/test_watcher.py
# - 修改 framework/tests/dag/test_block_cache.py
# - 修改 framework/tests/dag/test_block_cache_real_dag.py
# - 修改 framework/tests/dag/test_debugger.py
# - 修改 framework/tests/dag/test_end_to_end.py
# - 修改 framework/tests/dag/test_engine.py
# - 修改 framework/tests/dag/test_engine_logging.py
# - 修改 framework/tests/dag/test_errors.py
# - 修改 framework/tests/dag/test_graph_file_service.py
# - 修改 framework/tests/dag/test_incremental_and_lazy.py
# - 修改 framework/tests/dag/test_sandbox.py
# - 修改 framework/tests/dag/test_schema.py
# - 修改 framework/tests/dag/test_serializer.py
# - 修改 framework/tests/dag/test_service.py
# - 修改 framework/tests/dag/test_subgraph.py
# - 修改 framework/tests/dag/test_templates.py
# - 修改 framework/tests/data/test_attr_schema.py
# - 修改 framework/tests/data/test_context.py
# - 修改 framework/tests/data/test_loader.py
# - 修改 framework/tests/data/test_schema.py
# - 修改 framework/tests/editor/test_cli.py
# - 修改 framework/tests/editor/test_editor.py
# - 修改 framework/tests/editor/test_gui.py
# - 修改 framework/tests/graph_editor/test_compiler.py
# - 修改 framework/tests/graph_editor/test_endfield_zone_package.py
# - 修改 framework/tests/graph_editor/test_file_actions.py
# - 修改 framework/tests/graph_editor/test_file_io.py
# - 修改 framework/tests/graph_editor/test_graph_editor_widget.py
# - 修改 framework/tests/graph_editor/test_node_operations.py
# - 修改 framework/tests/graph_editor/test_node_panel.py
# - 修改 framework/tests/graph_editor/test_package_manager.py
# - 修改 framework/tests/graph_editor/test_ports_and_wire.py
# - 修改 framework/tests/graph_editor/test_prop_panel.py
# - 修改 framework/tests/graph_editor/test_registry.py
# - 修改 framework/tests/graph_editor/test_schema.py
# - 修改 framework/tests/graph_editor/test_serializer.py
# - 修改 framework/tests/graph_editor/test_wire_creation.py
# - 修改 framework/tests/inverse/test_advanced_extra.py
# - 修改 framework/tests/inverse/test_advanced_formulas.py
# - 修改 framework/tests/inverse/test_base_extra.py
# - 修改 framework/tests/inverse/test_engine.py
# - 修改 framework/tests/ocr/test_detector.py
# - 修改 framework/tests/ocr/test_mapper.py
# - 修改 framework/tests/ocr/test_recognizer.py
# - 修改 framework/tests/plugin/test_plugin.py
# - 修改 framework/tests/publish/test_publish.py
# - 修改 framework/tests/search/test_cancel_result.py
# - 修改 framework/tests/search/test_engine.py
# - 修改 framework/tests/search/test_engine_extra.py
# - 修改 framework/tests/search/test_parallel.py
# - 修改 framework/tests/search/test_persist.py
# - 修改 framework/tests/search/test_tracker.py
# - 修改 framework/tests/test_logging.py
# - 修改 framework/tests/ui/test_compute_sheet.py
# - 修改 framework/tests/ui/test_controls.py
# - 修改 framework/tests/ui/test_endfield_compute_sheet.py
# - 修改 framework/tests/ui/test_format.py
# - 修改 framework/tests/ui/test_layout.py
# - 修改 framework/tests/utils/test_updater.py
# - 修改 games/endfield/framework_bridge.py
# - 修改 games/endfield/gui_design/app/confirm_refresh.py
# - 修改 games/endfield/gui_design/app/display_request.py
# - 修改 games/endfield/gui_design/app/loadout_evaluation.py
# - 修改 games/endfield/gui_design/app/loadout_preset.py
# - 修改 games/endfield/gui_design/app/loadout_state.py
# - 修改 games/endfield/gui_design/controls/enemy/qt_enemy_panel.py
# - 修改 games/endfield/gui_design/controls/enhancement/qt_dialogs.py
# - 修改 games/endfield/gui_design/controls/manual_buff/qt_window.py
# - 修改 games/endfield/gui_design/controls/ocr/__init__.py
# - 修改 games/endfield/gui_design/controls/search/qt_actions.py
# - 修改 games/endfield/gui_design/controls/search/qt_search_browser.py
# - 修改 games/endfield/gui_design/controls/search/search_estimate_message.py
# - 修改 games/endfield/gui_design/controls/search/search_settings.py
# - 修改 games/endfield/gui_design/designer/data_browser_tab.py
# - 修改 games/endfield/gui_design/designer/data_editor_tab.py
# - 修改 games/endfield/gui_design/designer/designer_main.py
# - 修改 games/endfield/gui_design/designer/inverse_tab.py
# - 修改 games/endfield/gui_design/layout/gui_layout.py
# - 修改 games/endfield/gui_design/legal/attribution_content.py
# - 修改 games/endfield/gui_design/legal/donation_qt.py
# - 修改 games/endfield/gui_design/panels/selection/qt_ability_panel.py
# - 修改 games/endfield/gui_design/panels/selection/qt_panel.py
# - 修改 games/endfield/gui_design/panels/selection/qt_panel_getters_mixin.py
# - 修改 games/endfield/gui_design/panels/selection/qt_subpanels.py
# - 修改 games/endfield/gui_design/presentation/damage_snapshot.py
# - 修改 games/endfield/gui_design/presentation/display/character.py
# - 修改 games/endfield/gui_design/presentation/display/format.py
# - 修改 games/endfield/gui_design/presentation/display/single_hit.py
# - 修改 games/endfield/gui_design/presentation/display/skill_resolve.py
# - 修改 games/endfield/gui_design/presentation/display_lines.py
# - 修改 games/endfield/gui_design/presentation/preview/multi_skill.py
# - 修改 games/endfield/gui_design/presentation/preview/single_skill.py
# - 修改 games/endfield/gui_design/presentation/preview_lines.py
# - 修改 games/endfield/gui_design/presentation/search_results_lines.py
# - 修改 games/endfield/gui_design/presentation/total_damage_panel.py
# - 修改 games/endfield/gui_design/shared/calc_history.py
# - 修改 games/endfield/gui_design/shared/calc_mode_labels.py
# - 修改 games/endfield/gui_design/shared/damage_visualization.py
# - 修改 games/endfield/gui_design/shared/display_view/qt_columns.py
# - 修改 games/endfield/gui_design/shared/preset_batch_compare.py
# - 修改 games/endfield/gui_design/shared/ui_preferences.py
# - 修改 games/endfield/gui_design/shared/weapon_display_text.py
# - 修改 games/endfield/gui_design/shell/qt_app.py
# - 修改 games/endfield/gui_design/shell/qt_app_confirm_mixin.py
# - 修改 games/endfield/gui_design/shell/qt_app_dialog_mixin.py
# - 修改 games/endfield/gui_design/shell/qt_app_search_mixin.py
# - 修改 games/endfield/gui_design/shell/qt_control_dock.py
# - 修改 games/endfield/gui_design/shell/qt_control_dock_builders.py
# - 修改 games/endfield/gui_design/shell/qt_control_dock_widgets.py
# - 修改 games/endfield/gui_design/shell/qt_factory.py
# - 修改 games/endfield/gui_design/shell/qt_worker.py
# - 修改 games/endfield/main.py
# - 变更 games/endfield/pyproject.toml
# - 修改 games/endfield/upload_meta.py
# - 修改 github_download_module.py
# - 修改 github_upload_module.py
# - 修改 installer/build_installer.py
# - 修改 main.py
# - 修改 main_build.py
# - 修改 main_designer.py
# - 修改 main_launcher.py
# - 修改 main_pack_designer.py
# - 修改 please_read_me.py
# - 修改 release_bundle/platform_win32_patch.py
# - 修改 release_bundle/pyinstaller_entry.py
# - 修改 release_bundle/release_layout.py
# - 修改 tools/bwiki_scout/__main__.py
# - 修改 tools/bwiki_scout/api.py
# - 修改 tools/bwiki_scout/backfill_weapon_max_stack.py
# - 修改 tools/bwiki_scout/compare_stats.py
# - 修改 tools/bwiki_scout/config.py
# - 修改 tools/bwiki_scout/detail_levels.py
# - 修改 tools/bwiki_scout/equipment_sync.py
# - 修改 tools/bwiki_scout/equipment_wiki.py
# - 修改 tools/bwiki_scout/gallery.py
# - 修改 tools/bwiki_scout/import_targets.py
# - 修改 tools/bwiki_scout/json_scan.py
# - 修改 tools/bwiki_scout/local_schema.py
# - 修改 tools/bwiki_scout/migrate_weapon_special_json.py
# - 修改 tools/bwiki_scout/names.py
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
# - 修改 tools/data_pipeline/__main__.py
# - 修改 tools/data_pipeline/cli.py
# - 修改 tools/data_pipeline/readers/csv_reader.py
# - 修改 tools/data_pipeline/readers/json_reader.py
# - 修改 tools/data_pipeline/schema.py
# - 修改 tools/data_pipeline/transformers/from_legacy_endfield.py
# - 修改 tools/data_pipeline/transformers/to_standard.py
# - 修改 tools/data_pipeline/validators/schema_check.py
# - 修改 tools/designer/__main__.py
# - 修改 tools/designer/app.py
# - 修改 tools/designer/data_editor/panel.py
# - 修改 tools/designer/exporter.py
# - 修改 tools/designer/layout_editor/canvas.py
# - 修改 tools/designer/layout_editor/collision.py
# - 修改 tools/designer/theme_editor/panel.py
# - 修改 tools/endfield_designer/__main__.py
# - 修改 tools/endfield_designer/data_browser_tab.py
# - 修改 tools/endfield_designer/data_editor_tab.py
# - 修改 tools/endfield_designer/designer_main.py
# - 修改 tools/endfield_designer/inverse_tab.py
# - 修改 tools/endfield_designer/seed_tab.py
# - 修改 tools/endfield_scripts/add_character.py
# - 修改 tools/endfield_scripts/add_weapon.py
# - 修改 tools/endfield_scripts/build.py
# - 修改 tools/endfield_scripts/editor_app.py
# - 修改 tools/endfield_scripts/inverse_cli.py
# - 修改 tools/endfield_scripts/inverse_formula_gui.py
# - 修改 tools/endfield_scripts/seed_characters.py
# - 修改 tools/endfield_scripts/seed_weapons.py
# - 修改 tools/framework_publish.py
# - 修改 tools/gen_architecture_review_html.py
# - 修改 tools/generate_endfield_zone_package.py
# - 修改 tools/migrate_weapon_skills_schema.py
# - 修改 tools/ocr/cli.py
# - 修改 tools/ocr/collector.py
# - 修改 tools/ocr/detector.py
# - 修改 tools/ocr/download_models.py
# - 修改 tools/ocr/label.py
# - 修改 tools/ocr/mapper.py
# - 修改 tools/ocr/recognizer.py
# - 修改 tools/ocr/train.py
# - 修改 tools/plugin_pack.py
# - 修改 tools/validate_layout_sync.py
# - 修改 upload_meta.py
# - 修改 utils/app_paths.py
# - 修改 utils/donation.py
# - 修改 utils/gui_chart_theme.py
# - 修改 utils/gui_fonts.py
# - 修改 utils/gui_help_calculator.py
# - 修改 utils/gui_help_designer.py
# - 修改 utils/gui_help_dialog.py
# - 修改 utils/gui_help_launcher.py
# - 修改 utils/gui_window.py
# - 修改 utils/operation_log.py
# - 修改 utils/optional_deps.py
# - 修改 utils/path_utils.py
# - 修改 utils/platform_win32_patch.py
# - 修改 utils/search_format.py
# - 修改 utils/updater.py
# - 修改 version.py
# - 修改 web/backend/api/adapters.py
# - 修改 web/backend/api/compute.py
# - 修改 web/backend/api/data.py
# - 修改 web/backend/api/hub.py
# - 修改 web/backend/api/layout.py
# - 修改 web/backend/api/pack.py
# - 修改 web/backend/api/search.py
# - 修改 web/backend/hub/storage.py
# - 修改 web/backend/main.py
# - 修改 web/hub/build_catalog.py
# - 修改 web/hub/build_plugin_catalog.py
# --- END UPLOAD_SUMMARY ---
