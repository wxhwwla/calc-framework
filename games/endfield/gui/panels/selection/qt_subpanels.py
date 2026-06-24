#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""

PySide6 选择面板子组件：信赖等级 / 技能等级。



替代 CTk 版 ``TrustPanel`` / ``SkillLevelPanel``。

武器特殊能力面板见 ``qt_ability_panel.py``。

"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSlider,
    QVBoxLayout,
    QWidget,
)

_SLIDER_STYLE = """

    QSlider::groove:horizontal {

        background: #3A3A3A; height: 6px; border-radius: 3px;

    }

    QSlider::handle:horizontal {

        background: #2B6CB6; width: 14px; height: 14px;

        margin: -4px 0; border-radius: 7px;

    }

    QSlider::sub-page:horizontal { background: #2B6CB6; border-radius: 3px; }

"""


_LABEL_STYLE = "color: #AAAAAA; padding: 2px 0;"

_VALUE_STYLE = "color: #D1D1D1;"


def _val_label(font: QFont) -> QLabel:
    lbl = QLabel("0")

    lbl.setFont(font)

    lbl.setStyleSheet(_VALUE_STYLE)

    lbl.setFixedWidth(30)

    lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

    """val label。"""
    return lbl


def _slider(vmin: int, vmax: int, val: int) -> QSlider:
    s = QSlider(Qt.Orientation.Horizontal)

    s.setMinimum(vmin)

    s.setMaximum(vmax)

    s.setValue(val)

    s.setStyleSheet(_SLIDER_STYLE)

    """slider。"""
    return s


# ═══════════════════════════════════════════════════════

#  1. 信赖等级

# ═══════════════════════════════════════════════════════


class QtTrustPanel(QWidget):
    """角色信赖等级滑块（0-4 级）。"""

    def __init__(self, font: QFont, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._level = 0

        layout = QVBoxLayout(self)

        layout.setContentsMargins(0, 0, 0, 0)

        layout.setSpacing(2)

        lbl = QLabel("信赖")

        lbl.setFont(font)

        lbl.setStyleSheet(_LABEL_STYLE)

        layout.addWidget(lbl)

        row = QHBoxLayout()

        row.setContentsMargins(0, 0, 0, 0)

        self._val_lbl = _val_label(font)

        self._val_lbl.setText("0")

        self._slider = _slider(0, 4, 0)

        self._slider.valueChanged.connect(self._on_change)

        row.addWidget(self._slider, stretch=1)

        row.addWidget(self._val_lbl)

        layout.addLayout(row)
        """初始化实例。"""

    def _on_change(self, value: int) -> None:
        self._level = value

        self._val_lbl.setText(str(value))
        """on change。"""

    @property
    def trust_level(self) -> int:
        """trust level。"""
        return self._level

    def reset(self) -> None:
        self._level = 0

        self._slider.setValue(0)

        self._val_lbl.setText("0")
        """重置为默认状态。"""

    def set_level(self, level: int) -> None:
        clamped = max(0, min(level, 4))

        self._level = clamped

        self._slider.setValue(clamped)

        self._val_lbl.setText(str(clamped))
        """设置level。"""


# ═══════════════════════════════════════════════════════

#  2. 技能等级（战技/连携/终结）

# ═══════════════════════════════════════════════════════


class QtSkillLevelPanel(QWidget):
    """角色战技/连携/终结技等级滑块（1-12 级）。"""

    def __init__(self, font: QFont, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._names: list[str] = ["战技", "连携技", "终结技"]

        self._levels: list[int] = [1, 1, 1]

        self._has_data: list[bool] = [True, True, True]

        self._sliders: list[QSlider] = []

        self._value_labels: list[QLabel] = []

        self._name_labels: list[QLabel] = []

        self._rows: list[QWidget] = []

        layout = QVBoxLayout(self)

        layout.setContentsMargins(0, 0, 0, 0)

        layout.setSpacing(2)

        for i, name in enumerate(self._names):
            name_lbl = QLabel(name)

            name_lbl.setFont(font)

            name_lbl.setStyleSheet(_LABEL_STYLE)

            layout.addWidget(name_lbl)

            self._name_labels.append(name_lbl)

            row_w = QWidget()

            row_layout = QHBoxLayout(row_w)

            row_layout.setContentsMargins(0, 0, 0, 0)

            val_lbl = _val_label(font)

            val_lbl.setText("1")

            slider = _slider(1, 12, 1)

            slider.valueChanged.connect(lambda v, idx=i: self._on_skill_change(idx, v))

            row_layout.addWidget(slider, stretch=1)

            row_layout.addWidget(val_lbl)

            layout.addWidget(row_w)

            self._sliders.append(slider)

            self._value_labels.append(val_lbl)

            self._rows.append(row_w)
        """初始化实例。"""

    def _on_skill_change(self, idx: int, value: int) -> None:
        self._levels[idx] = value

        self._value_labels[idx].setText(str(value))
        """on skill change。"""

    def refresh(self, char_data: dict[str, Any]) -> None:
        skill_keys = ["战技倍率", "连携技倍率", "终结技倍率"]

        for i, key in enumerate(skill_keys):
            data = char_data.get(key, [])

            has_data = len(data) >= 1

            self._has_data[i] = has_data

            self._name_labels[i].setVisible(has_data)

            self._rows[i].setVisible(has_data)

            if has_data:
                self._levels[i] = 1

                self._sliders[i].setValue(1)

                self._value_labels[i].setText("1")

        self.setVisible(any(self._has_data))
        """刷新界面状态。"""

    def apply_preset(self, level: int) -> None:
        clamped = max(1, min(level, 12))

        for i in range(3):
            if self._has_data[i]:
                self._sliders[i].setValue(clamped)

                self._levels[i] = clamped

                self._value_labels[i].setText(str(clamped))
        """应用preset。"""

    def apply_levels(self, s1: int, s2: int, s3: int) -> None:
        for idx, val in enumerate([s1, s2, s3]):
            if self._has_data[idx]:
                self._sliders[idx].setValue(val)

                self._levels[idx] = val

                self._value_labels[idx].setText(str(val))
        """应用levels。"""

    @property
    def skill_1_level(self) -> int:
        """skill 1 level。"""
        return self._levels[0]

    @property
    def skill_2_level(self) -> int:
        """skill 2 level。"""
        return self._levels[1]

    @property
    def skill_3_level(self) -> int:
        """skill 3 level。"""
        return self._levels[2]
