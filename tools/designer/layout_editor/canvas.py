#!/usr/bin/env python3
"""布局编辑器画布 — 基于 QGraphicsView 的可视化布局编辑器。

支持通过 AdapterManager 加载适配包变量和 layout.json。
新增多分辨率预览功能。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QGraphicsScene,
    QGraphicsView,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

_RESOLUTION_PRESETS = [
    ("1920×1080 (Full HD)", 1920, 1080),
    ("2560×1440 (2K)", 2560, 1440),
    ("3840×2160 (4K)", 3840, 2160),
    ("1366×768 (笔记本)", 1366, 768),
    ("375×667 (手机)", 375, 667),
    ("768×1024 (平板竖屏)", 768, 1024),
]


class ResolutionPreviewDialog(QDialog):
    """多分辨率预览对话框 — 渲染 layout.json 并模拟不同屏幕尺寸。"""

    def __init__(
        self,
        layout_data: dict,
        dag_service,
        adapter_name: str,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._layout_data = layout_data
        self._dag_service = dag_service
        self._adapter_name = adapter_name
        self._current_width = 1920
        self._current_height = 1080
        self._build_ui()

    def _build_ui(self) -> None:
        self.setWindowTitle(f"多分辨率预览 — {self._adapter_name}")
        layout = QVBoxLayout(self)

        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("模拟分辨率:"))

        self._res_combo = QComboBox()
        for label, *_ in _RESOLUTION_PRESETS:
            self._res_combo.addItem(label)
        self._res_combo.currentIndexChanged.connect(self._on_resolution_changed)
        toolbar.addWidget(self._res_combo)

        self._size_label = QLabel("1920 × 1080")
        toolbar.addWidget(self._size_label)

        toolbar.addStretch()

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        toolbar.addWidget(close_btn)

        layout.addLayout(toolbar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self._preview_container = QWidget()
        self._preview_layout = QVBoxLayout(self._preview_container)
        scroll.setWidget(self._preview_container)
        layout.addWidget(scroll, stretch=1)

        self._render_preview()

    def _on_resolution_changed(self, index: int) -> None:
        if 0 <= index < len(_RESOLUTION_PRESETS):
            _, w, h = _RESOLUTION_PRESETS[index]
            self._current_width = w
            self._current_height = h
            self._size_label.setText(f"{w} × {h}")
            self._render_preview()

    def _render_preview(self) -> None:
        while self._preview_layout.count():
            item = self._preview_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        try:
            from calc_framework.dag.service import DAGService
            from calc_framework.ui.compute_sheet import ComputeSheet
            from calc_framework.ui.layout import load_layout

            service = self._dag_service
            if isinstance(service, DAGService):
                pass
            else:
                service = DAGService(service)

            layout_obj = load_layout(self._layout_data)

            sheet = ComputeSheet(
                dag_service=service,
                layout=layout_obj,
                variables={},
                base_context={},
                parent=self._preview_container,
            )

            sheet_widget = sheet.widget
            sheet_widget.setMinimumWidth(min(self._current_width, 800))
            sheet_widget.setMaximumWidth(self._current_width)

            group = QGroupBox(f"预览 @ {self._current_width}×{self._current_height}")
            group_layout = QVBoxLayout(group)
            group_layout.addWidget(sheet_widget)
            self._preview_layout.addWidget(group)

            self._preview_layout.addStretch()

            sheet.evaluate()
        except Exception as e:
            error_lbl = QLabel(f"渲染失败: {e}")
            error_lbl.setStyleSheet("color: #FF6B6B; padding: 16px;")
            self._preview_layout.addWidget(error_lbl)


class LayoutCanvasPanel(QWidget):
    """布局编辑器面板 — 左栏变量池 + 中栏画布 + 右栏属性。"""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._dag_data: dict | None = None
        self._layout_data: dict | None = None
        self._adapter_path: Path | None = None
        self._dag_service = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        toolbar = QHBoxLayout()

        toolbar.addWidget(QLabel("适配器:"))
        self._adapter_selector = QComboBox()
        self._adapter_selector.setMinimumWidth(200)
        self._adapter_selector.currentIndexChanged.connect(self._on_adapter_selected)
        toolbar.addWidget(self._adapter_selector)

        load_btn = QPushButton("加载 DAG")
        load_btn.clicked.connect(self._load_dag)
        toolbar.addWidget(load_btn)

        toolbar.addWidget(QLabel("网格列数:"))
        self._cols_spin = QSpinBox()
        self._cols_spin.setRange(4, 24)
        self._cols_spin.setValue(12)
        toolbar.addWidget(self._cols_spin)

        toolbar.addWidget(QLabel("间距:"))
        self._gutter_spin = QSpinBox()
        self._gutter_spin.setRange(0, 32)
        self._gutter_spin.setValue(8)
        toolbar.addWidget(self._gutter_spin)

        self._snap_btn = QPushButton("吸附: 开")
        self._snap_btn.setCheckable(True)
        self._snap_btn.setChecked(True)
        self._snap_btn.clicked.connect(self._toggle_snap)
        toolbar.addWidget(self._snap_btn)

        self._collision_btn = QPushButton("碰撞检测: 开")
        self._collision_btn.setCheckable(True)
        self._collision_btn.setChecked(True)
        toolbar.addWidget(self._collision_btn)

        toolbar.addWidget(QLabel("预览:"))
        self._res_combo = QComboBox()
        for label, *_ in _RESOLUTION_PRESETS:
            self._res_combo.addItem(label)
        toolbar.addWidget(self._res_combo)

        preview_btn = QPushButton("渲染预览")
        preview_btn.clicked.connect(self._open_preview)
        toolbar.addWidget(preview_btn)

        save_btn = QPushButton("保存布局")
        save_btn.clicked.connect(self._save_layout)
        toolbar.addWidget(save_btn)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(QLabel("可用变量"))
        self._var_list = QListWidget()
        left_layout.addWidget(self._var_list)
        splitter.addWidget(left)

        self._scene = QGraphicsScene()
        self._view = QGraphicsView(self._scene)
        self._view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        splitter.addWidget(self._view)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.addWidget(QLabel("属性 (待实现)"))
        right_layout.addWidget(QLabel("选中控件后显示参数"))
        right_layout.addStretch()
        splitter.addWidget(right)

        splitter.setSizes([180, 500, 200])
        layout.addWidget(splitter, stretch=1)

        self._status_label = QLabel("就绪 — 选择适配器或加载 DAG")
        layout.addWidget(self._status_label)

    def populate_adapters(self, names: list[str]) -> None:
        """填充适配器选择器。"""
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
        try:
            from calc_framework.config.manager import AdapterManager

            mgr = AdapterManager()
            pkg = mgr.load(name)
            self._adapter_path = Path(pkg._adapter_dir)
            self._dag_service = pkg.dag_service

            self._var_list.clear()
            for var_name in pkg.dag_service.dag.variables:
                self._var_list.addItem(var_name)

            layout_path = self._adapter_path / "ui" / "layout.json"
            if layout_path.is_file():
                self._layout_data = json.loads(layout_path.read_text(encoding="utf-8"))
                self._status_label.setText(
                    f"已加载 {name} — layout.json + {len(pkg.dag_service.dag.variables)} 变量"
                )
            else:
                self._layout_data = {"schema_version": "ui-v1", "name": name, "sections": []}
                self._status_label.setText(f"已加载 {name} — 无 layout.json，新建空白布局")

            self._dag_data = {"name": name}
        except Exception as exc:
            QMessageBox.warning(self, "加载失败", str(exc))

    def _save_layout(self) -> None:
        if not self._layout_data or not self._adapter_path:
            QMessageBox.information(self, "提示", "请先选择适配器")
            return
        ui_dir = self._adapter_path / "ui"
        ui_dir.mkdir(parents=True, exist_ok=True)
        path = ui_dir / "layout.json"
        path.write_text(
            json.dumps(self._layout_data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        self._status_label.setText(f"布局已保存 → {path}")

    def _load_dag(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 DAG JSON", "", "JSON Files (*.json);;All Files (*)"
        )
        if not path:
            return
        try:
            from calc_framework.dag.serializer import load_dag

            dag = load_dag(path)
            self._dag_data = dag
            self._var_list.clear()
            for var_path in dag.variables:
                self._var_list.addItem(var_path)
            self._status_label.setText(f"已加载 DAG: {Path(path).name}")
        except Exception as e:
            QMessageBox.critical(self, "加载失败", str(e))

    def _toggle_snap(self) -> None:
        self._snap_btn.setText("吸附: 开" if self._snap_btn.isChecked() else "吸附: 关")

    def _open_preview(self) -> None:
        if not self._layout_data:
            QMessageBox.information(self, "提示", "请先选择适配器以加载 layout.json")
            return
        if not self._dag_service:
            QMessageBox.information(self, "提示", "请先选择适配器以加载 DAG 服务")
            return

        dialog = ResolutionPreviewDialog(
            layout_data=self._layout_data,
            dag_service=self._dag_service,
            adapter_name=self._adapter_selector.currentText(),
            parent=self,
        )
        dialog.setMinimumSize(900, 600)
        dialog.exec()
