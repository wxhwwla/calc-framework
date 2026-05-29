#!/usr/bin/env python3
"""终末地设计器——主入口。

PySide6 GUI，提供公式反推、数据浏览等功能，用于角色/武器数据的维护与验证。
"""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QTabWidget, QVBoxLayout, QWidget

from gui_design.designer.data_browser_tab import DataBrowserTab
from gui_design.designer.data_editor_tab import DataEditorTab
from gui_design.designer.inverse_tab import InverseTab

APP_NAME = "终末地设计器"
APP_VERSION = "1.0.0"


class DesignerApp(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(900, 650)
        self.resize(1100, 750)

        self.big_font = QFont()
        self.big_font.setPointSize(14)
        self.big_font.setBold(True)

        self.small_font = QFont()
        self.small_font.setPointSize(12)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(8, 8, 8, 8)

        self.tabs = QTabWidget()
        self.tabs.addTab(InverseTab(self.big_font, self.small_font), "公式反推")
        self.tabs.addTab(DataEditorTab(self.big_font, self.small_font), "数据编辑")
        self.tabs.addTab(DataBrowserTab(self.big_font, self.small_font), "数据浏览")
        layout.addWidget(self.tabs, stretch=1)

        status = QLabel(f"{APP_NAME} v{APP_VERSION} —— 数据维护工具，不包含伤害计算功能")
        status.setFont(self.small_font)
        status.setStyleSheet("color: #888888; padding: 4px 8px;")
        status.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(status)

        self._apply_dark_style()

    def _apply_dark_style(self) -> None:
        self.setStyleSheet("""
            QMainWindow { background-color: #1A1A1A; }
            QWidget { background-color: #1A1A1A; }
            QLabel { color: #D1D1D1; }
        """)


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = DesignerApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
