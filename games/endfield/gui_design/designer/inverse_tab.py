#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""公式反推页签：从数值数据反向推导成长公式参数。"""

from __future__ import annotations

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget

_STYLE = """
    QTextEdit { background-color: #1E1E1E; color: #D1D1D1;
                border: 1px solid #464646; border-radius: 4px;
                font-family: Consolas, monospace; font-size: 12px; }
"""


class InverseTab(QWidget):
    def __init__(self, big_font: QFont, small_font: QFont) -> None:
        super().__init__()
        layout = QVBoxLayout(self)

        label = QLabel("公式反推")
        label.setFont(big_font)
        label.setStyleSheet("color: #FF6B6B; padding: 8px 0;")
        layout.addWidget(label)

        hint = QLabel("输入 90 级属性 / 技能 9–12 级数据，自动反推成长公式参数。")
        hint.setFont(small_font)
        hint.setStyleSheet("color: #888888; padding: 4px 0;")
        layout.addWidget(hint)

        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("在此粘贴属性数值...")
        self.text_edit.setStyleSheet(_STYLE)
        layout.addWidget(self.text_edit)

        btn = QPushButton("开始反推")
        btn.setStyleSheet("""
            QPushButton { background-color: #2B6CB6; color: white;
                          border-radius: 6px; padding: 6px 16px; }
            QPushButton:hover { background-color: #346CB0; }
        """)
        btn.clicked.connect(self._invert)
        layout.addWidget(btn)

        self.result_edit = QTextEdit()
        self.result_edit.setReadOnly(True)
        self.result_edit.setStyleSheet(_STYLE)
        layout.addWidget(self.result_edit)

    def _invert(self) -> None:
        self.result_edit.setPlainText("公式反推功能开发中，请直接在源码 calculation/damage/inverse/ 使用 Python API。")
