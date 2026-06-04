#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""

数据设计器 — 主入口



PySide6 GUI，提供公式反推、数据浏览等功能。

用于角色/武器数据的维护与验证，不包含伤害计算。



打包入口：python build.py --target designer

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
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


from endfield_designer.data_browser_tab import DataBrowserTab

from endfield_designer.data_editor_tab import DataEditorTab

from endfield_designer.inverse_tab import InverseTab

from endfield_designer.seed_tab import SeedTab


from utils.gui.donation import open_donation_dialog


APP_NAME = "数据设计器"

APP_VERSION = "1.0.0"


class DesignerApp(QMainWindow):
    """DesignerApp 类。"""

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

        self.tabs.addTab(SeedTab(self.big_font, self.small_font), "数据录入")

        self.tabs.addTab(DataEditorTab(self.big_font, self.small_font), "数据编辑")

        self.tabs.addTab(DataBrowserTab(self.big_font, self.small_font), "数据浏览")

        layout.addWidget(self.tabs, stretch=1)

        bottom_bar = QHBoxLayout()

        bottom_bar.setContentsMargins(0, 4, 0, 0)

        self._bwiki_btn = QPushButton("从 BWIKI 同步数据")

        self._bwiki_btn.setFont(self.small_font)

        self._bwiki_btn.setStyleSheet("""

            QPushButton { background-color: #276749; color: white;

                          border: none; border-radius: 6px; padding: 6px 16px; }

            QPushButton:hover { background-color: #38A169; }

        """)

        self._bwiki_btn.clicked.connect(self._sync_bwiki)

        bottom_bar.addWidget(self._bwiki_btn)

        bottom_bar.addStretch()

        donation_btn = QPushButton("自愿捐赠")

        donation_btn.setFont(self.small_font)

        donation_btn.setStyleSheet("""

            QPushButton { background-color: #c0392b; color: white;

                          border: none; border-radius: 6px; padding: 6px 16px; }

            QPushButton:hover { background-color: #e74c3c; }

        """)

        donation_btn.clicked.connect(lambda: open_donation_dialog(self))

        bottom_bar.addWidget(donation_btn)

        status = QLabel(f"{APP_NAME} v{APP_VERSION} — 数据维护工具，不包含伤害计算功能")

        status.setFont(self.small_font)

        status.setStyleSheet("color: #888888; padding: 4px 8px;")

        status.setAlignment(Qt.AlignmentFlag.AlignLeft)

        bottom_bar.addWidget(status, stretch=1)

        layout.addLayout(bottom_bar)

        self._apply_dark_style()

    def _sync_bwiki(self) -> None:
        """执行 BWIKI 数据同步。"""

        try:
            from tools.bwiki_scout.sync_all import main as bwiki_main

        except ImportError:
            QMessageBox.critical(self, "同步失败", "BWIKI 同步模块未安装")

            return

        self._bwiki_btn.setEnabled(False)

        self._bwiki_btn.setText("同步中...")

        try:
            result = bwiki_main()

            if result == 0:
                QMessageBox.information(self, "BWIKI 同步", "数据同步完成！\n可在「数据浏览」页签查看最新数据。")

            else:
                QMessageBox.warning(
                    self, "BWIKI 同步", f"同步完成，但有警告（返回值: {result}）。\n可在命令行查看详情。"
                )

        except Exception as e:
            QMessageBox.critical(self, "同步失败", f"BWIKI 同步出错:\n{e}")

        finally:
            self._bwiki_btn.setEnabled(True)

            self._bwiki_btn.setText("从 BWIKI 同步数据")

    def _apply_dark_style(self) -> None:
        """_apply_dark_style 实现。"""
        self.setStyleSheet("""

            QMainWindow { background-color: #1A1A1A; }

            QWidget { background-color: #1A1A1A; }

            QLabel { color: #D1D1D1; }

            QTabWidget::pane {

                border: 1px solid #464646;

                border-radius: 8px;

                background-color: #1A1A1A;

                top: -1px;

            }

            QTabBar::tab {

                background-color: #2B2B2B;

                color: #D1D1D1;

                border: 1px solid #464646;

                border-bottom: none;

                border-top-left-radius: 6px;

                border-top-right-radius: 6px;

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


def main() -> None:
    """CLI 入口。"""
    app = QApplication(sys.argv)

    app.setStyle("Fusion")

    window = DesignerApp()

    window.showMaximized()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
