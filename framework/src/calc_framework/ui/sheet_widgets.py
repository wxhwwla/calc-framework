# -*- coding: utf-8 -*-
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
    QLabel,
    QSlider,
    QSpinBox,
    QWidget,
)

from .controls import ControlSpec

# 单个「标签 + 控件」项的舒适宽度。取值需覆盖较长中文描述（约 200px）
# 与输入框（约 130px）；过小会在窄窗口排成两列后超出可视宽度。
_AVG_ITEM_WIDTH = 340

# 数值输入框的最小宽度。QSpinBox 会按最大值文本（如 2^31-1）计算最小宽度，
# 不加限制会把整列撑到可视区之外；显式设置后布局可压缩输入框。
_MIN_CONTROL_WIDTH = 90

# DAG 变量未声明 max 时的实际上限。QSpinBox/QDoubleSpinBox 自带 99/99.99
# 的默认上限，会把「无上限」的输入静默截断。
_NO_MAX_INT = 2_147_483_647
_NO_MAX_FLOAT = 1_000_000_000_000.0


class _ResponsiveGroupBox(QGroupBox):
    """QGroupBox 子类，根据可用宽度自动重排行内 input 项。

    重排会调用 ``setParent(None)`` / ``addWidget``，改变布局尺寸提示并可能
    同步触发新的 resize。因此仅在列数真正变化时重建，并用重入标记阻止
    嵌套调用——否则会形成 resize ↔ 重排的反馈循环，事件循环被持续占用
    （查看器表现为窗口卡死）。
    """

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
        self._columns = 0
        self._relayouting = False
        for _var_path, label, _widget, _spec in items:
            # 长中文描述允许换行，窗口较窄时不会把整页撑出横向滚动条。
            label.setWordWrap(True)

    def _on_resized(self) -> None:
        available = self.width() - 40
        cols = max(1, available // _AVG_ITEM_WIDTH)
        cols = cols * 2  # each item takes 2 columns (label + widget)

        if self._relayouting or cols == self._columns:
            return

        self._relayouting = True
        try:
            self._columns = cols
            while self._grid.count():
                item = self._grid.takeAt(0)
                w = item.widget()
                if w:
                    w.setParent(None)

            for i, (_var_path, label, widget, _spec) in enumerate(self._items):
                row = i // (cols // 2)
                col_offset = (i % (cols // 2)) * 2
                self._grid.addWidget(label, row, col_offset)
                if widget is not None:
                    self._grid.addWidget(widget, row, col_offset + 1)

            # 每个输入控件列均分剩余宽度；只给首列拉伸会把后续列挤出可视区。
            for column in range(cols):
                self._grid.setColumnStretch(column, 1 if column % 2 else 0)
        finally:
            self._relayouting = False

    def resizeEvent(self, event) -> None:  # noqa: N802
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


def _decimals_for_step(step: float) -> int:
    """按步长推导小数位数（0.01 → 2，0.5 → 1，整步长 → 0）。"""
    text = f"{float(step):g}"
    if "." not in text:
        return 0
    return len(text.split(".", 1)[1])


def make_spinbox(spec: ControlSpec) -> QWidget:
    """根据 spec 创建 QSpinBox 或 QDoubleSpinBox 控件。

    未声明 ``max_val`` 时把上限提高到 Qt 的安全大值，避免 QSpinBox /
    QDoubleSpinBox 自带的 99 / 99.99 默认上限静默截断用户输入；只有
    DAG 变量显式声明 ``max`` 时才施加业务上限。
    """
    if isinstance(spec.default, int) or spec.step == 1:
        box = QSpinBox()
        box.setMaximum(_NO_MAX_INT)
        box.setSingleStep(int(spec.step))
        if spec.min_val is not None:
            box.setMinimum(int(spec.min_val))
        if spec.max_val is not None:
            box.setMaximum(int(spec.max_val))
        box.setValue(int(spec.default))
    else:
        box = QDoubleSpinBox()
        box.setDecimals(_decimals_for_step(spec.step))
        box.setMaximum(_NO_MAX_FLOAT)
        box.setSingleStep(spec.step)
        if spec.min_val is not None:
            box.setMinimum(float(spec.min_val))
        if spec.max_val is not None:
            box.setMaximum(float(spec.max_val))
        box.setValue(float(spec.default))
    if spec.suffix:
        box.setSuffix(spec.suffix)
    box.setMinimumWidth(_MIN_CONTROL_WIDTH)
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
