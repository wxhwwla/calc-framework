#!/usr/bin/env python3
"""
终末地布局编辑器 — 独立入口

可视化编排 DAG 变量到 layout.json Section。
任何人都可直接使用（无需 Python 环境），编辑后导出配置给计算器使用。

打包入口：python build.py --target layout-editor
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

# ── 框架路径 ──────────────────────────
_FRAMEWORK_SRC = Path(__file__).resolve().parents[1] / "framework" / "src"
if str(_FRAMEWORK_SRC) not in sys.path:
    sys.path.insert(0, str(_FRAMEWORK_SRC))

_ADAPTER_DIR = Path(__file__).resolve().parents[1] / "framework" / "adapters" / "endfield"
_DAG_PATH = _ADAPTER_DIR.parent.parent / "src" / "calc_framework" / "configs" / "endfield_full.dag.json"

from calc_framework.editor.gui import LayoutEditorWidget

APP_NAME = "终末地布局编辑器"
APP_VERSION = "1.0.0"


class LayoutEditorApp(QMainWindow):
    """布局编辑器主窗口。

    自动加载终末地 DAG，也可通过「加载 DAG」按钮切换其他适配包。
    """

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

        self.editor = LayoutEditorWidget()
        layout.addWidget(self.editor, stretch=1)

        status = QLabel(f"{APP_NAME} v{APP_VERSION} — 编辑 DAG 变量排版，导出 layout.json 配置")
        status.setFont(self.small_font)
        status.setStyleSheet("color: #888888; padding: 4px 8px;")
        status.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(status)

        self._apply_dark_style()

        self._load_default_dag()

    def _apply_dark_style(self) -> None:
        self.setStyleSheet("""
            QMainWindow { background-color: #1A1A1A; }
            QWidget { background-color: #1A1A1A; }
            QLabel { color: #D1D1D1; }
        """)

    def _load_default_dag(self) -> None:
        """启动时自动加载终末地 DAG。"""
        dag_path = _DAG_PATH.resolve()
        if dag_path.is_file():
            try:
                self.editor.load_dag_file(str(dag_path))
                self.setWindowTitle(f"{APP_NAME} v{APP_VERSION} — {dag_path.name}")
            except Exception as exc:
                status = self.findChild(QLabel)
                if status:
                    status.setText(f"自动加载 DAG 失败: {exc}")
        else:
            status = self.findChild(QLabel)
            if status:
                status.setText(f"DAG 文件未找到: {dag_path}，请手动加载")


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = LayoutEditorApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
