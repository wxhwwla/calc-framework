#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级页控制栏（PySide6 版）。

与 CTk 版 ``app_control_dock.py`` 平行的 Qt 实现。
当前仅迁移操作/乘区展示列；搜索与多技能区块为占位符，待后续阶段迁移。
"""

from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from gui_design.shared.calc_mode_labels import CALC_MODE_LABELS, DEFAULT_CALC_MODE_LABEL

# ── 尺寸常量（与 gui_layout 同步） ──────────────────────────
_PRIMARY_BTN_HEIGHT = 40
_SECONDARY_BTN_HEIGHT = 32
_SECTION_HEADER_COLOR = "#FF6B6B"
_LABEL_SECONDARY_COLOR = "#CCCCCC"


class _SectionHeader(QLabel):
    """区块标题（红色高亮）。"""

    def __init__(self, text: str, font: QFont) -> None:
        super().__init__(text)
        self.setFont(font)
        self.setStyleSheet(f"color: {_SECTION_HEADER_COLOR};")


class _PlaceholderSection(QFrame):
    """待迁移区块占位符。"""

    def __init__(self, title: str, hint: str, font: QFont) -> None:
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("QFrame { border: 1px dashed #464646; border-radius: 4px; }")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        title_lbl = QLabel(title)
        title_lbl.setFont(font)
        title_lbl.setStyleSheet(f"color: {_SECTION_HEADER_COLOR}; border: none;")
        layout.addWidget(title_lbl)
        hint_lbl = QLabel(hint)
        hint_lbl.setStyleSheet("color: #828282; border: none;")
        hint_lbl.setWordWrap(True)
        layout.addWidget(hint_lbl)
        layout.addStretch()


class QtControlDock(QWidget):
    """高级页三列控制栏（PySide6 版）。"""

    calc_mode_changed = Signal(str)

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        *,
        big_font: Optional[QFont] = None,
        small_font: Optional[QFont] = None,
        on_back_to_main: Optional[Callable[[], None]] = None,
        on_confirm: Optional[Callable[[], None]] = None,
        on_attribution: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(parent)
        self._big_font = big_font or QFont()
        self._small_font = small_font or QFont()
        self._on_back_to_main = on_back_to_main
        self._on_confirm = on_confirm
        self._on_attribution = on_attribution

        self.back_to_main_btn: QPushButton
        self.confirm_btn: QPushButton
        self.attribution_btn: QPushButton
        self.calc_mode_menu: QComboBox

        self._build_ui()

    def _make_btn(self, text: str, height: int, primary: bool = False) -> QPushButton:
        btn = QPushButton(text)
        btn.setMinimumHeight(height)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        if primary:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2B6CB6;
                    color: white;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #3182CE; }
                QPushButton:pressed { background-color: #2C5282; }
            """)
        else:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #D1D1D1;
                    border: 1px solid #464646;
                    border-radius: 6px;
                }
                QPushButton:hover { border-color: #2B6CB6; color: white; }
            """)
        return btn

    def _build_ui(self) -> None:
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        # ── 列 1：操作 / 乘区展示 ──────────────────────
        col_actions = QWidget()
        col_actions.setMinimumWidth(200)
        col_actions.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        al = QVBoxLayout(col_actions)
        al.setContentsMargins(4, 4, 4, 4)
        al.setSpacing(4)

        al.addWidget(_SectionHeader("操作", self._big_font))

        self.back_to_main_btn = self._make_btn("返回计算页", _SECONDARY_BTN_HEIGHT)
        if self._on_back_to_main:
            self.back_to_main_btn.clicked.connect(self._on_back_to_main)
        al.addWidget(self.back_to_main_btn)

        self.confirm_btn = self._make_btn("确认选择", _PRIMARY_BTN_HEIGHT, primary=True)
        if self._on_confirm:
            self.confirm_btn.clicked.connect(self._on_confirm)
        al.addWidget(self.confirm_btn)

        self.attribution_btn = self._make_btn("数据来源与许可", _SECONDARY_BTN_HEIGHT)
        if self._on_attribution:
            self.attribution_btn.clicked.connect(self._on_attribution)
        al.addWidget(self.attribution_btn)

        al.addSpacing(8)
        al.addWidget(_SectionHeader("乘区展示", self._big_font))

        mode_label = QLabel("计算模式")
        mode_label.setStyleSheet(f"color: {_LABEL_SECONDARY_COLOR};")
        al.addWidget(mode_label)

        self.calc_mode_menu = QComboBox()
        self.calc_mode_menu.addItems(list(CALC_MODE_LABELS))
        self.calc_mode_menu.setCurrentText(DEFAULT_CALC_MODE_LABEL)
        self.calc_mode_menu.currentTextChanged.connect(self._on_calc_mode_changed)
        self.calc_mode_menu.setStyleSheet("""
            QComboBox {
                background-color: #2B2B2B;
                color: #D1D1D1;
                border: 1px solid #464646;
                border-radius: 4px;
                padding: 2px 6px;
                min-height: 28px;
            }
            QComboBox:hover { border-color: #2B6CB6; }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #464646;
            }
            QComboBox QAbstractItemView {
                background-color: #2B2B2B;
                color: #D1D1D1;
                selection-background-color: #2B6CB6;
                border: 1px solid #464646;
            }
        """)
        al.addWidget(self.calc_mode_menu)

        # 增强操作区块（占位符）
        al.addWidget(_PlaceholderSection(
            "工具与分享", "导入导出、仪表盘、插件等（待迁移）", self._big_font
        ))

        al.addStretch()

        # ── 列 2：全量搜索（占位符） ─────────────────
        col_search = QWidget()
        col_search.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sl = QVBoxLayout(col_search)
        sl.setContentsMargins(4, 4, 4, 4)
        sl.addWidget(_PlaceholderSection(
            "全量搜索", "搜索参数、固定配装、遍历按钮等（待迁移）", self._big_font
        ))
        sl.addStretch()

        # ── 列 3：多技能次数（占位符） ──────────────
        col_multi = QWidget()
        col_multi.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        ml = QVBoxLayout(col_multi)
        ml.setContentsMargins(4, 4, 4, 4)
        ml.addWidget(_PlaceholderSection(
            "多技能次数", "技能段数、异常矩阵、手动增益等（待迁移）", self._big_font
        ))
        ml.addStretch()

        outer.addWidget(col_actions, stretch=1)
        outer.addWidget(col_search, stretch=2)
        outer.addWidget(col_multi, stretch=3)

    def _on_calc_mode_changed(self, text: str) -> None:
        self.calc_mode_changed.emit(text)

    def current_calc_mode(self) -> str:
        return self.calc_mode_menu.currentText()
