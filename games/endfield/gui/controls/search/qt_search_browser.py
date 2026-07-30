#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""历史搜索记录浏览对话框（search_output/ SQLite 快速搜装）。"""

from __future__ import annotations

from pathlib import Path

from calc_framework.ui.i18n import tr
from PySide6.QtCore import Qt
from PySide6.QtGui import QClipboard, QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

# 数据层已提取到 search_history_data.py（无 PySide6 依赖）
from .search_history_data import (
    RunInfo,
    ScoreInfo,
    format_clipboard_text,
    format_loadout_line,
    human_size,
    list_runs,
    list_scores,
    scan_search_output,
)

_DARK_BG = "#1E1E1E"

_DARK_FG = "#D1D1D1"

_ACCENT = "#2B6CB6"

_SCORE_FG = QColor("#9BB9E0")

_DMG_FG = QColor("#85C1A8")


class SearchHistoryDialog(QDialog):
    """历史搜索记录浏览弹窗。"""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        big_font: QFont,
        small_font: QFont,
    ) -> None:
        super().__init__(parent)

        self.setWindowTitle(tr("desktop.endfield.searchBrowserTitle"))

        self.resize(960, 720)

        self.setMinimumSize(640, 480)

        self._big = big_font

        self._small = small_font

        self._all_db_paths: list[Path] = []

        layout = QVBoxLayout(self)

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

        self._populate()
        """初始化实例。"""

    def _populate(self) -> None:
        self._tree.clear()

        self._all_db_paths = scan_search_output()

        if not self._all_db_paths:
            item = QTreeWidgetItem(
                [
                    tr("desktop.endfield.searchBrowserEmpty"),
                    "",
                    tr("desktop.endfield.searchBrowserEmptyHint"),
                ]
            )

            item.setFlags(Qt.ItemFlag.ItemIsEnabled)

            self._tree.addTopLevelItem(item)

            return

        for db_path in self._all_db_paths:
            db_name = f"{db_path.parent.name} ({human_size(db_path)})"

            db_item = QTreeWidgetItem(
                [db_name, "", tr("desktop.endfield.searchBrowserPathDetail", path=db_path.parent)]
            )

            db_item.setFlags(Qt.ItemFlag.ItemIsEnabled)

            db_item.setData(0, Qt.ItemDataRole.UserRole, str(db_path))

            self._tree.addTopLevelItem(db_item)

            runs = list_runs(db_path)

            if not runs:
                empty = QTreeWidgetItem([tr("desktop.endfield.searchBrowserNoRuns"), "", ""])

                empty.setFlags(Qt.ItemFlag.ItemIsEnabled)

                db_item.addChild(empty)

                continue

            for run in runs:
                status_icon = {"completed": "✅", "cancelled": "⏹️", "running": "▶️"}.get(run.status, "❓")

                run_text = f"{run.signature[:40]}…" if len(run.signature) > 40 else run.signature

                status_text = f"{status_icon} {run.status}  {run.processed_combinations}/{run.total_combinations}"

                run_item = QTreeWidgetItem([run_text, status_text, ""])

                run_item.setFlags(Qt.ItemFlag.ItemIsEnabled)

                run_item.setData(0, Qt.ItemDataRole.UserRole, run.signature)

                run_item.setData(1, Qt.ItemDataRole.UserRole, str(db_path))

                db_item.addChild(run_item)

                scores = list_scores(db_path, run.signature)

                for idx, sc in enumerate(scores, start=1):
                    score_text = format_loadout_line(sc)

                    child = QTreeWidgetItem(
                        [tr("desktop.endfield.rankNth", idx=idx), f"{sc.final_damage:.1f}", score_text]
                    )

                    child.setForeground(0, _SCORE_FG)

                    child.setForeground(1, _DMG_FG)

                    child.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)

                    child.setData(0, Qt.ItemDataRole.UserRole, str(db_path))

                    child.setData(1, Qt.ItemDataRole.UserRole, run.signature)

                    run_item.addChild(child)

            db_item.setExpanded(False)
        """populate。"""

    def _on_item_double_clicked(self, item: QTreeWidgetItem, _column: int) -> None:
        """双击 TopN 行时复制单行到剪贴板。"""

        parent = item.parent()

        if parent is None:
            return

        grandparent = parent.parent()

        if grandparent is None:
            return

        text = item.text(2) or item.text(0)

        if text:
            cb: QClipboard = self.clipboard()

            cb.setText(text)

            self._flash_status(tr("desktop.endfield.copiedSnippet", text=text[:60]))

    def _copy_all(self) -> None:
        """复制全部可见内容到剪贴板。"""

        all_runs: list[RunInfo] = []

        all_scores: list[ScoreInfo] = []

        db_paths: set[str] = set()

        for i in range(self._tree.topLevelItemCount()):
            db_item = self._tree.topLevelItem(i)

            if db_item is None:
                continue

            db_path_str = db_item.data(0, Qt.ItemDataRole.UserRole) or ""

            if db_path_str:
                db_paths.add(db_path_str)

            for j in range(db_item.childCount()):
                run_item = db_item.child(j)

                if run_item is None:
                    continue

                sig = run_item.data(0, Qt.ItemDataRole.UserRole) or ""

                db_p = run_item.data(1, Qt.ItemDataRole.UserRole) or ""

                if sig and db_p:
                    all_scores.extend(list_scores(Path(db_p), sig))

        text = format_clipboard_text(
            run_infos=all_runs,
            score_infos=all_scores,
            db_path="; ".join(db_paths) if db_paths else "",
        )

        cb: QClipboard = self.clipboard()

        cb.setText(text)

        self._flash_status(tr("desktop.endfield.copiedLoadoutCount", n=len(all_scores)))

    def _flash_status(self, msg: str) -> None:
        """在窗口标题栏闪烁提示。"""

        old = self.windowTitle()

        self.setWindowTitle(f"{msg} — {old}")

        from PySide6.QtCore import QTimer

        QTimer.singleShot(2000, lambda: self.setWindowTitle(old))

    @staticmethod
    def clipboard() -> QClipboard:
        from PySide6.QtWidgets import QApplication

        """clipboard。"""
        return QApplication.clipboard()
