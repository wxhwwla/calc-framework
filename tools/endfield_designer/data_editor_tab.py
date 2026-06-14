# SPDX-License-Identifier: AGPL-3.0
"""数据编辑页签 — 新增/编辑/删除角色、武器、装备数据。"""

from __future__ import annotations


from typing import Any


from PySide6.QtCore import Qt

from PySide6.QtGui import QFont

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


from games.endfield.data_loading.loader import (
    get_characters,
    get_equipments,
    get_weapons,
    save_characters,
    save_equipments,
    save_weapons,
)


_LABEL_STYLE = "color: #CCCCCC;"

_HINT_STYLE = "color: #888888;"

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

_BTN_DANGER = """

    QPushButton { background-color: transparent; color: #E53E3E;

                  border: 1px solid #E53E3E; border-radius: 6px;

                  padding: 6px 16px; }

    QPushButton:hover { background-color: #E53E3E; color: white; }

"""

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

_DIALOG_STYLE = """

    QDialog { background-color: #1A1A1A; }

    QLabel { color: #D1D1D1; }

    QLineEdit { background-color: #2B2B2B; color: #D1D1D1;

                border: 1px solid #464646; border-radius: 4px;

                padding: 4px 8px; min-height: 24px; }

    QLineEdit:focus { border-color: #2B6CB6; }

    QSpinBox { background-color: #2B2B2B; color: #D1D1D1;

               border: 1px solid #464646; border-radius: 4px;

               padding: 2px 6px; min-height: 24px; }

    QSpinBox:focus { border-color: #2B6CB6; }

    QSpinBox::up-button, QSpinBox::down-button {

               border: 1px solid #464646; width: 16px; }

"""


# ── Schema definitions ─────────────────────────────────────────────


_SCALAR_FIELDS = {
    "character": [
        ("名称", "text"),
        ("类型", "combo:物理/能量/电磁/热熔/异裂"),
        ("星级", "spin:1,6"),
        ("武器", "text"),
        ("主能力", "combo:力量/敏捷/智识/意志"),
        ("副能力", "combo:力量/敏捷/智识/意志"),
        ("力量", "spin:0,999"),
        ("敏捷", "spin:0,999"),
        ("智识", "spin:0,999"),
        ("意志", "spin:0,999"),
        ("信赖", "spin:0,10"),
    ],
    "weapon": [
        ("名称", "text"),
        ("类型", "combo:尖兵/刀锋/重装/射手/术士/医疗/支援"),
        ("星级", "spin:1,6"),
    ],
    "equipment": [
        ("名称", "text"),
        ("部位", "combo:胸甲/手套/饰品"),
        ("星级", "spin:1,6"),
    ],
}


_COLUMNS = {
    "character": ["名称", "类型", "星级", "主能力", "副能力"],
    "weapon": ["名称", "类型", "星级"],
    "equipment": ["名称", "部位", "星级"],
}


_SAVERS = {
    "character": save_characters,
    "weapon": save_weapons,
    "equipment": save_equipments,
}


_GETTERS = {
    "character": get_characters,
    "weapon": get_weapons,
    "equipment": get_equipments,
}


class DataEditorTab(QWidget):
    """数据编辑页签：新增/编辑/删除角色、武器、装备。"""

    def __init__(self, big_font: QFont, small_font: QFont) -> None:
        super().__init__()

        self._big = big_font

        self._small = small_font

        self._data_type = "character"

        self._all_data: list[dict[str, Any]] = []

        self._build_ui()

        self._load_data()

    def _build_ui(self) -> None:
        """_build_ui 实现。"""
        layout = QVBoxLayout(self)

        layout.setContentsMargins(12, 12, 12, 12)

        layout.setSpacing(8)

        header = QLabel("数据编辑")

        header.setFont(self._big)

        header.setStyleSheet("color: #FF6B6B; padding: 4px 0;")

        layout.addWidget(header)

        top_row = QHBoxLayout()

        top_row.addWidget(self._label("数据类型"))

        self._type_combo = QComboBox()

        self._type_combo.addItems(["角色数据", "武器数据", "装备数据"])

        self._type_combo.setStyleSheet(_COMBO_STYLE)

        self._type_combo.currentIndexChanged.connect(self._on_type_change)

        top_row.addWidget(self._type_combo)

        top_row.addStretch()

        for btn, style in [
            ("新增", _BTN_STYLE),
            ("编辑选中", _BTN_STYLE),
            ("删除选中", _BTN_DANGER),
        ]:
            b = QPushButton(btn)

            b.setStyleSheet(style)

            top_row.addWidget(b)

            setattr(self, f"_{btn.replace(' ', '_')}_btn", b)

        self._新增_btn.clicked.connect(self._on_add)

        self._编辑选中_btn.clicked.connect(self._on_edit)

        self._删除选中_btn.clicked.connect(self._on_delete)

        layout.addLayout(top_row)

        self._count_label = self._label("")

        self._count_label.setStyleSheet(_HINT_STYLE)

        layout.addWidget(self._count_label)

        hint = self._label(
            "提示：选中行后点击「编辑选中」修改数据。"
            "数组字段（等级曲线/基础攻击力等）以只读文本显示，可在 JSON 中编辑。"
        )

        hint.setStyleSheet("color: #888888; font-size: 11px;")

        hint.setWordWrap(True)

        layout.addWidget(hint)

        self._table = QTableWidget()

        self._table.setStyleSheet(_TABLE_STYLE)

        self._table.setAlternatingRowColors(True)

        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self._table.horizontalHeader().setStretchLastSection(True)

        self._table.verticalHeader().setVisible(False)

        self._table.doubleClicked.connect(self._on_edit)

        layout.addWidget(self._table, stretch=1)

    def _label(self, text: str) -> QLabel:
        """_label 实现。"""
        lbl = QLabel(text)

        lbl.setFont(self._small)

        lbl.setStyleSheet(_LABEL_STYLE)

        return lbl

    def _on_type_change(self) -> None:
        """_on_type_change 实现。"""
        idx = self._type_combo.currentIndex()

        self._data_type = ["character", "weapon", "equipment"][idx]

        self._load_data()

    def _load_data(self) -> None:
        """_load_data 实现。"""
        try:
            self._all_data = list(_GETTERS[self._data_type]())

        except Exception as exc:
            self._all_data = []

            self._count_label.setText(f"加载失败: {exc}")

            self._table.setRowCount(0)

            return

        self._count_label.setText(f"共 {len(self._all_data)} 条记录")

        self._populate_table()

    def _populate_table(self) -> None:
        """_populate_table 实现。"""
        columns = _COLUMNS[self._data_type]

        self._table.setColumnCount(len(columns))

        self._table.setHorizontalHeaderLabels(columns)

        self._table.setRowCount(len(self._all_data))

        for row_idx, item in enumerate(self._all_data):
            for col_idx, col_name in enumerate(columns):
                value = item.get(col_name, "")

                display = str(value) if not isinstance(value, list) else "[数组]"

                cell = QTableWidgetItem(display)

                cell.setFlags(cell.flags() & ~Qt.ItemFlag.ItemIsEditable)

                self._table.setItem(row_idx, col_idx, cell)

        self._table.resizeColumnsToContents()

    def _get_selected_index(self) -> int | None:
        """_get_selected_index 实现。"""
        rows = self._table.selectionModel().selectedRows()

        if not rows:
            QMessageBox.information(self, "提示", "请先选中一行")

            return None

        return rows[0].row()

    def _on_add(self) -> None:
        """_on_add 实现。"""
        fields = _SCALAR_FIELDS[self._data_type]

        dialog = _EditDialog(self._data_type, fields, None, self._small)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        new_entry = dialog.get_data()

        self._all_data.append(new_entry)

        self._save()

        self._populate_table()

        self._count_label.setText(f"共 {len(self._all_data)} 条记录")

    def _on_edit(self) -> None:
        """_on_edit 实现。"""
        idx = self._get_selected_index()

        if idx is None:
            return

        fields = _SCALAR_FIELDS[self._data_type]

        dialog = _EditDialog(self._data_type, fields, self._all_data[idx], self._small)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        self._all_data[idx] = dialog.get_data()

        self._save()

        self._populate_table()

    def _on_delete(self) -> None:
        """_on_delete 实现。"""
        idx = self._get_selected_index()

        if idx is None:
            return

        name = self._all_data[idx].get("名称", f"条目 #{idx}")

        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除「{name}」吗？\n此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        self._all_data.pop(idx)

        self._save()

        self._populate_table()

        self._count_label.setText(f"共 {len(self._all_data)} 条记录")

    def _save(self) -> None:
        """_save 实现。"""
        saver = _SAVERS[self._data_type]

        if not saver(self._all_data):
            QMessageBox.critical(self, "保存失败", "数据保存失败，请检查文件权限。")


class _EditDialog(QDialog):
    """编辑/新增条目对话框。"""

    def __init__(
        self,
        data_type: str,
        fields: list[tuple[str, str]],
        existing: dict[str, Any] | None,
        small_font: QFont,
    ) -> None:
        super().__init__()

        self.setWindowTitle("编辑" if existing else "新增")

        self.setMinimumWidth(420)

        self.setStyleSheet(_DIALOG_STYLE)

        self._fields = fields

        self._widgets: dict[str, QWidget] = {}

        layout = QVBoxLayout(self)

        form = QFormLayout()

        form.setSpacing(8)

        form.setContentsMargins(16, 16, 16, 8)

        for field_name, field_type in fields:
            w = self._build_widget(field_name, field_type, existing.get(field_name) if existing else None)

            lbl = QLabel(field_name)

            lbl.setFont(small_font)

            lbl.setStyleSheet("color: #D1D1D1;")

            form.addRow(lbl, w)

            self._widgets[field_name] = w

        layout.addLayout(form)

        # 只读区域显示数组字段摘要

        if existing:
            arr_summary = self._build_array_summary(existing)

            if arr_summary:
                layout.addWidget(arr_summary)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

        buttons.accepted.connect(self.accept)

        buttons.rejected.connect(self.reject)

        buttons.setStyleSheet("""

            QPushButton { background-color: transparent; color: #D1D1D1;

                          border: 1px solid #464646; border-radius: 6px;

                          padding: 6px 20px; min-width: 60px; }

            QPushButton:hover { border-color: #2B6CB6; color: white; }

        """)

        layout.addWidget(buttons)

    def _build_widget(self, field_name: str, field_type: str, value: Any) -> QWidget:
        """_build_widget 实现。"""
        if field_type == "text":
            w = QLineEdit()

            w.setText(str(value) if value is not None else "")

            return w

        if field_type.startswith("combo:"):
            options = field_type.split(":", 1)[1].split("/")

            w = QComboBox()

            w.addItems(options)

            if value and str(value) in options:
                w.setCurrentText(str(value))

            return w

        if field_type.startswith("spin:"):
            parts = field_type.split(":", 1)[1].split(",")

            w = QSpinBox()

            w.setRange(int(parts[0]), int(parts[1]))

            if value is not None:
                w.setValue(int(value))

            return w

        w = QLineEdit()

        w.setText(str(value) if value is not None else "")

        return w

    def _build_array_summary(self, existing: dict[str, Any]) -> QLabel | None:
        """_build_array_summary 实现。"""
        lines: list[str] = []

        for key, val in existing.items():
            if isinstance(val, list):
                length = len(val)

                sample = ""

                if length > 0:
                    first = val[0]

                    if isinstance(first, list):
                        sample = f"({len(first)} 项)"

                    else:
                        sample = f"[{first}...]"

                lines.append(f"  {key}: 数组({length}) {sample}")

        if not lines:
            return None

        lbl = QLabel("只读字段（请在 JSON 文件中直接编辑）:\n" + "\n".join(lines))

        lbl.setStyleSheet("color: #888888; font-size: 11px; padding: 8px 16px;")

        lbl.setWordWrap(True)

        return lbl

    def get_data(self) -> dict[str, Any]:
        """get_data 实现。"""
        result: dict[str, Any] = {}

        for field_name, _field_type in self._fields:
            w = self._widgets[field_name]

            if isinstance(w, QLineEdit):
                result[field_name] = w.text()

            elif isinstance(w, QComboBox):
                result[field_name] = w.currentText()

            elif isinstance(w, QSpinBox):
                result[field_name] = w.value()

        return result
