#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PySide6 主应用壳层（阶段 0 骨架）。

当前为最小窗口，后续阶段将逐步填充控件。

与 ``app.py`` 的 CTk 版本保持相同的 ``.app`` / ``.run()`` 接口，
使 ``main.py`` 的启动逻辑与后端无关。
"""

from __future__ import annotations

import sys
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

from gui_design.shared.gui_settings import gui_settings
from please_read_me import get_exe_version


class QtDamageApp:
    """PySide6 主应用。

    属性：
        app: QMainWindow 实例（与 CTk 版 ``DamageCalculatorApp.app`` 语义一致）
    """

    def __init__(self) -> None:
        gui_settings()

        self._qapp: QApplication = QApplication(sys.argv)
        self._qapp.setStyle("Fusion")

        self.app: QMainWindow = QMainWindow()
        self.app.setWindowTitle(f"终末地伤害计算小工具 v{get_exe_version()}")
        self.app.setMinimumSize(1024, 600)
        self.app.resize(1280, 720)

        central = QWidget()
        self.app.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label = QLabel("PySide6 迁移中…")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(16)
        label.setFont(font)
        layout.addWidget(label)

        self._apply_dark_style()

    def _apply_dark_style(self) -> None:
        self._qapp.setStyleSheet("""
            QMainWindow { background-color: #1A1A1A; }
            QLabel { color: #D1D1D1; }
        """)

    def run(self) -> None:
        """启动主事件循环。"""
        self.app.show()
        sys.exit(self._qapp.exec())
