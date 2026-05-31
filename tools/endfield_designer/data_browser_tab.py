#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""数据浏览页签 — 查看角色、武器、装备 JSON 数据。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

_LABEL_STYLE = "color: #CCCCCC;"
_HINT_STYLE = "color: #888888;"
_COMBO_STYLE = """
    QComboBox { background-color: #2B2B2B; color: #D1D1D1;
                border: 1px solid #464646; border-radius: 4px;
                padding: 2px 8px; min-height: 28px; }
    QComboBox:hover { border-color: #2B6CB6; }
    QComboBox::drop-down { border-left: 1px solid #464646; width: 20px; }
    QComboBox QAbstractItemView {
        background-color: #2B2B2B; color: #D1D1D1;
        selection-background-color: #2B6CB6; border: 1px solid #464646; }
"""
_TABLE_STYLE = """
    QTableWidget { background-color: #1E1E1E; color: #D1D1D1;
                   border: 1px solid #464646; border-radius: 4px;
                   gridline-color: #333333; font-size: 12px; }
    QTableWidget::item { padding: 4px 8px; }
    QTableWidget::item:selected { background-color: #2B6CB6; color: white; }
    QHeaderView::section { background-color: #2B2B2B; color: #D1D1D1;
                           border: 1px solid #464646; padding: 4px 8px;
                           font-weight: bold; }
"""
_BTN_STYLE = """
    QPushButton { background-color: transparent; color: #D1D1D1;
                  border: 1px solid #464646; border-radius: 6px;
                  padding: 6px 16px; }
    QPushButton:hover { border-color: #2B6CB6; color: white; }
"""

# 数据源配置
_DATA_SOURCES: list[tuple[str, str, list[str]]] = [
    ("character", "character_data/characters.json",
     ["名称", "类型", "星级", "主能力", "副能力", "武器"]),
    ("weapon", "weapon_data/weapons.json",
     ["名称", "类型", "星级"]),
    ("equipment", "equipment_data/equipments.json",
     ["名称", "部位", "星级"]),
]


class DataBrowserTab(QWidget):
    """数据浏览页签：查看角色/武器/装备 JSON 列表。"""

    def __init__(self, big_font: QFont, small_font: QFont) -> None:
        super().__init__()
        self._big = big_font
        self._small = small_font
        self._pkg_root = Path(__file__).resolve().parent.parent.parent / "framework" / "adapters" / "endfield"
        self._all_data: list[dict[str, Any]] = []
        self._build_ui()
        self._load_data()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        header = QLabel("数据浏览")
        header.setFont(self._big)
        header.setStyleSheet("color: #FF6B6B; padding: 4px 0;")
        layout.addWidget(header)

        top_row = QHBoxLayout()
        top_row.addWidget(self._label("数据源"))
        self._source_combo = QComboBox()
        self._source_combo.addItems(["角色数据", "武器数据", "装备数据"])
        self._source_combo.setStyleSheet(_COMBO_STYLE)
        self._source_combo.currentIndexChanged.connect(self._load_data)
        top_row.addWidget(self._source_combo)
        top_row.addStretch()

        self._refresh_btn = QPushButton("刷新")
        self._refresh_btn.setStyleSheet(_BTN_STYLE)
        self._refresh_btn.clicked.connect(self._load_data)
        top_row.addWidget(self._refresh_btn)

        layout.addLayout(top_row)

        self._count_label = self._label("")
        self._count_label.setStyleSheet(_HINT_STYLE)
        layout.addWidget(self._count_label)

        self._table = QTableWidget()
        self._table.setStyleSheet(_TABLE_STYLE)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.verticalHeader().setVisible(False)
        layout.addWidget(self._table, stretch=1)

    def _label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setFont(self._small)
        lbl.setStyleSheet(_LABEL_STYLE)
        return lbl

    def _load_data(self) -> None:
        idx = self._source_combo.currentIndex()
        if idx < 0 or idx >= len(_DATA_SOURCES):
            return
        _, rel_path, columns = _DATA_SOURCES[idx]
        json_path = self._pkg_root / rel_path
        try:
            with json_path.open(encoding="utf-8") as f:
                raw = json.load(f)
            self._all_data = raw if isinstance(raw, list) else [raw]
        except Exception as exc:
            self._all_data = []
            self._count_label.setText(f"加载失败: {exc}")
            self._table.setRowCount(0)
            self._table.setColumnCount(0)
            return

        self._count_label.setText(f"共 {len(self._all_data)} 条记录")
        self._populate_table(columns)

    def _populate_table(self, columns: list[str]) -> None:
        self._table.setColumnCount(len(columns))
        self._table.setHorizontalHeaderLabels(columns)
        self._table.setRowCount(len(self._all_data))

        for row_idx, item in enumerate(self._all_data):
            for col_idx, col_name in enumerate(columns):
                value = item.get(col_name, "")
                display = str(value) if not isinstance(value, list) else f"[数组, {len(value)} 项]"
                cell = QTableWidgetItem(display)
                cell.setFlags(cell.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._table.setItem(row_idx, col_idx, cell)

        self._table.resizeColumnsToContents()
        total_width = sum(self._table.columnWidth(c) for c in range(len(columns)))
        viewport_width = self._table.viewport().width()
        if total_width < viewport_width:
            self._table.horizontalHeader().setStretchLastSection(True)
