#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""历史搜索记录浏览对话框（search_output/ SQLite 快速搜装）。

P2-07 拆分：UI 构建迁至 ``qt_search_browser_build_mixin.py``，本模块保留
数据填充、复制与剪贴板逻辑，``SearchHistoryDialog`` 公开路径不变。
"""

from __future__ import annotations

from pathlib import Path

from calc_framework.ui.i18n import tr
from PySide6.QtCore import Qt
from PySide6.QtGui import QClipboard, QColor, QFont
from PySide6.QtWidgets import QDialog, QTreeWidgetItem, QWidget

from .qt_search_browser_build_mixin import QtSearchBrowserBuildMixin

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

_SCORE_FG = QColor("#9BB9E0")

_DMG_FG = QColor("#85C1A8")


class SearchHistoryDialog(QtSearchBrowserBuildMixin, QDialog):
    """历史搜索记录浏览弹窗。"""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        big_font: QFont,
        small_font: QFont,
    ) -> None:
        super().__init__(parent)

        self._build_gui(big_font=big_font, small_font=small_font)

        self._populate()

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

        return QApplication.clipboard()
