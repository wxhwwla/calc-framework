# SPDX-License-Identifier: AGPL-3.0
"""TEMPLATE（{Game}）桌面 GUI — QMainWindow 骨架。

TODO:
  - 替换 _template_App.py 文件名为 your_game_App.py
  - 替换类名 TEMPLATEDamageApp 为 YourGameDamageApp
  - 实现 UI 布局：角色选择、参数输入、计算结果展示
  - 可选用 framework.ui.compute_sheet.ComputeSheet 渲染 DAG 变量
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# TODO: 按需取消注释
# from framework.ui.compute_sheet import ComputeSheet
# from . import _path_setup  # noqa: F401


class TEMPLATEDamageApp(QMainWindow):
    """{Game} 桌面伤害计算器骨架。"""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("{Game} 伤害计算器")
        self.setMinimumSize(800, 600)
        self.resize(1024, 768)
        self._setup_ui()

    def _setup_ui(self) -> None:
        cw = QWidget()
        self.setCentralWidget(cw)
        lo = QVBoxLayout(cw)

        title = QLabel("{Game} 伤害计算器")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 12px;")
        lo.addWidget(title)

        # TODO: 在此处添加 ComputeSheet 或其他计算控件
        # sheet = ComputeSheet(self)
        # sheet.load_layout("framework/adapters/_template/ui/layout.json")
        # lo.addWidget(sheet, stretch=1)

        compute_btn = QPushButton("计算")
        compute_btn.clicked.connect(self._on_compute)
        lo.addWidget(compute_btn)

        result_label = QLabel("结果将显示在此处")
        result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lo.addWidget(result_label)

    def _on_compute(self) -> None:
        """计算按钮回调。"""
        # TODO: 调用 compute_snapshot_with_dag() 并展示结果
        pass


def main() -> None:
    """应用入口。"""
    import sys

    # TODO: 配置 sys.path（参照 games/arknights/main.py 的 _path_setup 模式）
    app = QApplication(sys.argv)
    window = TEMPLATEDamageApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
