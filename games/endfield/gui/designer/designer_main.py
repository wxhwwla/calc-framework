#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""数据设计器——主入口。



PySide6 GUI，提供公式反推、数据浏览等功能，用于角色/武器数据的维护与验证。

"""



from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from gui.designer.data_browser_tab import DataBrowserTab
from gui.designer.data_editor_tab import DataEditorTab
from gui.designer.inverse_tab import InverseTab

APP_NAME = "数据设计器"

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



        bottom_bar = QHBoxLayout()

        bottom_bar.setContentsMargins(0, 4, 0, 0)



        status = QLabel(f"{APP_NAME} v{APP_VERSION} —— 数据维护工具，不包含伤害计算功能")

        status.setFont(self.small_font)

        status.setStyleSheet("color: #888888; padding: 4px 8px;")

        status.setAlignment(Qt.AlignmentFlag.AlignLeft)

        bottom_bar.addWidget(status, stretch=1)



        self.help_btn = QPushButton("📖 使用说明")

        self.help_btn.setFont(self.small_font)

        self.help_btn.setStyleSheet("""

            QPushButton {

                background-color: transparent; color: #D1D1D1;

                border: 1px solid #464646; border-radius: 4px;

                padding: 4px 12px; min-height: 24px;

            }

            QPushButton:hover { border-color: #2B6CB6; color: white; }

        """)

        self.help_btn.clicked.connect(self._open_help)

        bottom_bar.addWidget(self.help_btn)

        self.donation_btn = QPushButton("🤝 自愿捐赠")

        self.donation_btn.setFont(self.small_font)

        self.donation_btn.setStyleSheet("""

            QPushButton {

                background-color: transparent; color: #D1D1D1;

                border: 1px solid #464646; border-radius: 4px;

                padding: 4px 12px; min-height: 24px;

            }

            QPushButton:hover { border-color: #c0392b; color: #e74c3c; }

        """)

        self.donation_btn.clicked.connect(self._open_donation)

        bottom_bar.addWidget(self.donation_btn)



        layout.addLayout(bottom_bar)



        self._apply_dark_style()



    def _open_help(self) -> None:

        from utils.gui.help_designer import build_designer_help
        from utils.gui.help_dialog import HelpDialog

        dialog = HelpDialog(build_designer_help, self, title="数据设计器 使用说明")

        dialog.exec()

    def _open_donation(self) -> None:

        from utils.gui.donation import open_donation_dialog

        open_donation_dialog(self)



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

