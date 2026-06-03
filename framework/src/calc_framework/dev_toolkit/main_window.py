# SPDX-License-Identifier: AGPL-3.0
"""开发者工具箱主窗口 — 左侧导航 + 右侧 QStackedWidget 内容区。"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from calc_framework.logging import get_logger

logger = get_logger(__name__)


# ── 页面适配器注册 ──────────────────────────────────────

_PAGE_REGISTRY: dict[str, type[QWidget]] = {}


def _register_page(page_id: str, widget_class: type[QWidget]) -> None:
    _PAGE_REGISTRY[page_id] = widget_class


# ── 分类条目定义 ────────────────────────────────────────

# (page_id, label, group)
_PAGE_DEFS: list[tuple[str, str, str]] = [
    ("data_editor", "数据编辑", "📦 配置"),
    ("layout_editor", "布局编辑", "📦 配置"),
    ("export_pack", "导出打包", "📦 配置"),
    ("graph_editor", "图编辑器", "🔧 开发"),
    ("dag_debugger", "DAG 调试器", "🔧 开发"),
    ("calcpack_viewer", "计算包查看", "🔧 开发"),
    ("ai_generator", "AI 生成器", "🔧 开发"),
    ("ocr_label", "OCR 标注", "🔧 开发"),
]


class _SidebarWidget(QWidget):
    """左侧导航栏（分组列表）。"""

    SEPARATOR_ROLE = Qt.ItemDataRole.UserRole + 99

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedWidth(180)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QLabel("  工具")
        header.setProperty("heading", True)
        header.setFixedHeight(32)
        layout.addWidget(header)

        self._list = QListWidget()
        self._list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._populate()
        layout.addWidget(self._list)

    def _populate(self) -> None:
        current_group = ""
        for page_id, label, group in _PAGE_DEFS:
            if group != current_group:
                current_group = group
                item = QListWidgetItem(group)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                item.setData(self.SEPARATOR_ROLE, True)
                self._list.addItem(item)
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, page_id)
            self._list.addItem(item)

    @property
    def list_widget(self) -> QListWidget:
        return self._list


def _read_framework_version() -> str:
    try:
        root = Path(__file__).resolve().parents[4]
        sys.path.insert(0, str(root))
        from scripts.please_read_me import _VERSION

        return str(_VERSION)
    except Exception:
        return "?"


class DevToolkitWindow(QMainWindow):
    """开发者工具箱主窗口。"""

    def __init__(self) -> None:
        super().__init__()
        version = _read_framework_version()
        self.setWindowTitle(f"开发者工具箱 v0.1.0")
        self.resize(1400, 900)

        # ── 中央区域：侧栏 + 分割器 + 内容 ──
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self._sidebar = _SidebarWidget()
        root_layout.addWidget(self._sidebar)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        root_layout.addWidget(splitter, stretch=1)

        # ── 右侧空白提示 / 内容区 ──
        self._stack = QStackedWidget()
        self._init_pages()
        splitter.addWidget(self._stack)

        # ── 连接导航 ──
        self._sidebar.list_widget.currentItemChanged.connect(self._on_item_changed)

        # ── 状态栏 ──
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status_label = QLabel(f"框架 v{version}")
        self._status.addPermanentWidget(self._status_label)
        self._status.showMessage("就绪", 5000)

        # 默认选中第一项
        self._sidebar.list_widget.setCurrentRow(1 if _PAGE_DEFS else 0)

    def _init_pages(self) -> None:
        """懒加载所有页面。"""
        self._pages: dict[str, QWidget] = {}
        self._page_order: list[str] = []
        for page_id, label, group in _PAGE_DEFS:
            self._page_order.append(page_id)

    def _ensure_page(self, page_id: str) -> QWidget:
        """确保页面已创建并返回。"""
        if page_id in self._pages:
            return self._pages[page_id]

        cls = _PAGE_REGISTRY.get(page_id)
        if cls is None:
            w = QLabel(f"页面未注册: {page_id}")
        else:
            try:
                w = cls(self)
            except Exception as exc:
                logger.exception("加载页面失败: %s", page_id)
                w = QLabel(f"加载失败: {exc}")

        self._pages[page_id] = w
        self._stack.addWidget(w)
        return w

    def _on_item_changed(self, current: QListWidgetItem | None, _previous: Any) -> None:
        if current is None:
            return
        page_id = current.data(Qt.ItemDataRole.UserRole)
        if page_id is None:
            return
        w = self._ensure_page(page_id)
        self._stack.setCurrentWidget(w)
        self._status.showMessage(current.text(), 3000)


def main() -> None:
    """启动开发者工具箱。"""
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("开发者工具箱")
    window = DevToolkitWindow()
    window.show()
    sys.exit(app.exec())
