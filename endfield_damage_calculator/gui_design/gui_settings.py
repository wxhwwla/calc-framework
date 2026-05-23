#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI 设置模块

此模块包含 GUI 全局设置初始化函数和常量定义。
"""

from utils.platform_win32_patch import apply_platform_win32_patch

apply_platform_win32_patch()
import customtkinter as ctk


def gui_settings() -> None:
    """
    初始化 GUI 全局设置
    
    功能：
    1. 设置应用外观模式为深色模式（"dark"）
    2. 设置应用颜色主题为蓝色（"blue"）
    
    调用时机：应在创建任何 CTk 组件之前调用
    
    示例：
        gui_settings()  # 在创建 CTk 窗口之前调用
    """
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
