# SPDX-License-Identifier: AGPL-3.0
"""高级页控制栏：小部件类与异常矩阵构建器。"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QWidget,
)

_LABEL_COLOR = "#CCCCCC"
_HINT_COLOR = "#888888"
_SECTION_COLOR = "#FF6B6B"
_ENTRY_STYLE = """
    QLineEdit { background-color: #2B2B2B; color: #D1D1D1;
                border: 1px solid #464646; border-radius: 4px;
                padding: 2px 6px; min-height: 24px; }
    QLineEdit:focus { border-color: #2B6CB6; }
"""
_COMBO_STYLE = """
    QComboBox { background-color: #2B2B2B; color: #D1D1D1;
                border: 1px solid #464646; border-radius: 4px;
                padding: 2px 6px; min-height: 28px; }
    QComboBox:hover { border-color: #2B6CB6; }
    QComboBox::drop-down { border-left: 1px solid #464646; width: 20px; }
    QComboBox QAbstractItemView { background-color: #2B2B2B; color: #D1D1D1;
        selection-background-color: #2B6CB6; border: 1px solid #464646; }
"""


class SectionHeader(QLabel):
    def __init__(self, text: str, font: QFont) -> None:
        super().__init__(text)
        self.setFont(font)
        self.setStyleSheet(f"color: {_SECTION_COLOR}; padding: 4px 0;")


class HintLabel(QLabel):
    def __init__(self, text: str, font: QFont) -> None:
        super().__init__(text)
        self.setFont(font)
        self.setStyleSheet(f"color: {_HINT_COLOR};")
        self.setWordWrap(True)


class SmallLabel(QLabel):
    def __init__(self, text: str, font: QFont) -> None:
        super().__init__(text)
        self.setFont(font)
        self.setStyleSheet(f"color: {_LABEL_COLOR};")


class ComboRow(QWidget):
    def __init__(self, label: str, items: list[str], current: str, font: QFont) -> None:
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.label = SmallLabel(label, font)
        layout.addWidget(self.label)
        self.combo = QComboBox()
        self.combo.addItems(items)
        self.combo.setCurrentText(current)
        self.combo.setStyleSheet(_COMBO_STYLE)
        layout.addWidget(self.combo, stretch=1)

    def current(self) -> str:
        return self.combo.currentText()


def build_abnormal_matrix(
    small_font: QFont,
    rows: list[str],
    cols: list[str],
) -> tuple[QWidget, dict[str, list[QLineEdit]]]:
    w = QWidget()
    grid = QGridLayout(w)
    grid.setSpacing(2)
    grid.setContentsMargins(0, 0, 0, 0)
    edits_by_row: dict[str, list[QLineEdit]] = {}
    for j, c in enumerate(cols, start=1):
        lbl = QLabel(c)
        lbl.setFont(small_font)
        lbl.setStyleSheet(f"color: {_LABEL_COLOR};")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(lbl, 0, j)
    for i, row_name in enumerate(rows, start=1):
        lbl = QLabel(row_name)
        lbl.setFont(small_font)
        lbl.setStyleSheet(f"color: {_LABEL_COLOR};")
        grid.addWidget(lbl, i, 0)
        row_edits: list[QLineEdit] = []
        for j in range(len(cols)):
            edit = QLineEdit("0")
            edit.setStyleSheet(_ENTRY_STYLE)
            edit.setFixedWidth(44)
            edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(edit, i, j + 1)
            row_edits.append(edit)
        edits_by_row[row_name] = row_edits
    return w, edits_by_row


def build_manual_abnormal_matrix(
    small_font: QFont,
    specs: tuple,
    *,
    column_labels: tuple[str, ...],
) -> tuple[QWidget, dict[str, list[QLineEdit]]]:
    """按 NGA 异常等级列（L0–L4）构建矩阵；不可用档位置灰。"""
    from games.endfield.calc.manual_buff.abnormal_matrix import AbnormalMatrixRowSpec

    w = QWidget()
    grid = QGridLayout(w)
    grid.setSpacing(2)
    grid.setContentsMargins(0, 0, 0, 0)
    edits_by_row: dict[str, list[QLineEdit]] = {}
    for j, col_text in enumerate(column_labels, start=1):
        lbl = QLabel(col_text)
        lbl.setFont(small_font)
        lbl.setStyleSheet(f"color: {_LABEL_COLOR};")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(lbl, 0, j)
    for i, spec in enumerate(specs, start=1):
        if not isinstance(spec, AbnormalMatrixRowSpec):
            continue
        lbl = QLabel(spec.label)
        lbl.setFont(small_font)
        lbl.setStyleSheet(f"color: {_LABEL_COLOR};")
        grid.addWidget(lbl, i, 0)
        allowed = set(spec.ui_levels)
        row_edits: list[QLineEdit] = []
        for ui_level, col_text in enumerate(column_labels):
            edit = QLineEdit("0")
            edit.setStyleSheet(_ENTRY_STYLE)
            edit.setFixedWidth(44)
            edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if ui_level not in allowed:
                edit.setEnabled(False)
                edit.setText("—")
                edit.setStyleSheet(_ENTRY_STYLE + " color: #555555;")
            grid.addWidget(edit, i, ui_level + 1)
            row_edits.append(edit)
        edits_by_row[spec.abnormal_key] = row_edits
    return w, edits_by_row


def read_abnormal_edits(
    edits_by_row: dict[str, list[QLineEdit]],
    keys: list[str],
) -> dict[str, int]:
    result: dict[str, int] = {}
    for i, (row_name, edits) in enumerate(edits_by_row.items()):
        total = 0
        for e in edits:
            try:
                total += max(0, int(e.text() or "0"))
            except ValueError:
                total += 0
        if i < len(keys):
            result[keys[i]] = total
    return result
