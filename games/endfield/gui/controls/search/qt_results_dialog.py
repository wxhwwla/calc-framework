#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""全量 / MVP 搜索结果展示弹窗（P2-07 从 ``qt_actions.py`` 拆出）。"""

from __future__ import annotations

from collections.abc import Sequence

from calc_framework.ui.i18n import tr
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from games.endfield.calc.loadout.optimizer import LoadoutScore
from games.endfield.gui.controls.search.search_worker_logic import (
    SearchResultItem,
    build_search_result_items,
    format_search_result_summary,
)

__all__ = ["QtSearchResultsDialog", "_build_tree_items"]


_DARK_BG = "#1E1E1E"

_DARK_FG = "#D1D1D1"

_ACCENT = "#2B6CB6"

_HEADER_BG = "#2A2A2A"

_SEG_FG = QColor("#9BB9E0")

_ABNORMAL_FG = QColor("#C9A96E")


def _node_to_item(node: SearchResultItem) -> QTreeWidgetItem:
    """将 SearchResultItem 转换为 QTreeWidgetItem（递归）。"""
    item = QTreeWidgetItem([node.text])
    item.setFlags(Qt.ItemFlag.ItemIsEnabled)
    if node.color == "segment":
        item.setForeground(0, _SEG_FG)
    elif node.color == "abnormal":
        item.setForeground(0, _ABNORMAL_FG)
    for child_node in node.children:
        child_item = _node_to_item(child_node)
        item.addChild(child_item)
    return item


def _build_tree_items(
    lines: list[str],
    top_results: Sequence[LoadoutScore] | None,
    *,
    damage_metric: str | None,
    segment_counts: dict[str, int] | None,
    abnormal_counts: dict[str, int] | None,
    spell_abnormal_counts: dict[str, int] | None,
) -> list[QTreeWidgetItem]:
    """构建搜索结果树节点。

    当提供 top_results 时生成结构化树；否则退化为纯文本 flat 列表。
    数据处理委托给 search_worker_logic.build_search_result_items。
    """
    items: list[QTreeWidgetItem] = []

    if not top_results:
        for line in lines:
            item = QTreeWidgetItem([line])
            item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            items.append(item)
        return items

    metric = damage_metric if damage_metric is not None else tr("desktop.endfield.damageMetric")
    nodes = build_search_result_items(
        list(top_results),
        damage_metric=metric,
        segment_counts=segment_counts,
        abnormal_counts=abnormal_counts,
        spell_abnormal_counts=spell_abnormal_counts,
    )
    for node in nodes:
        item = _node_to_item(node)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsAutoTristate)
        item.setExpanded(node.expanded)
        items.append(item)

    return items


class QtSearchResultsDialog(QDialog):
    """全量 / MVP 搜索结果展示弹窗（结构化树视图）。"""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        title: str,
        lines: list[str],
        big_font: QFont,
        small_font: QFont,
        top_results: Sequence[LoadoutScore] | None = None,
        damage_metric: str | None = None,
        segment_counts: dict[str, int] | None = None,
        abnormal_counts: dict[str, int] | None = None,
        spell_abnormal_counts: dict[str, int] | None = None,
    ) -> None:
        super().__init__(parent)

        self.setWindowTitle(title)

        self.resize(960, 760)

        self.setMinimumSize(680, 480)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(12, 12, 12, 12)

        tree = QTreeWidget()

        tree.setFont(small_font)

        tree.setHeaderLabels([tr("desktop.endfield.searchResultsHeader")])

        tree.header().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        tree.header().setVisible(False)

        tree.setAlternatingRowColors(True)

        tree.setStyleSheet(f"""

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

            QTreeWidget::branch:has-children:!has-siblings:closed,

            QTreeWidget::branch:closed:has-children:has-siblings {{

                border-image: none;

                image: none;

            }}

            QTreeWidget::branch:open:has-children:!has-siblings,

            QTreeWidget::branch:open:has-children:has-siblings {{

                border-image: none;

                image: none;

            }}

        """)

        tree.setIndentation(20)

        tree.setAnimated(True)

        tree.setRootIsDecorated(True)

        tree_items = _build_tree_items(
            lines,
            top_results,
            damage_metric=damage_metric,
            segment_counts=segment_counts,
            abnormal_counts=abnormal_counts,
            spell_abnormal_counts=spell_abnormal_counts,
        )

        for item in tree_items:
            tree.addTopLevelItem(item)

        layout.addWidget(tree, stretch=1)

        info_label = QPushButton(format_search_result_summary(list(top_results) if top_results else None))

        info_label.setFont(small_font)

        info_label.setStyleSheet("""

            QPushButton {

                background-color: transparent; color: #888;

                border: none; text-align: left; padding: 2px 0;

            }

        """)

        info_label.setEnabled(False)

        layout.addWidget(info_label)

        btn_row = QHBoxLayout()

        btn_row.addStretch()

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
