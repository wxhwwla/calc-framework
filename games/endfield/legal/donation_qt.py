#!/usr/bin/env python3
"""自愿捐赠对话框（PySide6 版）。"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from legal.donation_content import (
    DIALOG_FOOTER,
    DIALOG_HEADER,
    DIALOG_INTRO,
    DIALOG_SIZE,
    DIALOG_TITLE,
    DONATION_TIERS,
    WECHAT_QR_PATH,
)


def open_donation_dialog(parent: QWidget | None = None) -> QDialog:
    """打开自愿捐赠对话框。"""
    dialog = QDialog(parent)
    dialog.setWindowTitle(DIALOG_TITLE)
    dialog.resize(*DIALOG_SIZE)
    dialog.setMinimumSize(420, 500)

    outer = QVBoxLayout(dialog)
    outer.setContentsMargins(0, 0, 0, 0)

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QScrollArea.NoFrame)
    outer.addWidget(scroll, stretch=1)

    body = QWidget()
    scroll.setWidget(body)
    lay = QVBoxLayout(body)
    lay.setContentsMargins(16, 12, 16, 12)
    lay.setSpacing(6)

    header = QLabel(DIALOG_HEADER)
    header_font = QFont()
    header_font.setPointSize(14)
    header_font.setBold(True)
    header.setFont(header_font)
    lay.addWidget(header)

    intro = QLabel(DIALOG_INTRO)
    intro.setWordWrap(True)
    intro_font = QFont()
    intro_font.setPointSize(11)
    intro.setFont(intro_font)
    lay.addWidget(intro)
    lay.addSpacing(8)

    for tier in DONATION_TIERS:
        card = QWidget()
        card.setStyleSheet("background-color: #2D2D2D; border-radius: 6px;")
        card.setMinimumHeight(44)
        row = QHBoxLayout(card)
        row.setContentsMargins(12, 8, 12, 8)

        amount_label = QLabel(tier.label)
        amount_font = QFont()
        amount_font.setPointSize(13)
        amount_font.setBold(True)
        amount_label.setFont(amount_font)
        amount_label.setFixedWidth(80)
        row.addWidget(amount_label)

        desc_label = QLabel(tier.description)
        desc_font = QFont()
        desc_font.setPointSize(11)
        desc_label.setFont(desc_font)
        desc_label.setWordWrap(True)
        row.addWidget(desc_label, stretch=1)

        lay.addWidget(card)

    lay.addSpacing(12)

    if WECHAT_QR_PATH.is_file():
        qr_label = QLabel()
        pixmap = QPixmap(str(WECHAT_QR_PATH))
        scaled = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        qr_label.setPixmap(scaled)
        qr_label.setAlignment(Qt.AlignCenter)
        lay.addWidget(qr_label)
    else:
        hint = QLabel("（微信赞赏码图片未找到）")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("color: #888;")
        lay.addWidget(hint)
        path_hint = QLabel(f"请将 wechat_reward.jpg 放置在:\n{WECHAT_QR_PATH}")
        path_hint.setAlignment(Qt.AlignCenter)
        path_hint.setStyleSheet("color: #888; font-size: 10pt;")
        lay.addWidget(path_hint)

    footer = QLabel(DIALOG_FOOTER)
    footer_font = QFont()
    footer_font.setPointSize(11)
    footer.setFont(footer_font)
    footer.setAlignment(Qt.AlignCenter)
    lay.addWidget(footer)
    lay.addSpacing(8)

    close_btn = QPushButton("关闭")
    close_btn.clicked.connect(dialog.accept)
    close_btn.setMinimumHeight(36)
    close_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    lay.addWidget(close_btn, alignment=Qt.AlignCenter)

    dialog.setStyleSheet(
        """
        QDialog { background-color: #1E1E1E; color: #E0E0E0; }
        QLabel { color: #E0E0E0; }
        QPushButton {
            background-color: #2B2B2B; border: 1px solid #555;
            border-radius: 4px; padding: 6px 24px; color: #E0E0E0;
        }
        QPushButton:hover { background-color: #3A3A3A; border-color: #888; }
        QScrollArea { background-color: transparent; }
        """
    )

    return dialog
