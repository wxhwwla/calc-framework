"""布局编辑器画布 — 拖拽式布局编辑 + 乘区变量映射。

左侧变量池 → 拖拽到画布上 Section 内 → 保存为 layout.json。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from PySide6.QtCore import Qt, QRectF, QPointF, QMimeData, Signal
from PySide6.QtGui import (
    QBrush, QColor, QDrag, QFont, QLinearGradient, QPainter,
    QPen, QPixmap,
)
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QDialog, QDragEnterEvent, QDropEvent,
    QFileDialog, QFormLayout, QGraphicsItem, QGraphicsRectItem,
    QGraphicsScene, QGraphicsSceneDragDropEvent, QGraphicsSimpleTextItem,
    QGraphicsView, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMessageBox, QPushButton,
    QScrollArea, QSizePolicy, QSpinBox, QSplitter, QVBoxLayout, QWidget,
)

from calc_framework.ui.layout import Layout, Section, load_layout

_SECTION_COLOR = QColor("#2D2D2D")
_SECTION_BORDER = QColor("#555555")
_CONTROL_COLOR = QColor("#3D3D3D")
_CONTROL_BORDER = QColor("#4ECDC4")
_SECTION_WIDTH = 500
_SECTION_HEADER_H = 28
_CONTROL_H = 30
_CONTROL_MARGIN = 10
_GRID_SIZE = 20


class _ControlItem(QGraphicsRectItem):
    """画布上的一个乘区变量控件。"""

    def __init__(self, var_name: str, label: str, parent_section, parent=None):
        super().__init__(0, 0, _SECTION_WIDTH - _CONTROL_MARGIN * 2, _CONTROL_H, parent)
        self._var_name = var_name
        self._label = label
        self.setBrush(QBrush(_CONTROL_COLOR))
        self.setPen(QPen(_CONTROL_BORDER, 1))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        text = QGraphicsSimpleTextItem(label, self)
        text.setFont(QFont("Microsoft YaHei", 9))
        text.setBrush(QBrush(QColor("#D1D1D1")))
        text.setPos(8, 6)

    @property
    def var_name(self) -> str:
        return self._var_name


class _SectionItem(QGraphicsRectItem):
    """画布上的一个 Section 区块。"""

    def __init__(self, section_id: str, title: str, section_type: str, columns: int, parent=None):
        h = _SECTION_HEADER_H + _CONTROL_MARGIN
        super().__init__(0, 0, _SECTION_WIDTH, h, parent)
        self._section_id = section_id
        self._section_type = section_type
        self._columns = columns
        self._title = title
        self._controls: list[_ControlItem] = []

        grad = QLinearGradient(0, 0, 0, _SECTION_HEADER_H)
        grad.setColorAt(0, QColor("#3D3D3D"))
        grad.setColorAt(1, QColor("#353535"))
        self._header_brush = QBrush(grad)
        self.setBrush(QBrush(_SECTION_COLOR))
        self.setPen(QPen(_SECTION_BORDER, 1))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setAcceptDrops(True)

        title_text = f"{title} [{section_type}]"
        self._title_item = QGraphicsSimpleTextItem(title_text, self)
        self._title_item.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        self._title_item.setBrush(QBrush(QColor("#F0F0F0")))
        self._title_item.setPos(8, 5)

        type_tag = QGraphicsSimpleTextItem(f"col={columns}", self)
        type_tag.setFont(QFont("Microsoft YaHei", 8))
        type_tag.setBrush(QBrush(QColor("#888888")))
        type_tag.setPos(_SECTION_WIDTH - 60, 6)

    def add_control(self, var_name: str, label: str) -> _ControlItem:
        ctrl = _ControlItem(var_name, label, self)
        y = _SECTION_HEADER_H + _CONTROL_MARGIN + len(self._controls) * (_CONTROL_H + 4)
        ctrl.setPos(_CONTROL_MARGIN, y)
        self._controls.append(ctrl)
        self._resize_to_fit()
        return ctrl

    def remove_control(self, var_name: str) -> bool:
        for ctrl in self._controls[:]:
            if ctrl.var_name == var_name:
                self._controls.remove(ctrl)
                self.scene().removeItem(ctrl)
                self._reposition_controls()
                self._resize_to_fit()
                return True
        return False

    def _reposition_controls(self) -> None:
        for i, ctrl in enumerate(self._controls):
            y = _SECTION_HEADER_H + _CONTROL_MARGIN + i * (_CONTROL_H + 4)
            ctrl.setPos(_CONTROL_MARGIN, y)

    def _resize_to_fit(self) -> None:
        total = _SECTION_HEADER_H + _CONTROL_MARGIN
        if self._controls:
            total += len(self._controls) * (_CONTROL_H + 4) + _CONTROL_MARGIN
        else:
            total += 40
        self.setRect(0, 0, _SECTION_WIDTH, total)

    @property
    def section_id(self) -> str:
        return self._section_id

    @property
    def section_type(self) -> str:
        return self._section_type

    @property
    def section_title(self) -> str:
        return self._title

    def to_section(self) -> Section:
        inp_vars = [c.var_name for c in self._controls if c.var_name.startswith("character.") or c.var_name.startswith("weapon.") or c.var_name.startswith("equipment.") or c.var_name.startswith("enemy.") or c.var_name.startswith("user.")]
        out_vars = [c.var_name for c in self._controls if not (c.var_name.startswith("character.") or c.var_name.startswith("weapon.") or c.var_name.startswith("equipment.") or c.var_name.startswith("enemy.") or c.var_name.startswith("user."))]
        if self._section_type == "inputs":
            return Section(id=self._section_id, title=self._title, type="inputs", variables=inp_vars, outputs=[], columns=self._columns)
        else:
            return Section(id=self._section_id, title=self._title, type="outputs", variables=[], outputs=out_vars, columns=self._columns)


class SectionEditDialog(QDialog):
    """新建/编辑 Section 的对话框。"""

    def __init__(self, title="", section_type="inputs", columns=2, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Section 属性")
        self._result: dict | None = None
        layout = QFormLayout(self)

        self._title_edit = QLineEdit(title)
        layout.addRow("标题:", self._title_edit)

        self._type_combo = QComboBox()
        self._type_combo.addItems(["inputs", "outputs"])
        self._type_combo.setCurrentText(section_type)
        layout.addRow("类型:", self._type_combo)

        self._cols_spin = QSpinBox()
        self._cols_spin.setRange(1, 6)
        self._cols_spin.setValue(columns)
        layout.addRow("列数:", self._cols_spin)

        btns = QHBoxLayout()
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self._accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(ok_btn)
        btns.addWidget(cancel_btn)
        layout.addRow(btns)

    def _accept(self) -> None:
        self._result = {
            "title": self._title_edit.text() or "新 Section",
            "type": self._type_combo.currentText(),
            "columns": self._cols_spin.value(),
        }
        self.accept()

    @property
    def result(self) -> dict | None:
        return self._result


class LayoutCanvasPanel(QWidget):
    """布局编辑器面板 — 拖拽式 Section + 控件放置。"""

    layout_changed = Signal(object)  # layout_data dict

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._dag_service = None
        self._adapter_name = ""
        self._dag_data: dict | None = None
        self._section_id_counter = 0
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        toolbar = QHBoxLayout()

        add_section_btn = QPushButton("+ 添加 Section")
        add_section_btn.clicked.connect(self._add_section)
        toolbar.addWidget(add_section_btn)

        del_section_btn = QPushButton("删除选中")
        del_section_btn.clicked.connect(self._delete_selected)
        toolbar.addWidget(del_section_btn)

        toolbar.addWidget(QLabel("  适配器:"))
        self._adapter_selector = QComboBox()
        self._adapter_selector.setMinimumWidth(160)
        self._adapter_selector.currentIndexChanged.connect(self._on_adapter_selected)
        toolbar.addWidget(self._adapter_selector)

        clear_btn = QPushButton("清空画布")
        clear_btn.clicked.connect(self._clear_canvas)
        toolbar.addWidget(clear_btn)

        preview_btn = QPushButton("渲染预览")
        preview_btn.clicked.connect(self._open_preview)
        toolbar.addWidget(preview_btn)

        save_btn = QPushButton("保存布局")
        save_btn.clicked.connect(self._save_layout)
        save_btn.setStyleSheet("QPushButton { font-weight: bold; }")
        toolbar.addWidget(save_btn)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left = QWidget()
        left_layout = QVBoxLayout(left)

        left_layout.addWidget(QLabel("输入变量 (拖拽到画布)"))
        self._var_list = QListWidget()
        self._var_list.setDragEnabled(True)
        self._var_list.setAcceptDrops(False)
        self._var_list.setStyleSheet("QListWidget::item { padding: 4px; }")
        left_layout.addWidget(self._var_list)

        left_layout.addWidget(QLabel("乘区输出 (拖拽到画布)"))
        self._output_list = QListWidget()
        self._output_list.setDragEnabled(True)
        self._output_list.setAcceptDrops(False)
        self._output_list.setStyleSheet("QListWidget::item { padding: 4px; }")
        left_layout.addWidget(self._output_list)

        splitter.addWidget(left)

        self._scene = QGraphicsScene()
        self._view = QGraphicsView(self._scene)
        self._view.setAcceptDrops(True)
        self._view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self._view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._set_grid_background()
        splitter.addWidget(self._view)

        right = QWidget()
        self._right_layout = QVBoxLayout(right)
        self._right_layout.addWidget(QLabel("属性"))
        self._prop_group = QGroupBox("选中项")
        prop_form = QFormLayout(self._prop_group)
        self._prop_title = QLabel("（未选中）")
        prop_form.addRow("", self._prop_title)
        self._prop_detail = QLabel("")
        prop_form.addRow("详情:", self._prop_detail)
        self._right_layout.addWidget(self._prop_group)
        self._right_layout.addStretch()
        splitter.addWidget(right)

        splitter.setSizes([200, 550, 180])
        layout.addWidget(splitter, stretch=1)

        self._status_label = QLabel("就绪 — 选择适配器以加载变量")
        layout.addWidget(self._status_label)

        self._scene.selectionChanged.connect(self._on_selection_changed)

    def _set_grid_background(self) -> None:
        from PySide6.QtGui import QPixmap
        pix = QPixmap(_GRID_SIZE * 2, _GRID_SIZE * 2)
        pix.fill(QColor("#1E1E1E"))
        from PySide6.QtGui import QPainter as QP
        p = QP(pix)
        p.setPen(QPen(QColor("#2A2A2A"), 1))
        p.drawPoint(0, 0)
        p.drawPoint(_GRID_SIZE, 0)
        p.drawPoint(0, _GRID_SIZE)
        p.drawPoint(_GRID_SIZE, _GRID_SIZE)
        p.end()
        self._view.setBackgroundBrush(QBrush(pix))

    def _add_section(self) -> None:
        dialog = SectionEditDialog(parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted or not dialog.result:
            return
        r = dialog.result
        self._section_id_counter += 1
        sid = f"section_{self._section_id_counter}"
        sec_item = _SectionItem(sid, r["title"], r["type"], r["columns"])
        x = 30 + (self._section_id_counter % 3) * 40
        y = 30 + (self._section_id_counter % 3) * 30
        sec_item.setPos(x, y)
        self._scene.addItem(sec_item)
        self._status_label.setText(f"已添加 Section: {r['title']}")
        self._emit_layout_changed()

    def _delete_selected(self) -> None:
        for item in self._scene.selectedItems():
            if isinstance(item, _SectionItem):
                self._scene.removeItem(item)
                self._status_label.setText(f"已删除 Section: {item.section_title}")
        self._emit_layout_changed()

    def _clear_canvas(self) -> None:
        self._scene.clear()
        self._set_grid_background()
        self._section_id_counter = 0
        self._status_label.setText("画布已清空")
        self._emit_layout_changed()

    def _on_selection_changed(self) -> None:
        selected = self._scene.selectedItems()
        if not selected:
            self._prop_title.setText("（未选中）")
            self._prop_detail.setText("")
            return
        item = selected[0]
        if isinstance(item, _SectionItem):
            self._prop_title.setText(f"Section: {item.section_title}")
            self._prop_detail.setText(f"ID: {item.section_id}\n类型: {item.section_type}\n控件数: {len(item._controls)}")
        elif isinstance(item, _ControlItem):
            self._prop_title.setText(f"控件: {item.var_name}")
            self._prop_detail.setText(f"标签: {item._label}")
        else:
            self._prop_title.setText(type(item).__name__)

    def populate_adapters(self, names: list[str]) -> None:
        self._adapter_selector.blockSignals(True)
        current = self._adapter_selector.currentText()
        self._adapter_selector.clear()
        self._adapter_selector.addItem("— 选择适配器 —")
        for name in names:
            self._adapter_selector.addItem(name)
        idx = self._adapter_selector.findText(current)
        if idx >= 0:
            self._adapter_selector.setCurrentIndex(idx)
        self._adapter_selector.blockSignals(False)

    def _on_adapter_selected(self, index: int) -> None:
        if index <= 0:
            return
        name = self._adapter_selector.currentText()
        self._adapter_name = name
        try:
            from calc_framework.config.manager import AdapterManager
            mgr = AdapterManager()
            pkg = mgr.load(name)
            self._dag_service = pkg.dag_service
            self._dag_data = {"from_adapter": name}

            self._var_list.clear()
            self._output_list.clear()
            for var_name, var_def in pkg.dag_service.dag.variables.items():
                source = var_def.source if hasattr(var_def, "source") else ""
                item = QListWidgetItem(f"{var_name}  [{source}]")
                item.setData(Qt.ItemDataRole.UserRole, var_name)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsDragEnabled)
                if source in ("character", "weapon", "equipment", "enemy", "user_input"):
                    self._var_list.addItem(item)
                else:
                    self._output_list.addItem(item)

            layout_path = Path(str(pkg._adapter_dir)) / "ui" / "layout.json"
            if layout_path.is_file():
                data = json.loads(layout_path.read_text(encoding="utf-8"))
                self._load_layout_to_canvas(data)
                self._status_label.setText(f"已加载 {name} — {len(pkg.dag_service.dag.variables)} 变量 + layout.json")
            else:
                self._status_label.setText(f"已加载 {name} — {len(pkg.dag_service.dag.variables)} 变量，无 layout.json")
        except Exception as exc:
            QMessageBox.warning(self, "加载失败", str(exc))

    def _load_layout_to_canvas(self, data: dict) -> None:
        self._scene.clear()
        self._set_grid_background()
        try:
            layout = load_layout(data)
        except Exception:
            return
        self._section_id_counter = 0
        for i, sec in enumerate(layout.sections):
            self._section_id_counter += 1
            sec_item = _SectionItem(sec.id, sec.title, sec.type, sec.columns)
            sec_item.setPos(30 + (i % 2) * 60, 30 + (i % 2) * 30)
            self._scene.addItem(sec_item)
            for var_name in sec.variables:
                sec_item.add_control(var_name, var_name)
            for out_name in sec.outputs:
                sec_item.add_control(out_name, out_name)

    def _emit_layout_changed(self) -> None:
        data = self._build_layout_data()
        self.layout_changed.emit(data)

    def _build_layout_data(self) -> dict:
        sections = []
        for item in self._scene.items():
            if isinstance(item, _SectionItem):
                sec = item.to_section()
                sections.append({
                    "id": sec.id,
                    "type": sec.type,
                    "title": sec.title,
                    "variables": sec.variables,
                    "outputs": sec.outputs,
                    "columns": sec.columns,
                })
        return {
            "schema_version": "ui-v1",
            "name": self._adapter_name or "Computed Layout",
            "description": "",
            "sections": sections,
        }

    def _save_layout(self) -> None:
        if not self._adapter_name or self._adapter_selector.currentIndex() <= 0:
            QMessageBox.information(self, "提示", "请先选择适配器")
            return
        from calc_framework.config.manager import AdapterManager
        mgr = AdapterManager()
        pkg = mgr.load(self._adapter_name)
        adapter_path = Path(str(pkg._adapter_dir))
        ui_dir = adapter_path / "ui"
        ui_dir.mkdir(parents=True, exist_ok=True)
        data = self._build_layout_data()
        path = ui_dir / "layout.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        self._status_label.setText(f"布局已保存 → {path}")
        self._emit_layout_changed()

    def _open_preview(self) -> None:
        from calc_framework.ui.compute_sheet import ComputeSheet
        from calc_framework.ui.layout import load_layout
        from calc_framework.dag.service import DAGService

        data = self._build_layout_data()
        if not data["sections"]:
            QMessageBox.information(self, "提示", "画布为空，请先添加 Section 并拖入变量")
            return
        if not self._dag_service:
            QMessageBox.information(self, "提示", "请先选择适配器以加载 DAG")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"布局预览 — {self._adapter_name}")
        dialog.resize(900, 600)
        dl = QVBoxLayout(dialog)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        cl = QVBoxLayout(container)
        try:
            layout_obj = load_layout(data)
            sheet = ComputeSheet(
                dag_service=self._dag_service,
                layout=layout_obj,
                variables=self._dag_service.dag.variables,
                base_context={},
                parent=container,
            )
            cl.addWidget(sheet.widget)
            cl.addStretch()
            scroll.setWidget(container)
            dl.addWidget(scroll)
            sheet.evaluate()
        except Exception as e:
            dl.addWidget(QLabel(f"渲染失败: {e}"))
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        dl.addWidget(close_btn)
        dialog.exec()

    def get_layout_data(self) -> dict | None:
        if not self._adapter_selector.currentIndex():
            return None
        return self._build_layout_data()

    def get_dag_service(self):
        return self._dag_service

    def get_adapter_name(self) -> str:
        return self._adapter_name
