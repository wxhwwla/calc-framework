# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""历史搜索浏览弹窗的 UI 构建（P2-07 从 qt_search_browser.py 拆出）。"""

from __future__ import annotations

from pathlib import Path

from calc_framework.ui.i18n import tr
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTreeWidget,
    QVBoxLayout,
)

__all__ = ["QtSearchBrowserBuildMixin"]

_DARK_BG = "#1E1E1E"

_DARK_FG = "#D1D1D1"

_ACCENT = "#2B6CB6"


class QtSearchBrowserBuildMixin:
    """为 ``SearchHistoryDialog`` 构建标题栏、树控件与底部按钮。"""

    def _build_gui(self, *, big_font: QFont, small_font: QFont) -> None:
        self.setWindowTitle(tr("desktop.endfield.searchBrowserTitle"))

        self.resize(960, 720)

        self.setMinimumSize(640, 480)

        self._big = big_font

        self._small = small_font

        self._all_db_paths: list[Path] = []

        layout = QVBoxLayout(self)  # pyright: ignore[reportArgumentType]

        layout.setContentsMargins(12, 12, 12, 12)

        top_row = QHBoxLayout()

        title = QLabel(tr("desktop.endfield.searchBrowserHeading"))

        title.setFont(big_font)

        title.setStyleSheet(f"color: {_DARK_FG};")

        top_row.addWidget(title)

        top_row.addStretch()

        refresh_btn = QPushButton(tr("common.refresh"))

        refresh_btn.setFont(small_font)

        refresh_btn.setStyleSheet(f"""

            QPushButton {{

                background-color: transparent; color: {_DARK_FG};

                border: 1px solid #464646; border-radius: 6px;

                padding: 6px 20px;

            }}

            QPushButton:hover {{ border-color: {_ACCENT}; color: white; }}

        """)

        refresh_btn.clicked.connect(self._populate)

        top_row.addWidget(refresh_btn)

        copy_btn = QPushButton(tr("desktop.endfield.searchBrowserCopyAll"))

        copy_btn.setFont(small_font)

        copy_btn.setStyleSheet(f"""

            QPushButton {{

                background-color: transparent; color: {_DARK_FG};

                border: 1px solid #464646; border-radius: 6px;

                padding: 6px 20px;

            }}

            QPushButton:hover {{ border-color: {_ACCENT}; color: white; }}

        """)

        copy_btn.clicked.connect(self._copy_all)

        top_row.addWidget(copy_btn)

        layout.addLayout(top_row)

        self._tree = QTreeWidget()

        self._tree.setFont(small_font)

        self._tree.setHeaderLabels(
            [
                tr("desktop.endfield.searchBrowserColRun"),
                tr("desktop.endfield.searchBrowserColStatus"),
                tr("desktop.endfield.searchBrowserColDetails"),
            ]
        )

        self._tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

        self._tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

        self._tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        self._tree.setAlternatingRowColors(True)

        self._tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        self._tree.setStyleSheet(f"""

            QTreeWidget {{

                background-color: {_DARK_BG}; color: {_DARK_FG};

                border: 1px solid #464646; border-radius: 6px;

                padding: 4px;

                alternate-background-color: #252525;

            }}

            QTreeWidget::item {{

                padding: 3px 4px;

                border-bottom: 1px solid #333;

            }}

            QTreeWidget::item:selected {{

                background-color: {_ACCENT}; color: white;

            }}

        """)

        self._tree.setIndentation(20)

        self._tree.setAnimated(True)

        self._tree.itemDoubleClicked.connect(self._on_item_double_clicked)

        layout.addWidget(self._tree, stretch=1)

        btn_row = QHBoxLayout()

        btn_row.addStretch()

        expand_btn = QPushButton(tr("desktop.endfield.searchBrowserExpandAll"))

        expand_btn.setFont(small_font)

        expand_btn.setStyleSheet(f"""

            QPushButton {{

                background-color: transparent; color: {_DARK_FG};

                border: 1px solid #464646; border-radius: 6px;

                padding: 6px 20px;

            }}

            QPushButton:hover {{ border-color: {_ACCENT}; color: white; }}

        """)

        expand_btn.clicked.connect(lambda: self._tree.expandAll())

        btn_row.addWidget(expand_btn)

        collapse_btn = QPushButton(tr("desktop.endfield.searchBrowserCollapseAll"))

        collapse_btn.setFont(small_font)

        collapse_btn.setStyleSheet(f"""

            QPushButton {{

                background-color: transparent; color: {_DARK_FG};

                border: 1px solid #464646; border-radius: 6px;

                padding: 6px 20px;

            }}

            QPushButton:hover {{ border-color: {_ACCENT}; color: white; }}

        """)

        collapse_btn.clicked.connect(lambda: self._tree.collapseAll())

        btn_row.addWidget(collapse_btn)

        close_btn = QPushButton(tr("common.close"))

        close_btn.setFont(small_font)

        close_btn.setStyleSheet(f"""

            QPushButton {{

                background-color: transparent; color: {_DARK_FG};

                border: 1px solid #464646; border-radius: 6px;

                padding: 6px 24px;

            }}

            QPushButton:hover {{ border-color: {_ACCENT}; color: white; }}

        """)

        close_btn.clicked.connect(self.accept)

        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)
