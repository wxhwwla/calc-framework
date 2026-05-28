#!/usr/bin/env python3
"""终末地布局编辑器——独立入口。

可视化编辑 DAG 变量的 layout.json Section。
打包入口：python scripts/build.py --target layout-editor
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget

APP_NAME = "终末地布局编辑器"
APP_VERSION = "1.0.0"


class LayoutEditorApp(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(900, 650)
        self.resize(1100, 750)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(8, 8, 8, 8)

        status = QLabel(f"{APP_NAME} v{APP_VERSION} —— 编辑 DAG 变量排版，导出 layout.json 配置")
        font = QFont()
        font.setPointSize(12)
        status.setFont(font)
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
    window = LayoutEditorApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
