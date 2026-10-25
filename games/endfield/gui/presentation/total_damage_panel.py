# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
from __future__ import annotations

from typing import Any

from calc_framework.ui.i18n import tr
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from games.endfield.gui.presentation.total_damage_display_data import (
    TotalDamageDisplayData,
    build_total_damage_display,
)

_SECTION_COLOR = "#FF6B6B"

_TOTAL_COLOR = "#4FC3F7"

_SUBTOTAL_COLOR = "#81C784"

_TEXT_COLOR = "#D1D1D1"

_DIM_COLOR = "#828282"

_BG_COLOR = "#1E1E1E"


class _SectionHeader(QLabel):
    def __init__(self, text: str, font: QFont) -> None:
        super().__init__(text)

        self.setFont(font)

        self.setStyleSheet(f"color: {_SECTION_COLOR}; padding: 4px 0;")
        """初始化实例。"""

    """SectionHeader。"""


class _Divider(QFrame):
    def __init__(self) -> None:
        super().__init__()

        self.setFrameShape(QFrame.Shape.HLine)

        self.setStyleSheet("color: #333333;")
        """初始化实例。"""

    """Divider。"""


def _small_label(text: str, color: str = _TEXT_COLOR) -> QLabel:
    lbl = QLabel(text)

    lbl.setStyleSheet(f"color: {color}; font-size: 12px;")

    """small label。"""
    return lbl


def _dim_label(text: str) -> QLabel:
    """dim label。"""
    return _small_label(text, _DIM_COLOR)


class TotalDamagePanel(QWidget):
    """确认后展示各技能段加权总伤的原生 Qt 面板。



    放在计算页右栏 ComputeSheet 下方，显示：

    - 各技能类型的段级明细（单次×次数=小计）

    - 技能类型汇总

    - 加权总伤

    - 计算参数摘要

    """

    def __init__(self, big_font: QFont, small_font: QFont, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._big_font = big_font

        self._small_font = small_font

        self._build_ui()
        """初始化实例。"""

    def _build_ui(self) -> None:
        self.setStyleSheet(f"background-color: {_BG_COLOR}; border-radius: 6px;")

        layout = QVBoxLayout(self)

        layout.setContentsMargins(8, 6, 8, 6)

        layout.setSpacing(4)

        header = _SectionHeader(tr("desktop.endfield.totalSettlement"), self._big_font)

        layout.addWidget(header)

        self._body = QWidget()

        self._body_layout = QVBoxLayout(self._body)

        self._body_layout.setContentsMargins(0, 0, 0, 0)

        self._body_layout.setSpacing(3)

        layout.addWidget(self._body)

        self._empty_label = QLabel(tr("desktop.endfield.totalEmptyHint"))

        self._empty_label.setStyleSheet(f"color: {_DIM_COLOR}; font-size: 12px; padding: 8px 0;")

        self._body_layout.addWidget(self._empty_label)

        layout.addStretch()
        """build ui。"""

    def update_from_snapshot(self, snapshot: Any | None) -> None:
        """用 DamageSnapshot 数据刷新面板。"""

        while self._body_layout.count():
            item = self._body_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if snapshot is None:
            self._empty_label = QLabel(tr("desktop.endfield.totalEmptyHint"))
            self._empty_label.setStyleSheet(f"color: {_DIM_COLOR}; font-size: 12px; padding: 8px 0;")
            self._body_layout.addWidget(self._empty_label)
            self._body_layout.addStretch()
            return

        data: TotalDamageDisplayData = build_total_damage_display(
            seg_damage=getattr(snapshot, "segment_damage", {}),
            seg_counts=getattr(snapshot, "segment_counts", {}),
            seg_totals=getattr(snapshot, "segment_totals", {}),
            skill_type_totals=getattr(snapshot, "skill_type_totals", {}),
            weighted_total=getattr(snapshot, "weighted_total_damage", 0.0),
            rotation_share=getattr(snapshot, "rotation_share_percent", {}),
            selected_label=getattr(snapshot, "selected_skill_label", ""),
        )

        for group in data.groups:
            header = QLabel(group.label)
            header.setStyleSheet("color: #FFD54F; font-size: 13px; font-weight: bold; padding: 2px 0;")
            self._body_layout.addWidget(header)

            for seg in group.segments:
                if seg.count <= 0:
                    continue
                share_text = f" ({seg.share:.1f}%)" if seg.share > 0 else ""
                row = _small_label(
                    tr(
                        "desktop.endfield.segmentRow",
                        index=seg.seg_index,
                        single=f"{seg.single:.1f}",
                        count=seg.count,
                        total=f"{seg.total:.1f}",
                        share=share_text,
                    )
                )
                self._body_layout.addWidget(row)

            if group.total > 0:
                sub = _small_label(tr("desktop.endfield.subtotal", total=f"{group.total:.1f}"), _SUBTOTAL_COLOR)
                self._body_layout.addWidget(sub)

        for seg in data.fallback_rows:
            if seg.count > 0:
                row = _small_label(
                    tr(
                        "desktop.endfield.genericRow",
                        key=seg.key,
                        single=f"{seg.single:.1f}",
                        count=seg.count,
                        total=f"{seg.total:.1f}",
                    )
                )
                self._body_layout.addWidget(row)

        self._body_layout.addWidget(_Divider())

        total_row = QHBoxLayout()
        total_row.setContentsMargins(0, 0, 0, 0)
        total_icon = QLabel("🏆")
        total_icon.setStyleSheet("font-size: 16px;")
        total_row.addWidget(total_icon)

        total_text = QLabel(tr("desktop.endfield.weightedTotal", total=f"{data.weighted_total:,.1f}"))
        total_font = QFont(self._big_font)
        total_font.setPointSize(16)
        total_font.setBold(True)
        total_text.setFont(total_font)
        total_text.setStyleSheet(f"color: {_TOTAL_COLOR};")
        total_row.addWidget(total_text)
        total_row.addStretch()
        self._body_layout.addLayout(total_row)

        if data.selected_label:
            info = _dim_label(tr("desktop.endfield.skillInfo", name=data.selected_label))
            self._body_layout.addWidget(info)

        self._body_layout.addStretch()

    def hide_damage(self) -> None:
        """清空面板回到空状态。"""

        self.update_from_snapshot(None)
