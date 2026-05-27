#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CTk 后端 widget adapter。

本模块为迁移期提供超薄包装层：将 CustomTkinter 控件以通用接口形式导出，
供双后端代码共用同一套导入路径。迁移完成后可直接删除。
"""

from __future__ import annotations

from utils.platform_win32_patch import apply_platform_win32_patch

apply_platform_win32_patch()
import customtkinter as ctk

# 直接透传 CTk 控件类，保持原有行为不变
# 双后端共用代码可通过 backends 统一导入
CTkFrame = ctk.CTkFrame
CTkLabel = ctk.CTkLabel
CTkButton = ctk.CTkButton
CTkOptionMenu = ctk.CTkOptionMenu
CTkSlider = ctk.CTkSlider
CTkEntry = ctk.CTkEntry
CTkCheckBox = ctk.CTkCheckBox
CTkSwitch = ctk.CTkSwitch
CTkTabview = ctk.CTkTabview
CTkScrollableFrame = ctk.CTkScrollableFrame
CTkTextbox = ctk.CTkTextbox
CTkToplevel = ctk.CTkToplevel
CTkFont = ctk.CTkFont
CTkComboBox = ctk.CTkComboBox

__all__ = [
    "CTkFrame",
    "CTkLabel",
    "CTkButton",
    "CTkOptionMenu",
    "CTkSlider",
    "CTkEntry",
    "CTkCheckBox",
    "CTkSwitch",
    "CTkTabview",
    "CTkScrollableFrame",
    "CTkTextbox",
    "CTkToplevel",
    "CTkFont",
    "CTkComboBox",
]
