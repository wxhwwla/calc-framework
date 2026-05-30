"""共享捐赠组件 — 对话框 + 内嵌 widget。

所有 GUI 应用通过此模块提供自愿捐赠入口。
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

DONATION_TEXT = "感谢使用！如果觉得有用，欢迎通过爱发电支持开发者。"


def open_donation_dialog(parent: QWidget | None = None) -> QDialog:
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
        label = QLabel(self._text)
        label.setWordWrap(True)
        label.setStyleSheet("font-size: 13px; padding: 12px;")
        layout.addWidget(label)
        if self._image_path:
            pixmap = QPixmap(self._image_path)
            if not pixmap.isNull():
                img_label = QLabel()
                img_label.setPixmap(pixmap.scaledToWidth(300, Qt.TransformationMode.SmoothTransformation))
                img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(img_label)
        btn = QPushButton("关闭")
        btn.clicked.connect(dialog.accept)
        layout.addWidget(btn)
        dialog.exec()
