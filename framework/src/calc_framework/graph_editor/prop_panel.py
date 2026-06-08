# SPDX-License-Identifier: AGPL-3.0
"""属性面板 — 编辑选中节点的配置参数。"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from .registry import get_registry
from .schema import GraphNode


class PropPanel(QWidget):
    """底部属性面板，编辑选中节点的配置。"""

    node_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._current_node: GraphNode | None = None

        self._current_item_id: str | None = None

        self._controls: dict[str, QWidget] = {}

        self._form_row: QFormLayout | None = None

        layout = QVBoxLayout(self)

        layout.setContentsMargins(8, 4, 8, 4)

        title = QLabel("节点属性")

        title.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))

        layout.addWidget(title)

        self._placeholder = QLabel("选择节点以编辑属性")

        self._placeholder.setFont(QFont("Microsoft YaHei", 9))

        self._placeholder.setStyleSheet("color: #888;")

        layout.addWidget(self._placeholder)

        self._form_group = QGroupBox()

        self._form_group.setVisible(False)

        self._form_row = QFormLayout(self._form_group)

        self._form_row.setSpacing(4)

        layout.addWidget(self._form_group)

        # ── 预览值（只读） ──

        preview_group = QGroupBox()

        preview_layout = QFormLayout(preview_group)

        self._preview_label = QLabel("—")

        self._preview_label.setFont(QFont("Consolas", 12, QFont.Weight.Bold))

        self._preview_label.setStyleSheet("color: #4fc3f7; padding: 4px;")

        preview_layout.addRow("预览值", self._preview_label)

        layout.addWidget(preview_group)

        layout.addStretch()

    @property
    def current_node_id(self) -> str | None:
        return self._current_item_id

    @property
    def current_node(self) -> GraphNode | None:
        return self._current_node

    def show_node(self, node: GraphNode | None) -> None:
        """显示节点的可编辑属性。传入 None 清空面板。"""

        self._current_node = node

        self._current_item_id = node.id if node else None

        if node is None:
            self._placeholder.setVisible(True)

            self._form_group.setVisible(False)

            return

        self._placeholder.setVisible(False)

        self._form_group.setVisible(True)

        self._rebuild_form(node)

    def _rebuild_form(self, node: GraphNode) -> None:
        """根据节点类型重建表单。"""

        self._controls.clear()

        self._clear_layout(self._form_row)  # type: ignore[arg-type]

        # ID（只读）

        id_label = QLabel(f"<b>{node.id}</b>")

        self._form_row.addRow("ID", id_label)

        # 标签（可编辑）

        label_edit = QLineEdit(node.label or "")

        label_edit.textChanged.connect(lambda t: self._on_label_changed(t))

        self._controls["label"] = label_edit

        self._form_row.addRow("名称", label_edit)

        # 类型（只读）

        reg = get_registry()

        entry = reg.get(node.type)

        type_label = QLabel(entry.display_name if entry else node.type)

        self._form_row.addRow("类型", type_label)

        if node.type == "const":
            self._add_const_controls(node)

        elif node.type == "var":
            self._add_var_controls(node)

        elif node.type == "user_input":
            self._add_user_input_controls(node)

        elif node.type in ("unary", "binary"):
            self._add_op_controls(node)

    def _add_const_controls(self, node: GraphNode) -> None:
        sb = QDoubleSpinBox()

        sb.setRange(-1e9, 1e9)

        sb.setDecimals(4)

        sb.setValue(node.config.value)

        sb.editingFinished.connect(lambda: self._on_value_changed(sb.value()))

        self._controls["value"] = sb

        self._form_row.addRow("数值", sb)

    def _add_var_controls(self, node: GraphNode) -> None:
        le = QLineEdit(node.config.path)

        le.textChanged.connect(lambda t: self._on_path_changed(t))

        self._controls["path"] = le

        self._form_row.addRow("变量路径", le)

    def _add_user_input_controls(self, node: GraphNode) -> None:
        default_sb = QDoubleSpinBox()

        default_sb.setRange(-1e9, 1e9)

        default_sb.setValue(node.config.default)

        default_sb.editingFinished.connect(lambda: self._on_user_input_changed(default_sb.value(), "default"))

        self._controls["default"] = default_sb

        self._form_row.addRow("默认值", default_sb)

        min_sb = QDoubleSpinBox()

        min_sb.setRange(-1e9, 1e9)

        min_sb.setValue(node.config.min)

        min_sb.editingFinished.connect(lambda: self._on_user_input_changed(min_sb.value(), "min"))

        self._controls["min"] = min_sb

        self._form_row.addRow("最小值", min_sb)

        max_sb = QDoubleSpinBox()

        max_sb.setRange(-1e9, 1e9)

        max_sb.setValue(node.config.max)

        max_sb.editingFinished.connect(lambda: self._on_user_input_changed(max_sb.value(), "max"))

        self._controls["max"] = max_sb

        self._form_row.addRow("最大值", max_sb)

        step_sb = QDoubleSpinBox()

        step_sb.setRange(0.001, 1e9)

        step_sb.setDecimals(4)

        step_sb.setValue(node.config.step)

        step_sb.editingFinished.connect(lambda: self._on_user_input_changed(step_sb.value(), "step"))

        self._controls["step"] = step_sb

        self._form_row.addRow("步长", step_sb)

    def _add_op_controls(self, node: GraphNode) -> None:
        reg = get_registry()

        entry = reg.get(node.type)

        if entry is None or not entry.ops:
            return

        cb = QComboBox()

        ops = entry.ops

        current_idx = 0

        for i, (op_id, op_name) in enumerate(ops):
            cb.addItem(f"{op_name} ({op_id})", op_id)

            if op_id == node.op:
                current_idx = i

        cb.setCurrentIndex(current_idx)

        cb.currentIndexChanged.connect(lambda idx: self._on_op_changed(cb.itemData(idx)))

        self._controls["op"] = cb

        self._form_row.addRow("操作", cb)

    def _on_label_changed(self, text: str) -> None:
        if self._current_node:
            self._current_node.label = text

            self.node_changed.emit(self._current_node.id)

    def _on_value_changed(self, value: float) -> None:
        if self._current_node:
            self._current_node.config.value = value

            self.node_changed.emit(self._current_node.id)

    def _on_path_changed(self, path: str) -> None:
        if self._current_node:
            self._current_node.config.path = path

            self.node_changed.emit(self._current_node.id)

    def _on_user_input_changed(self, value: float, field: str) -> None:
        if self._current_node:
            setattr(self._current_node.config, field, value)

            self.node_changed.emit(self._current_node.id)

    def _on_op_changed(self, op_id: str) -> None:
        if self._current_node:
            self._current_node.op = op_id

            self.node_changed.emit(self._current_node.id)

    def set_preview_value(self, value_text: str) -> None:
        """设置预览值的显示文本。"""

        self._preview_label.setText(value_text)

    @staticmethod
    def _clear_layout(layout: QFormLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)

            if item.widget():
                item.widget().deleteLater()
