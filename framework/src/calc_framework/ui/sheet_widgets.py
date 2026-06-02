# SPDX-License-Identifier: AGPL-3.0
"""ComputeSheet 控件生成 — 为 layout.json 每个控件类型创建对应 Qt 控件。

从 compute_sheet.py 拆分而来。
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QSlider,
    QSpinBox,
    QWidget,
)

from .controls import ControlSpec

_AVG_ITEM_WIDTH = 280


class _ResponsiveGroupBox(QGroupBox):
    """QGroupBox 子类，根据可用宽度自动重排行内 input 项。"""

    def __init__(
        self,
        title: str,
        items: list[tuple[str, QLabel, QWidget | None, ControlSpec]],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(title, parent)
        self._items = items
        self._grid = QGridLayout(self)
        self._grid.setColumnStretch(1, 1)

    def _on_resized(self) -> None:
        available = self.width() - 40
        cols = max(1, available // _AVG_ITEM_WIDTH)
        cols = cols * 2  # each item takes 2 columns (label + widget)

        while self._grid.count():
            item = self._grid.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)

        for i, (_var_path, label, widget, spec) in enumerate(self._items):
            row = i // (cols // 2)
            col_offset = (i % (cols // 2)) * 2
            self._grid.addWidget(label, row, col_offset)
            if widget is not None:
                self._grid.addWidget(widget, row, col_offset + 1)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._on_resized()


def make_slider(spec: ControlSpec) -> QWidget:
    """根据 spec 创建 QSlider 控件。"""
    min_v = int(spec.min_val or 0)
    max_v = int(spec.max_val or 100)
    if spec.step < 1:
        min_v = int(min_v * 100)
        max_v = int(max_v * 100)
        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_v, max_v)
        slider.setValue(int(float(spec.default) * 100))
        slider.setSingleStep(max(1, int(spec.step * 100)))
    else:
        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_v, max_v)
        slider.setValue(int(spec.default))
        slider.setSingleStep(int(spec.step))
    return slider


def make_spinbox(spec: ControlSpec) -> QWidget:
    """根据 spec 创建 QSpinBox 或 QDoubleSpinBox 控件。"""
    if isinstance(spec.default, int) or spec.step == 1:
        box = QSpinBox()
        box.setValue(int(spec.default))
        box.setSingleStep(int(spec.step))
    else:
        box = QDoubleSpinBox()
        box.setValue(float(spec.default))
        box.setSingleStep(spec.step)
        box.setDecimals(max(0, -int(spec.step).bit_length() if spec.step < 1 else 2))
    if spec.min_val is not None:
        box.setMinimum(spec.min_val)  # type: ignore[reportArgumentType]
    if spec.max_val is not None:
        box.setMaximum(spec.max_val)  # type: ignore[reportArgumentType]
    return box


def make_checkbox(spec: ControlSpec) -> QWidget:
    """根据 spec 创建 QCheckBox 控件。"""
    cb = QCheckBox()
    cb.setChecked(bool(spec.default))
    return cb


def make_dropdown(spec: ControlSpec) -> QWidget:
    """根据 spec 创建 QComboBox 下拉控件。"""
    combo = QComboBox()
    combo.addItems(spec.options)
    default_idx = combo.findText(str(spec.default))
    if default_idx >= 0:
        combo.setCurrentIndex(default_idx)
    return combo


def create_control(spec: ControlSpec) -> QWidget | None:
    """根据 spec.widget 类型分发到对应的控件工厂函数。"""
    if spec.widget == "slider":
        return make_slider(spec)
    if spec.widget == "spinbox":
        return make_spinbox(spec)
    if spec.widget == "switch":
        return make_checkbox(spec)
    if spec.widget == "dropdown":
        return make_dropdown(spec)
    return None
