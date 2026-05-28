#!/usr/bin/env python3
"""主题编辑器 — 字体/色板配置 + .calcpack 导出。

骨架版本提供基础的导出功能，后续将添加可视化色板编辑。
"""

from __future__ import annotations

import json
import os
import sys

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class ThemePanel(QWidget):
    """主题与导出面板。"""

    export_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._theme: dict = self._default_theme()
        self._dag_data: dict | None = None
        self._layout_data: dict | None = None
        self._data_files: dict[str, list] = {}
        self._build_ui()

    def _default_theme(self) -> dict:
        return {
            "schema_version": "theme-v1",
            "name": "默认深色",
            "font": {"family": "Microsoft YaHei", "size": 12, "weight": "normal"},
            "colors": {
                "primary": "#0078D4",
                "background": "#1E1E1E",
                "surface": "#2D2D2D",
                "text": "#F0F0F0",
                "text_secondary": "#A0A0A0",
                "border": "#3D3D3D",
                "success": "#4ECDC4",
                "warning": "#FFD700",
                "error": "#E74C3C",
            },
            "spacing": {"padding": 8, "gap": 4},
        }

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        form = QFormLayout(content)

        self._font_family = QLineEdit("Microsoft YaHei")
        form.addRow("字体:", self._font_family)

        self._font_size = QSpinBox()
        self._font_size.setRange(8, 32)
        self._font_size.setValue(12)
        form.addRow("字号:", self._font_size)

        form.addRow(QLabel("--- 颜色 ---"))

        self._color_inputs: dict[str, QLineEdit] = {}
        for key, default in self._theme["colors"].items():
            inp = QLineEdit(default)
            self._color_inputs[key] = inp
            form.addRow(f"{key}:", inp)

        scroll.setWidget(content)
        layout.addWidget(scroll, stretch=1)

        data_group = QGroupBox("包含数据")
        data_layout = QVBoxLayout(data_group)
        self._data_label = QLabel("未加载数据")
        data_layout.addWidget(self._data_label)
        load_data_btn = QPushButton("加载数据 JSON")
        load_data_btn.clicked.connect(self._load_data)
        data_layout.addWidget(load_data_btn)
        load_dag_btn = QPushButton("加载 DAG JSON")
        load_dag_btn.clicked.connect(self._load_dag)
        data_layout.addWidget(load_dag_btn)
        load_layout_btn = QPushButton("加载 layout.json")
        load_layout_btn.clicked.connect(self._load_layout)
        data_layout.addWidget(load_layout_btn)
        layout.addWidget(data_group)

        export_btn = QPushButton("导出 .calcpack")
        export_btn.setStyleSheet("QPushButton { padding: 12px; font-size: 14px; }")
        export_btn.clicked.connect(self._export)
        layout.addWidget(export_btn)

    def _load_dag(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 DAG JSON", "", "JSON Files (*.json)"
        )
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                self._dag_data = json.load(f)
            QMessageBox.information(self, "已加载", f"DAG: {path}")
        except Exception as e:
            QMessageBox.critical(self, "失败", str(e))

    def _load_layout(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 layout.json", "", "JSON Files (*.json)"
        )
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                self._layout_data = json.load(f)
            QMessageBox.information(self, "已加载", f"Layout: {path}")
        except Exception as e:
            QMessageBox.critical(self, "失败", str(e))

    def _load_data(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "选择数据 JSON", "", "JSON Files (*.json)"
        )
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            name = os.path.splitext(os.path.basename(path))[0]
            if isinstance(data, list):
                self._data_files[name] = data
            else:
                self._data_files[name] = [data]
            self._data_label.setText(
                f"已加载: {', '.join(f'{k}({len(v)}条)' for k, v in self._data_files.items())}"
            )
        except Exception as e:
            QMessageBox.critical(self, "失败", str(e))

    def _build_theme(self) -> dict:
        return {
            "schema_version": "theme-v1",
            "name": "自定义主题",
            "font": {
                "family": self._font_family.text(),
                "size": self._font_size.value(),
                "weight": "normal",
            },
            "colors": {k: v.text() for k, v in self._color_inputs.items()},
            "spacing": {"padding": 8, "gap": 4},
        }

    def _read_meta(self) -> dict:
        return {
            "name": "自定义计算配置",
            "game": "自定义",
            "version": "1.0.0",
            "schema_version": "dag-v1",
            "author": "",
            "description": "由配置包设计器导出",
            "entry_dag": "dag/formula.dag.json",
            "ui_layout": "ui/layout.json",
            "ui_theme": "ui/theme.json",
            "entry_data": [f"data/{k}.json" for k in self._data_files],
        }

    def _export(self) -> None:
        if not self._dag_data:
            QMessageBox.warning(self, "缺少 DAG", "请先加载 DAG JSON")
            return
        if not self._layout_data:
            QMessageBox.warning(self, "缺少布局", "请先加载 layout.json")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "导出 .calcpack", "game.calcpack",
            "CalcPack (*.calcpack);;ZIP (*.zip);;All Files (*)",
        )
        if not path:
            return

        from tools.designer.exporter import export_calcpack

        try:
            result = export_calcpack(
                output_path=path,
                meta=self._read_meta(),
                dag=self._dag_data,
                layout=self._layout_data,
                theme=self._build_theme(),
                data_files=self._data_files,
            )
            QMessageBox.information(self, "导出成功", f"已写入:\n{result}")
            self.export_requested.emit(result)
        except Exception as e:
            QMessageBox.critical(self, "导出失败", str(e))
