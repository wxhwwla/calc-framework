#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""数据编辑页签：新增/编辑/删除角色、武器、装备。"""

from __future__ import annotations

from calc_framework.ui.i18n import tr
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget

_STYLE = """

    QTextEdit { background-color: #1E1E1E; color: #D1D1D1;

                border: 1px solid #464646; border-radius: 4px;

                font-family: Consolas, monospace; font-size: 12px; }

"""


class DataEditorTab(QWidget):
    def __init__(self, big_font: QFont, small_font: QFont) -> None:
        super().__init__()

        layout = QVBoxLayout(self)

        label = QLabel(tr("desktop.designer.dataEditorTitle"))

        label.setFont(big_font)

        label.setStyleSheet("color: #FF6B6B; padding: 8px 0;")

        layout.addWidget(label)

        hint = QLabel(tr("desktop.designer.dataEditorHint"))

        hint.setFont(small_font)

        hint.setStyleSheet("color: #888888; padding: 4px 0;")

        layout.addWidget(hint)

        self.text_edit = QTextEdit()

        self.text_edit.setReadOnly(True)

        self.text_edit.setStyleSheet(_STYLE)

        self.text_edit.setPlainText(tr("desktop.designer.dataEditorBody"))

        layout.addWidget(self.text_edit)

        btn = QPushButton(tr("desktop.designer.refreshCache"))

        btn.setStyleSheet("""

            QPushButton { background-color: #2B6CB6; color: white;

                          border-radius: 6px; padding: 6px 16px; }

            QPushButton:hover { background-color: #346CB0; }

        """)

        layout.addWidget(btn)
        """初始化实例。"""

    """DataEditorTab。"""
