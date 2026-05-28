#!/usr/bin/env python3
"""布局编辑器画布 — 基于 QGraphicsView 的可视化布局编辑器。

支持通过 AdapterManager 加载适配包变量和 layout.json。
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
    QFileDialog,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)


class LayoutCanvasPanel(QWidget):
    """布局编辑器面板 — 左栏变量池 + 中栏画布 + 右栏属性。"""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._dag_data: dict | None = None
        self._layout_data: dict | None = None
        self._adapter_path: Path | None = None
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

            self._var_list.clear()
            for var_name in pkg.dag_service.dag.variables:
                self._var_list.addItem(var_name)

            layout_path = self._adapter_path / "ui" / "layout.json"
            if layout_path.is_file():
                self._layout_data = json.loads(layout_path.read_text(encoding="utf-8"))
                self._status_label.setText(f"已加载 {name} — layout.json + {len(pkg.dag_service.dag.variables)} 变量")
            else:
                self._layout_data = {"sections": []}
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
        path.write_text(json.dumps(self._layout_data, ensure_ascii=False, indent=2), encoding="utf-8")
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
