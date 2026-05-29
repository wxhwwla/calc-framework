"""排版管理面板 — 添加/编辑/删除 Section，管理输出节点分配。"""

from __future__ import annotations

import uuid

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from calc_framework.graph_editor.schema import SectionDef


class SectionRow(QWidget):
    """单个 Section 的行编辑控件。"""

    changed = Signal()

    def __init__(self, section_id: str, title: str = "", columns: int = 1, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._section_id = section_id
        self._title = title
        self._columns = columns

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        title_label = QLabel(title or section_id)
        title_label.setFont(QFont("Microsoft YaHei", 10))
        layout.addWidget(title_label, 1)

        col_label = QLabel("列:")
        col_label.setFont(QFont("Microsoft YaHei", 9))
        layout.addWidget(col_label)

        col_spin = QSpinBox()
        col_spin.setRange(1, 4)
        col_spin.setValue(columns)
        col_spin.valueChanged.connect(lambda v: self._on_columns_changed(v))
        layout.addWidget(col_spin)

        del_btn = QPushButton("✕")
        del_btn.setFixedSize(24, 24)
        del_btn.setStyleSheet("QPushButton { border: none; color: #FF6B6B; font-weight: bold; }")
        del_btn.clicked.connect(lambda: self._on_delete())
        layout.addWidget(del_btn)

    @property
    def section_id(self) -> str:
        return self._section_id

    @property
    def title(self) -> str:
        return self._title

    @property
    def columns(self) -> int:
        return self._columns

    def _on_columns_changed(self, value: int) -> None:
        self._columns = value
        self.changed.emit()

    def _on_delete(self) -> None:
        self.changed.emit()


class LayoutPanel(QWidget):
    """排版管理面板，管理所有 Section。"""

    layout_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._sections: list[SectionDef] = []
        self._rows: list[SectionRow] = []
        self._output_map: dict[str, list[str]] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        header = QLabel("排版 (Section)")
        header.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        layout.addWidget(header)

        self._section_list = QListWidget()
        self._section_list.setStyleSheet("QListWidget { border: none; }")
        layout.addWidget(self._section_list, 1)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("+ 添加节")
        add_btn.clicked.connect(self._on_add_section)
        btn_layout.addWidget(add_btn)

        clear_btn = QPushButton("清空")
        clear_btn.clicked.connect(self.clear_all)
        btn_layout.addWidget(clear_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def sections(self) -> list[SectionDef]:
        return list(self._sections)

    def section_output_nodes(self, index: int) -> list[str]:
        if 0 <= index < len(self._sections):
            return list(self._sections[index].output_nodes)
        return []

    def add_section(self, title: str = "", output_nodes: list[str] | None = None) -> None:
        sec_id = f"sec_{uuid.uuid4().hex[:6]}"
        nodes = list(output_nodes) if output_nodes else []
        sec = SectionDef(id=sec_id, title=title or "新节", output_nodes=nodes)
        self._sections.append(sec)
        self._rebuild_ui()
        self.layout_changed.emit()

    def remove_section(self, index: int) -> None:
        if 0 <= index < len(self._sections):
            self._sections.pop(index)
            self._rebuild_ui()
            self.layout_changed.emit()

    def set_section_title(self, index: int, title: str) -> None:
        if 0 <= index < len(self._sections):
            self._sections[index].title = title
            self.layout_changed.emit()

    def set_section_columns(self, index: int, columns: int) -> None:
        if 0 <= index < len(self._sections):
            self._sections[index].columns = columns
            self.layout_changed.emit()

    def add_output_to_section(self, section_index: int, node_id: str) -> None:
        if 0 <= section_index < len(self._sections):
            if node_id not in self._sections[section_index].output_nodes:
                self._sections[section_index].output_nodes.append(node_id)
                self._rebuild_ui()
                self.layout_changed.emit()

    def remove_output_from_section(self, section_index: int, node_id: str) -> None:
        if 0 <= section_index < len(self._sections):
            if node_id in self._sections[section_index].output_nodes:
                self._sections[section_index].output_nodes.remove(node_id)
                self._rebuild_ui()
                self.layout_changed.emit()

    def set_sections(self, sections: list[SectionDef]) -> None:
        self._sections = [SectionDef(id=s.id, title=s.title, output_nodes=list(s.output_nodes), columns=s.columns)
                         for s in sections]
        self._rebuild_ui()
        self.layout_changed.emit()

    def clear_all(self) -> None:
        self._sections.clear()
        self._rebuild_ui()
        self.layout_changed.emit()

    def _on_add_section(self) -> None:
        self.add_section()

    def _rebuild_ui(self) -> None:
        self._section_list.clear()
        for i, sec in enumerate(self._sections):
            sec_id = sec.id
            row = SectionRow(sec_id, sec.title, sec.columns)
            row.changed.connect(self.layout_changed.emit)
            item = QListWidgetItem()
            item.setSizeHint(row.sizeHint())
            self._section_list.addItem(item)
            self._section_list.setItemWidget(item, row)
