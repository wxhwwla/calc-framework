# SPDX-License-Identifier: AGPL-3.0
"""共享捐赠组件 — 对话框 + 内嵌 widget。

所有 GUI 应用通过此模块提供自愿捐赠入口。

捐赠图片放在 ``resources/donation/`` 目录：
- ``donation_qr.png`` — 微信赞赏码
- ``afdian_qr.png`` — 爱发电

打包时通过 ``--add-data`` 包含整个目录。
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from utils.path_utils import get_resource_path

DONATION_TEXT = (
    "感谢使用！如果觉得有用，欢迎通过微信赞赏或爱发电支持开发者。\n\n"
    "⚠ 捐赠纯属自愿，不构成购买软件的对价，不授予商业使用授权。"
)
DONATION_IMAGE_PATH = "resources/donation/donation_qr.png"

# (文件名, 展示标签)
DONATION_IMAGE_FILES: tuple[tuple[str, str], ...] = (
    ("donation_qr.png", "微信赞赏码"),
    ("afdian_qr.png", "爱发电"),
)


def _default_donation_rel_paths() -> list[str]:
    return [f"resources/donation/{name}" for name, _ in DONATION_IMAGE_FILES]


def _dialog_image_paths(image_path: str = "") -> list[str]:
    """解析弹窗应展示的图片路径列表。"""
    norm = image_path.replace("\\", "/") if image_path else ""
    default_rels = _default_donation_rel_paths()
    if norm and "assets/" in norm:
        return [image_path]
    if norm and norm not in default_rels:
        return [image_path]
    paths: list[str] = []
    for rel in default_rels:
        if get_resource_path(rel).exists():
            paths.append(rel)
    if paths:
        return paths
    return [image_path] if image_path else [DONATION_IMAGE_PATH]


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


def _add_images_to_layout(layout: QVBoxLayout, image_path: str = "") -> None:
    for path in _dialog_image_paths(image_path):
        img_label = _load_image(path)
        if img_label:
            layout.addWidget(img_label)


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

    _add_images_to_layout(layout, image_path)

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

        _add_images_to_layout(layout, self._image_path)

        label = QLabel(self._text)
        label.setWordWrap(True)
        label.setStyleSheet("font-size: 13px; padding: 12px;")
        layout.addWidget(label)

        btn = QPushButton("关闭")
        btn.clicked.connect(dialog.accept)
        layout.addWidget(btn)
        dialog.exec()
