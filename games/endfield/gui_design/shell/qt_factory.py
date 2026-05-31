#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""
PySide6 后端 widget adapter。

本模块为迁移期提供超薄包装层：将 PySide6 控件以通用命名导出，
部分控件附加 CTk 兼容的属性（如 ``font``、``fg_color`` 等），
使双后端代码共用同一套导入路径。迁移完成后可改为直接 ``from PySide6.QtWidgets import ...``。
"""

from __future__ import annotations

from PySide6.QtGui import QFont as QtFont
from PySide6.QtWidgets import (
    QCheckBox as QtCheckBox,
)
from PySide6.QtWidgets import (
    QComboBox as QtOptionMenu,
)
from PySide6.QtWidgets import (
    QDialog as QtToplevel,
)
from PySide6.QtWidgets import (
    QLabel as QtLabel,
)
from PySide6.QtWidgets import (
    QLineEdit as QtEntry,
)
from PySide6.QtWidgets import (
    QPushButton as QtButton,
)
from PySide6.QtWidgets import (
    QScrollArea as QtScrollableFrame,
)
from PySide6.QtWidgets import (
    QSlider as QtSlider,
)
from PySide6.QtWidgets import (
    QTabWidget as QtTabview,
)
from PySide6.QtWidgets import (
    QTextEdit as QtTextbox,
)
from PySide6.QtWidgets import (
    QWidget as QtFrame,
)

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
    "CTkButton",
    "CTkCheckBox",
    "CTkComboBox",
    "CTkEntry",
    "CTkFont",
    "CTkFrame",
    "CTkLabel",
    "CTkOptionMenu",
    "CTkScrollableFrame",
    "CTkSlider",
    "CTkSwitch",
    "CTkTabview",
    "CTkTextbox",
    "CTkToplevel",
]
