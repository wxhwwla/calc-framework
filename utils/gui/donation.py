# SPDX-License-Identifier: AGPL-3.0
"""共享捐赠组件 — 对话框 + 内嵌 widget。

所有 GUI 应用通过此模块提供自愿捐赠入口（微信赞赏码 + 爱发电，同一弹窗）。

捐赠图片放在 ``resources/donation/`` 目录（格式可混用，按槽位取第一个存在的文件）：
- 微信：``donation_qr.jpg`` / ``donation_q.jpg`` / ``donation_qr.png`` 等
- 爱发电：``afdian_qr.png`` / ``afdian_qr.jpg`` 等

打包时通过 ``--add-data`` 包含整个目录。
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from utils.donation_assets import (
    WECHAT_DONATION_PREFERRED,
    AFDIAN_DONATION_PREFERRED,
    caption_for_donation_path,
    default_wechat_donation_rel,
    resolve_donation_rel_paths,
)
from utils.path_utils import get_resource_path

DONATION_TEXT = (
    "感谢使用！如果觉得有用，欢迎通过微信赞赏或爱发电支持开发者。\n\n"
    "⚠ 捐赠纯属自愿，不构成购买软件的对价，不授予商业使用授权。"
)
DONATION_IMAGE_PATH = default_wechat_donation_rel()

DONATION_IMAGE_FILES: tuple[tuple[str, str], ...] = (
    (WECHAT_DONATION_PREFERRED, "微信赞赏码"),
    (AFDIAN_DONATION_PREFERRED, "爱发电"),
)


def _dialog_image_paths(image_path: str = "") -> list[str]:
    """解析弹窗应展示的图片路径列表。"""
    norm = image_path.replace("\\", "/") if image_path else ""
    resolved = resolve_donation_rel_paths()
    if norm:
        if "assets/" in norm:
            return [image_path]
        if get_resource_path(norm).exists() and norm not in resolved:
            return [image_path]
    if resolved:
        return resolved
    return [image_path] if image_path else [DONATION_IMAGE_PATH]


def _load_image(image_path: str, *, max_width: int = 280) -> QLabel | None:
    full_path = get_resource_path(image_path)
    if not full_path.exists():
        return None
    pixmap = QPixmap(str(full_path))
    if pixmap.isNull():
        return None
    label = QLabel()
    label.setPixmap(pixmap.scaledToWidth(max_width, Qt.TransformationMode.SmoothTransformation))
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return label


def _build_donation_image_row(image_path: str = "", *, max_width: int = 280) -> QWidget:
    container = QWidget()
    row = QHBoxLayout(container)
    row.setAlignment(Qt.AlignmentFlag.AlignCenter)
    row.setSpacing(16)

    paths = _dialog_image_paths(image_path)
    shown = 0
    for path in paths:
        img_label = _load_image(path, max_width=max_width)
        if not img_label:
            continue
        col = QVBoxLayout()
        col.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col.addWidget(img_label)
        cap = QLabel(caption_for_donation_path(path))
        cap.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cap.setStyleSheet("color: #888888; font-size: 12px;")
        col.addWidget(cap)
        row.addLayout(col)
        shown += 1

    if shown == 0:
        hint = QLabel(
            f"暂未配置捐赠二维码（请将微信码如 {WECHAT_DONATION_PREFERRED}、"
            f"爱发电 {AFDIAN_DONATION_PREFERRED} 放入 resources/donation/）"
        )
        hint.setWordWrap(True)
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("color: #888888; font-size: 12px; padding: 8px;")
        row.addWidget(hint)

    return container


def _add_images_to_layout(layout: QVBoxLayout, image_path: str = "") -> None:
    layout.addWidget(_build_donation_image_row(image_path))


def open_donation_dialog(
    parent: QWidget | None = None,
    text: str = DONATION_TEXT,
    image_path: str = "",
) -> QDialog:
    dialog = QDialog(parent)
    dialog.setWindowTitle("自愿捐赠")
    dialog.setMinimumWidth(420)
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


def append_donation_help_menu_action(help_menu: QMenu, parent: QWidget | None = None) -> QAction:
    action = QAction("自愿捐赠(&D)", parent)
    action.triggered.connect(lambda: open_donation_dialog(parent))
    help_menu.addAction(action)
    return action


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
        open_donation_dialog(self, text=self._text, image_path=self._image_path)
