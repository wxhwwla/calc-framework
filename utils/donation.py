# SPDX-License-Identifier: AGPL-3.0
"""共享捐赠组件 — 对话框 + 内嵌 widget。

所有 GUI 应用通过此模块提供自愿捐赠入口。

捐赠图片应放在 ``resources/donation/`` 目录下，打包时自动包含。
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from utils.path_utils import get_resource_path

DONATION_TEXT = "感谢使用！如果觉得有用，欢迎通过爱发电支持开发者。\n\n⚠ 捐赠纯属自愿，不构成购买软件的对价，不授予商业使用授权。"
DONATION_IMAGE_PATH = "resources/donation/donation_qr.png"


def _load_image(image_path: str) -> QLabel | None:
    """加载图片并返回 QLabel，加载失败返回 None。"""
    full_path = get_resource_path(image_path)
    if not full_path.exists():
        return None
    pixmap = QPixmap(str(full_path))
    if pixmap.isNull():
        return None
    label = QLabel()
    label.setPixmap(pixmap.scaledToWidth(300, Qt.TransformationMode.SmoothTransformation))
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return label


def open_donation_dialog(
    parent: QWidget | None = None,
    text: str = DONATION_TEXT,
    image_path: str = "",
) -> QDialog:
    """打开捐赠对话框。"""
    dialog = QDialog(parent)
    dialog.setWindowTitle("自愿捐赠")
    dialog.setMinimumWidth(400)
    layout = QVBoxLayout(dialog)

    img_label = _load_image(image_path or DONATION_IMAGE_PATH)
    if img_label:
        layout.addWidget(img_label)

    label = QLabel(text)
    label.setWordWrap(True)
    label.setStyleSheet("font-size: 13px; padding: 12px;")
    layout.addWidget(label)

    btn = QPushButton("关闭")
    btn.clicked.connect(dialog.accept)
    layout.addWidget(btn)
    dialog.exec()
    return dialog


class DonationWidget(QWidget):
    """可嵌入布局的捐赠组件，支持自定义文字和图片。"""

    def __init__(
        self,
        text: str = DONATION_TEXT,
        image_path: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._text = text
        self._image_path = image_path

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet("font-size: 13px; color: #888;")
        layout.addWidget(label, stretch=1)

        btn = QPushButton("自愿捐赠")
        btn.setFixedWidth(100)
        btn.clicked.connect(self._open_dialog)
        btn.setStyleSheet("""
            QPushButton {
                background: #c0392b; color: white; border: none;
                border-radius: 4px; padding: 6px 12px;
                font-size: 13px;
            }
            QPushButton:hover { background: #e74c3c; }
        """)
        layout.addWidget(btn)

    def _open_dialog(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("自愿捐赠")
        layout = QVBoxLayout(dialog)

        img_label = _load_image(self._image_path) if self._image_path else None
        if img_label:
            layout.addWidget(img_label)

        label = QLabel(self._text)
        label.setWordWrap(True)
        label.setStyleSheet("font-size: 13px; padding: 12px;")
        layout.addWidget(label)

        btn = QPushButton("关闭")
        btn.clicked.connect(dialog.accept)
        layout.addWidget(btn)
        dialog.exec()
