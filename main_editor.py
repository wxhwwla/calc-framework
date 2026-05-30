#!/usr/bin/env python3
"""
布局编辑器 — 独立入口

可视化编排 DAG 变量到 layout.json 节。
任何人都可直接使用（无需 Python 环境），编辑后导出配置给计算器使用。

使用方式：
    python main_editor.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

_REPO_ROOT = Path(__file__).resolve().parent
_FRAMEWORK_SRC = _REPO_ROOT / "framework" / "src"
if str(_FRAMEWORK_SRC) not in sys.path:
    sys.path.insert(0, str(_FRAMEWORK_SRC))

_ADAPTER_DIR = _REPO_ROOT / "framework" / "adapters" / "endfield"
_DAG_PATH = _FRAMEWORK_SRC / "calc_framework" / "configs" / "endfield_full.dag.json"

from calc_framework.editor.gui import LayoutEditorWidget

APP_NAME = "布局编辑器"
APP_VERSION = "1.0.0"


class LayoutEditorApp(QMainWindow):
    """布局编辑器主窗口。"""

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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QLabel(f"  {APP_NAME} v{APP_VERSION}")
        header.setFixedHeight(36)
        header.setFont(self.big_font)
        header.setStyleSheet("background: #2d2d2d; color: #eee; padding-left: 12px;")
        header.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(header)

        self.editor = LayoutEditorWidget(dag_path=str(_DAG_PATH))
        layout.addWidget(self.editor, 1)


def main() -> None:
    app = QApplication(sys.argv)
    window = LayoutEditorApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
