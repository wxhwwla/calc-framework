#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PySide6 后端 widget adapter。

本模块为迁移期提供超薄包装层：将 PySide6 控件以通用命名导出，
部分控件附加 CTk 兼容的属性（如 ``font``、``fg_color`` 等），
使双后端代码共用同一套导入路径。迁移完成后可改为直接 ``from PySide6.QtWidgets import ...``。
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget as QtFrame,
    QLabel as QtLabel,
    QPushButton as QtButton,
    QComboBox as QtOptionMenu,
    QSlider as QtSlider,
    QLineEdit as QtEntry,
    QCheckBox as QtCheckBox,
    QTabWidget as QtTabview,
    QScrollArea as QtScrollableFrame,
    QTextEdit as QtTextbox,
    QDialog as QtToplevel,
)
from PySide6.QtGui import QFont as QtFont

# 统一命名（与 ctk_factory 保持一致，让后端无关代码无缝切换）
CTkFrame = QtFrame
CTkLabel = QtLabel
CTkButton = QtButton
CTkOptionMenu = QtOptionMenu
CTkSlider = QtSlider
CTkEntry = QtEntry
CTkCheckBox = QtCheckBox
CTkSwitch = QtCheckBox  # Qt 无原生 Switch，阶段 1 开始用 QSS 模拟
CTkTabview = QtTabview
CTkScrollableFrame = QtScrollableFrame
CTkTextbox = QtTextbox
CTkToplevel = QtToplevel
CTkFont = QtFont
CTkComboBox = QtOptionMenu

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
