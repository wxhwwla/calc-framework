#!/usr/bin/env python3
"""布局编辑器画布 — 基于 QGraphicsView 的可视化布局编辑器。

当前为骨架，后续版本将提供：
- 拖拽变量到画布生成控件卡片
- 网格吸附（列数/间距可配置）
- 碰撞实时高亮
- 导出布局到 layout.json
"""

from __future__ import annotations

import json
import os
import sys

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
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
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        toolbar = QHBoxLayout()
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

        status = QLabel("就绪 — 加载 DAG 后拖拽变量到画布")
        layout.addWidget(status)

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
        except Exception as e:
            QMessageBox.critical(self, "加载失败", str(e))

    def _toggle_snap(self) -> None:
        self._snap_btn.setText("吸附: 开" if self._snap_btn.isChecked() else "吸附: 关")
