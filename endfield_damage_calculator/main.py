#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
终末地伤害计算小工具 - 项目入口文件

项目结构说明：
├── main.py                    # 项目入口，启动应用
├── pyproject.toml             # 打包配置文件
├── gui_design/                # GUI 界面模块
│   ├── gui.py                 # 主应用类，管理窗口和布局
│   ├── gui_tools.py           # GUI 工具组件导出层
│   ├── gui_settings.py        # GUI 设置初始化
│   ├── selection_panel.py     # 选择面板类
│   └── property_display.py    # 属性展示函数
├── calculation/               # 计算逻辑模块
│   └── multiplicative_zone.py # 乘法区伤害计算
├── data/                      # 统一数据加载层
│   └── loader.py              # 角色和武器数据的统一加载与缓存
├── utils/                     # 工具函数模块
│   └── path_utils.py          # 路径处理工具（支持打包后运行）
└── character_weapon_equipment/# 数据文件目录
    ├── character_data/        # 角色数据（JSON格式）
    └── weapon_data/           # 武器数据（JSON格式）

功能说明：
1. 提供角色和武器选择界面
2. 显示选中角色/武器的属性
3. 预留伤害计算区域（开发中）

使用方式：
    python main.py
"""

import sys
import threading
import time


def preload_data():
    """预加载角色/武器 JSON 到 data.loader 缓存（后台线程）。"""
    try:
        from data.loader import preload_game_data

        preload_game_data()
    except Exception as exc:
        # 启动阶段仅预加载；GUI 打开面板时会再次加载并弹窗提示
        import logging

        logging.getLogger(__name__).warning("预加载游戏数据失败: %s", exc)


def main() -> None:
    """
    应用主入口函数

    功能：
    1. 启动后台线程预加载数据
    2. 延迟导入 GUI 模块（加快启动速度）
    3. 创建应用实例
    4. 启动主事件循环
    """
    # 启动后台线程预加载数据（不阻塞主界面）
    preload_thread = threading.Thread(target=preload_data, daemon=True)
    preload_thread.start()
    
    # 导入 GUI 模块
    from gui_design.gui import DamageCalculatorApp
    
    # 创建应用实例
    app = DamageCalculatorApp()
    
    # 启动主事件循环，显示窗口
    app.run()


# 程序入口判断
if __name__ == "__main__":
    # 记录启动时间（用于调试）
    start_time = time.time()
    
    # 调用主函数启动应用
    main()
    
    # 输出启动耗时（仅在控制台运行时显示）
    if not hasattr(sys, 'frozen'):
        elapsed = (time.time() - start_time) * 1000
        print(f"启动耗时: {elapsed:.2f}ms")
