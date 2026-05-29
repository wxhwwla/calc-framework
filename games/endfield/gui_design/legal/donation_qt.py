#!/usr/bin/env python3
"""捐赠对话框。"""

from __future__ import annotations

from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout

from gui_design.legal.donation_content import DONATION_TEXT


def open_donation_dialog(parent=None) -> QDialog:
    dialog = QDialog(parent)
    dialog.setWindowTitle("自愿捐赠")
    dialog.setMinimumWidth(400)

    layout = QVBoxLayout(dialog)
    label = QLabel(DONATION_TEXT)
    label.setWordWrap(True)
    label.setStyleSheet("font-size: 13px; padding: 12px;")
    layout.addWidget(label)

    btn = QPushButton("关闭")
    btn.clicked.connect(dialog.accept)
    layout.addWidget(btn)

    return dialog
