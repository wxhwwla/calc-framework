#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
终末地伤害计算小工具 - 项目入口文件

项目结构说明（详见包内 README.md、docs/会话接续手册.md）：
├── main.py                    # 本文件：启动 GUI
├── gui_design/gui.py          # 主窗口（6 列：选择 / 计算与搜索 / 属性 / 乘区）
├── data/loader.py             # 角色、武器、装备 JSON 统一加载
├── calculation/               # 乘区、单段伤害、装备词条、全量搜索流水线
└── character_weapon_equipment/  # characters.json / weapons.json / equipments.json

功能说明：
1. 角色 / 武器 / 装备选择与属性、乘区展示
2. 单段伤害、乘区快照、多技能快速预览、单技能全量遍历（实验）
3. 完整敌方参数面板与多技能全量遍历产品化仍为后续功能

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
