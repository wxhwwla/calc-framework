#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PySide6 主应用壳层（阶段 1）。

布局：双页签（计算页 / 高级页）。
高级页已嵌入 QtControlDock（操作/搜索/多技能三列）。
"""

from __future__ import annotations

import sys
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from gui_design.shared.gui_settings import gui_settings
from gui_design.shell.qt_control_dock import QtControlDock
from please_read_me import get_exe_version


class QtDamageApp:
    """PySide6 主应用。

    属性：
        app: QMainWindow 实例（与 CTk 版 ``DamageCalculatorApp.app`` 语义一致）
        big_font: 标题/主按钮字体（14px bold）
        small_font: 正文/次按钮字体（12px normal）
        tabs: 双页签
        control_dock: 高级页控制栏（QtControlDock 实例）
    """

    def __init__(self) -> None:
        gui_settings()

        self._qapp: QApplication = QApplication(sys.argv)
        self._qapp.setStyle("Fusion")
        self._apply_dark_style()

        self.big_font: QFont = QFont()
        self.big_font.setPointSize(14)
        self.big_font.setBold(True)

        self.small_font: QFont = QFont()
        self.small_font.setPointSize(12)

        self.app: QMainWindow = QMainWindow()
        self.app.setWindowTitle(f"终末地伤害计算小工具 v{get_exe_version()}")
        self.app.setMinimumSize(1024, 600)
        self.app.resize(1280, 720)

        central = QWidget()
        self.app.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(0)

        # ── 双页签 ────────────────────────────────
        self.tabs: QTabWidget = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        self._style_tabs()
        main_layout.addWidget(self.tabs, stretch=1)

        # 计算页（占位符）
        calc_page = QWidget()
        calc_layout = QVBoxLayout(calc_page)
        calc_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        calc_label = QLabel("计算页 — 待迁移")
        calc_label.setFont(self.big_font)
        calc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        calc_layout.addWidget(calc_label)
        self.tabs.addTab(calc_page, "计算页")

        # 高级页 → 三列控制栏
        self.control_dock: QtControlDock = QtControlDock(
            big_font=self.big_font,
            small_font=self.small_font,
            on_back_to_main=self._show_main_page,
            on_confirm=self._on_confirm,
            on_attribution=self._on_attribution,
        )

        # 控制栏居中于高级页，不拉伸宽度
        adv_page = QWidget()
        adv_layout = QHBoxLayout(adv_page)
        adv_layout.setContentsMargins(0, 0, 0, 0)
        adv_layout.addWidget(self.control_dock, stretch=1)
        self.control_dock.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.tabs.addTab(adv_page, "高级页")

    def run(self) -> None:
        """启动主事件循环。"""
        self.app.show()
        sys.exit(self._qapp.exec())

    # ── 内部方法 ──────────────────────────────────

    def _apply_dark_style(self) -> None:
        self._qapp.setStyleSheet("""
            QMainWindow { background-color: #1A1A1A; }
            QWidget { background-color: #1A1A1A; }
            QLabel { color: #D1D1D1; }
        """)

    def _style_tabs(self) -> None:
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #464646;
                border-radius: 16px;
                background-color: #1A1A1A;
                top: -1px;
            }
            QTabBar::tab {
                background-color: #2B2B2B;
                color: #D1D1D1;
                border: 1px solid #464646;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 6px 16px;
                margin-right: 2px;
                font-size: 13px;
            }
            QTabBar::tab:selected {
                background-color: #2B6CB6;
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background-color: #333333;
            }
        """)

    def _show_main_page(self) -> None:
        """切换到计算页。"""
        self.tabs.setCurrentIndex(0)

    def _on_confirm(self) -> None:
        """确认选择（占位符，后续迁移 handle_confirm）。"""
        QMessageBox.information(self.app, "确认选择", "确认功能待迁移")

    def _on_attribution(self) -> None:
        """数据来源与许可（占位符，后续迁移 attribution dialog）。"""
        QMessageBox.information(
            self.app,
            "数据来源与许可",
            "数据来源与许可说明待迁移",
        )
