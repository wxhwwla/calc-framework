#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""
终末地伤害计算器 - Calc Framework（通用游戏计算框架）游戏适配包

项目结构说明（详见包内 README.md、docs/会话接续手册.md）：
├── main.py                    # 本文件：启动 GUI（PySide6 版）
├── gui/endfield_app.py  # 主窗口（双页签：计算页 / 高级页）
├── data/loader.py             # 角色、武器、装备 JSON 统一加载
├── data/game_data_facade.py   # 应用级数据门面（GUI / 对比 / 搜索）
├── calculation/               # 乘区、单段伤害、装备词条、全量搜索流水线
└── character_weapon_equipment/  # characters.json / weapons.json / equipments.json

功能说明：
1. 角色 / 武器 / 装备选择与属性、乘区展示
2. 单段伤害、乘区快照、多技能预览、全量遍历（单技能或手动次数加权，实验）
3. 完整敌方参数面板、总伤结算 UI 等仍为后续功能

使用方式：
    python main.py

注意：GUI 后端为 PySide6。CustomTkinter 版已于 2026-05 移除。
"""

import os
import sys
import threading
import time
from pathlib import Path

# 确保 repo 根在 sys.path 上（共享 utils/、release_bundle/ 等）
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# 打包 exe：须在 rust_bridge / evaluate 导入前设置
from utils.frozen_runtime import apply_frozen_runtime_defaults

apply_frozen_runtime_defaults()

# Windows：在 platform.release() 等调用前规避 WMI 卡死（PyInstaller 兼容）
from utils.platform_win32_patch import apply_platform_win32_patch

apply_platform_win32_patch()


def preload_data():
    """预加载角色/武器 JSON 到 data.loader 缓存（后台线程）。"""
    try:
        from games.endfield.data_loading.loader import preload_game_data

        preload_game_data()
    except Exception as exc:
        from games.endfield.framework_bridge import get_logger

        get_logger(__name__).warning("预加载游戏数据失败: %s", exc)


def main() -> None:
    """
    应用主入口函数

    功能：
    1. 启动后台线程预加载数据
    2. 延迟导入 GUI 模块（加快启动速度）
    3. 创建应用实例
    4. 启动主事件循环
    """
    import multiprocessing

    multiprocessing.freeze_support()

    from utils.search_diagnostics import init_search_diagnostics

    log_dir = init_search_diagnostics()

    # 启动后台线程预加载数据（不阻塞主界面）
    preload_thread = threading.Thread(target=preload_data, daemon=True)
    preload_thread.start()

    # 初始化框架日志系统（环境变量 CALC_FRAMEWORK_LOG_LEVEL 控制级别）
    from utils.path_utils import get_application_dir

    from games.endfield.framework_bridge import get_logger
    from games.endfield.framework_bridge import setup_logging as fw_setup_logging

    frozen = getattr(sys, "frozen", False)
    log_level = "INFO" if frozen else os.environ.get("CALC_FRAMEWORK_LOG_LEVEL", "WARNING")
    fw_setup_logging(log_file=str(log_dir / "app.log"), level=log_level)
    _logger = get_logger(__name__)
    _logger.info("应用启动中…")

    if not getattr(sys, "frozen", False):
        from utils.optional_deps import ensure_runtime_dependencies

        ensure_runtime_dependencies()
        _logger.info("正在加载界面…")

    # 导入 GUI 模块
    from games.endfield.data_loading.plugin_registry import load_default_plugins
    from games.endfield.gui.endfield_app import EndfieldApp as DamageCalculatorApp

    if not getattr(sys, "frozen", False):
        _logger.info("正在创建主窗口…")

    # 热加载 plugins/ 下的扩展 JSON/YAML（敌方等）
    load_default_plugins(get_application_dir())

    # 创建应用实例
    app = DamageCalculatorApp()

    if not getattr(sys, "frozen", False):
        from utils.optional_deps import format_missing_gui_extras

        extras_hint = format_missing_gui_extras()
        if extras_hint:
            _logger.info("缺失扩展提示:\n%s", extras_hint)

    # 启动主事件循环，显示窗口
    app.run()


# 程序入口判断
if __name__ == "__main__":
    # 记录启动时间（用于调试）
    start_time = time.time()

    # 调用主函数启动应用
    main()

    # 输出启动耗时
    if not hasattr(sys, "frozen"):
        elapsed = (time.time() - start_time) * 1000
        from games.endfield.framework_bridge import get_logger

        get_logger(__name__).info("启动耗时: %.2fms", elapsed)
