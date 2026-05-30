"""通用帮助对话框 — 在 GUI 内打开结构化的使用说明。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)


@dataclass
class HelpSection:
    """帮助文档中的一个分类。"""
    category: str
    title: str
    content: str
    sub_sections: list[HelpSection] = field(default_factory=list)


class HelpDialog(QDialog):
    """结构化的帮助文档对话框。

    左侧是分类树导航，右侧是文档内容展示区。
    可通过 ``show_help(parent, build_tree)`` 快捷调用。
    """

    def __init__(
        self,
        build_tree: Callable[[], list[HelpSection]],
        parent: QWidget | None = None,
        title: str = "使用说明",
    ) -> None:
        super().__init__(parent)
        self._build_tree = build_tree
        self.setWindowTitle(title)
        self.resize(900, 650)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setMinimumWidth(200)
        self._tree.setMaximumWidth(320)
        self._tree.setFont(QFont("Microsoft YaHei", 10))
        self._tree.setStyleSheet("""
            QTreeWidget {
                border: none;
                background: #2b2b2b;
                color: #d4d4d4;
            }
            QTreeWidget::item:selected {
                background: #094771;
                color: #ffffff;
            }
            QTreeWidget::item:hover {
                background: #3c3c3c;
            }
        """)
        self._tree.itemClicked.connect(self._on_item_clicked)
        splitter.addWidget(self._tree)

        self._browser = QTextBrowser()
        self._browser.setFont(QFont("Microsoft YaHei", 10))
        self._browser.setStyleSheet("""
            QTextBrowser {
                border: none;
                background: #1e1e1e;
                color: #d4d4d4;
                padding: 16px;
            }
            QTextBrowser h2 {
                color: #4fc3f7;
                border-bottom: 1px solid #333;
                padding-bottom: 6px;
            }
            QTextBrowser h3 {
                color: #81c784;
            }
            QTextBrowser h4 {
                color: #ffb74d;
            }
            QTextBrowser a {
                color: #4fc3f7;
            }
            QTextBrowser code {
                color: #ce9178;
                background: #2d2d2d;
                padding: 1px 4px;
                border-radius: 3px;
            }
            QTextBrowser pre {
                background: #2d2d2d;
                color: #dcdcaa;
                padding: 8px;
                border-radius: 4px;
                font-family: Consolas, monospace;
            }
            QTextBrowser table {
                background: #2d2d2d;
                color: #d4d4d4;
            }
            QTextBrowser th {
                background: #094771;
                color: #ffffff;
                padding: 4px 8px;
            }
            QTextBrowser td {
                padding: 4px 8px;
                border: 1px solid #3c3c3c;
            }
            QTextBrowser ul, ol {
                margin-left: 12px;
            }
            QTextBrowser li {
                margin: 4px 0;
            }
        """)
        self._browser.setOpenExternalLinks(True)
        QShortcut(QKeySequence(Qt.Key.Key_Escape), self).activated.connect(self.accept)
        splitter.addWidget(self._browser)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([250, 650])
        layout.addWidget(splitter, 1)

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(8, 8, 8, 8)
        btn_layout.addStretch()
        close_btn = QPushButton("关闭")
        close_btn.setFont(QFont("Microsoft YaHei", 10))
        close_btn.setFixedSize(100, 32)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        self._populate_tree()

    def _populate_tree(self) -> None:
        sections = self._build_tree()
        for section in sections:
            top_item = QTreeWidgetItem([section.category])
            top_item.setData(0, Qt.ItemDataRole.UserRole, section)
            top_font = QFont("Microsoft YaHei", 10, QFont.Weight.Bold)
            top_item.setFont(0, top_font)

            all_items = [section] + section.sub_sections
            for sub in all_items:
                child = QTreeWidgetItem([sub.title])
                child.setData(0, Qt.ItemDataRole.UserRole, sub)
                if sub != section:
                    top_item.addChild(child)

            self._tree.addTopLevelItem(top_item)

        self._tree.expandAll()

        first = self._tree.topLevelItem(0)
        if first:
            first_child = first.child(0) or first
            self._tree.setCurrentItem(first_child)
            self._show_content(first_child)

    def _on_item_clicked(self, item: QTreeWidgetItem, _column: int) -> None:
        self._show_content(item)

    def _show_content(self, item: QTreeWidgetItem) -> None:
        section: HelpSection | None = item.data(0, Qt.ItemDataRole.UserRole)
        if section is None:
            return
        html = section.content
        if section.sub_sections:
            html += "<hr><h3>本分类下的更多内容</h3><ul>"
            for sub in section.sub_sections:
                html += f"<li><b>{sub.title}</b></li>"
            html += "</ul>"
        self._browser.setHtml(html)
