# SPDX-License-Identifier: AGPL-3.0
from __future__ import annotations

from typing import Any

from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from games.endfield.calc.skills.segments import parse_segment_key

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

    return lbl
    """small label。"""





def _dim_label(text: str) -> QLabel:

    return _small_label(text, _DIM_COLOR)
    """dim label。"""





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



        header = _SectionHeader("总伤结算", self._big_font)

        layout.addWidget(header)



        self._body = QWidget()

        self._body_layout = QVBoxLayout(self._body)

        self._body_layout.setContentsMargins(0, 0, 0, 0)

        self._body_layout.setSpacing(3)

        layout.addWidget(self._body)



        self._empty_label = QLabel("按「确认选择」查看总伤结算")

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

            self._empty_label = QLabel("按「确认选择」查看总伤结算")

            self._empty_label.setStyleSheet(f"color: {_DIM_COLOR}; font-size: 12px; padding: 8px 0;")

            self._body_layout.addWidget(self._empty_label)

            self._body_layout.addStretch()

            return



        seg_damage = getattr(snapshot, "segment_damage", {})

        seg_counts = getattr(snapshot, "segment_counts", {})

        seg_totals = getattr(snapshot, "segment_totals", {})

        skill_type_totals = getattr(snapshot, "skill_type_totals", {})

        weighted_total = getattr(snapshot, "weighted_total_damage", 0.0)

        rotation_share = getattr(snapshot, "rotation_share_percent", {})

        selected_label = getattr(snapshot, "selected_skill_label", "")



        _SKILL_TYPE_ORDER = ("战技", "连携技", "终结技")  # noqa: N806

        segments_by_type: dict[str, list[tuple[str, float, int, float, float]]] = {}

        for key in seg_damage:

            stype, _ = parse_segment_key(key)

            if stype not in segments_by_type:

                segments_by_type[stype] = []

            single = seg_damage.get(key, 0.0)

            count = seg_counts.get(key, 0)

            total = seg_totals.get(key, 0.0)

            share = rotation_share.get(key, 0.0)

            segments_by_type[stype].append((key, single, count, total, share))



        has_data = bool(weighted_total > 0)

        visible_types = [t for t in _SKILL_TYPE_ORDER if t in segments_by_type or t in skill_type_totals]



        for skill_type in visible_types:

            st_label = f"{skill_type}"

            st_total = skill_type_totals.get(skill_type, 0.0)

            if has_data and weighted_total > 0:

                st_pct = st_total / weighted_total * 100.0

                st_label += f" ({st_pct:.1f}%)"

            header = QLabel(st_label)

            header.setStyleSheet("color: #FFD54F; font-size: 13px; font-weight: bold; padding: 2px 0;")

            self._body_layout.addWidget(header)



            segments = segments_by_type.get(skill_type, [])

            segments.sort(key=lambda x: x[1], reverse=True)

            for key, single, count, total, share in segments:

                if count <= 0:

                    continue

                share_text = f" ({share:.1f}%)" if share > 0 else ""

                row = _small_label(

                    f"  ├ 第{key.split(':')[1]}段: {single:.1f} × {count} = {total:.1f}{share_text}"

                )

                self._body_layout.addWidget(row)



            if st_total > 0:

                sub = _small_label(f"  └ 小计: {st_total:.1f}", _SUBTOTAL_COLOR)

                self._body_layout.addWidget(sub)



        if not visible_types and has_data:

            for key, single in seg_damage.items():

                count = seg_counts.get(key, 0)

                total = seg_totals.get(key, 0.0)

                if count > 0:

                    row = _small_label(f"  {key}: {single:.1f} × {count} = {total:.1f}")

                    self._body_layout.addWidget(row)



        self._body_layout.addWidget(_Divider())



        total_row = QHBoxLayout()

        total_row.setContentsMargins(0, 0, 0, 0)

        total_icon = QLabel("🏆")

        total_icon.setStyleSheet("font-size: 16px;")

        total_row.addWidget(total_icon)

        total_text = QLabel(f"加权总伤: {weighted_total:,.1f}")

        total_font = QFont(self._big_font)

        total_font.setPointSize(16)

        total_font.setBold(True)

        total_text.setFont(total_font)

        total_text.setStyleSheet(f"color: {_TOTAL_COLOR};")

        total_row.addWidget(total_text)

        total_row.addStretch()

        self._body_layout.addLayout(total_row)



        if selected_label:

            info = _dim_label(f"技能: {selected_label}")

            self._body_layout.addWidget(info)



        self._body_layout.addStretch()



    def hide_damage(self) -> None:

        """清空面板回到空状态。"""

        self.update_from_snapshot(None)

