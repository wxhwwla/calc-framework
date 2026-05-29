#!/usr/bin/env python3
"""手动场外 buff 编辑窗口（PySide6 版）。"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from calculation.manual_buff.model import (
    MANUAL_BUFF_ZONE_OPTIONS,
    build_active_keys_from_counts,
    empty_buff_dict,
    get_buffs_for_key,
    set_buffs_for_key,
)

_WINDOW_TITLE = "额外加成微调"
_WINDOW_WIDTH = 900
_WINDOW_HEIGHT = 600


def _format_key_label(key: str) -> str:
    parts = key.rsplit(":", 1)
    if len(parts) == 2:
        return f"{parts[0]} 第{parts[1]}次"
    return key


class QtManualBuffDialog(QDialog):
    """手动 Buff 微调对话框。

    左列：段/异常 key 列表（QListWidget）
    右列：当前选中 key 的乘区编辑器（ComboBox + DoubleSpinBox）
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        big_font: QFont,
        small_font: QFont,
        read_counts_callback,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(_WINDOW_TITLE)
        self.resize(_WINDOW_WIDTH, _WINDOW_HEIGHT)
        self.setMinimumSize(700, 400)

        self._big = big_font
        self._small = small_font
        self._read_counts = read_counts_callback
        self._store: dict[str, list[dict[str, str | float]]] = empty_buff_dict()

        main = QHBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        # 左列
        left = QWidget()
        left.setFixedWidth(260)
        left.setStyleSheet("background-color: #1a1a2e;")
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(8, 8, 8, 8)

        left_header = QWidget()
        hdr_lay = QHBoxLayout(left_header)
        hdr_lay.setContentsMargins(0, 0, 0, 0)
        hdr = QLabel("段 / 异常")
        hdr.setFont(self._big)
        hdr.setStyleSheet("color: #FF6B6B;")
        hdr_lay.addWidget(hdr)
        hdr_lay.addStretch()
        refresh_btn = QPushButton("刷新")
        refresh_btn.setFont(self._small)
        refresh_btn.setStyleSheet(
            "color: #D1D1D1; background: transparent; border: 1px solid #464646; border-radius: 4px; padding: 2px 8px;"
        )
        refresh_btn.clicked.connect(self._refresh_key_list)
        hdr_lay.addWidget(refresh_btn)
        left_lay.addWidget(left_header)

        self._key_list = QListWidget()
        self._key_list.setStyleSheet("""
            QListWidget { background: transparent; border: none; color: #D1D1D1; }
            QListWidget::item { padding: 6px 4px; border-radius: 4px; }
            QListWidget::item:selected { background-color: #2B6CB6; }
            QListWidget::item:hover { background-color: #333333; }
        """)
        self._key_list.currentItemChanged.connect(self._on_key_selected)
        left_lay.addWidget(self._key_list, stretch=1)

        main.addWidget(left)

        # 分隔线
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("color: #333333;")
        main.addWidget(sep)

        # 右列
        right = QWidget()
        right.setStyleSheet("background-color: #1e1e30;")
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(12, 8, 12, 8)

        self._right_header = QLabel("选择左侧项目进行编辑")
        self._right_header.setFont(self._big)
        self._right_header.setStyleSheet("color: #4ECDC4;")
        right_lay.addWidget(self._right_header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")
        self._edit_container = QWidget()
        self._edit_lay = QVBoxLayout(self._edit_container)
        self._edit_lay.setContentsMargins(0, 0, 0, 0)
        self._edit_lay.setSpacing(4)
        self._edit_lay.addStretch()
        scroll.setWidget(self._edit_container)
        right_lay.addWidget(scroll, stretch=1)

        main.addWidget(right, stretch=1)

        self._refresh_key_list()

    def _refresh_key_list(self) -> None:
        self._key_list.blockSignals(True)
        self._key_list.clear()
        skill_counts, pab_counts, sab_counts = self._read_counts()
        keys = build_active_keys_from_counts(
            skill_counts=skill_counts,
            physical_abnormal_counts=pab_counts,
            spell_abnormal_counts=sab_counts,
        )
        if not keys:
            item = QListWidgetItem("暂无已配置的段/异常次数\n请在高级页设置次数 > 0 后重试")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            item.setForeground(Qt.gray)
            self._key_list.addItem(item)
            self._key_list.blockSignals(False)
            return

        for key in keys:
            has_buffs = bool(get_buffs_for_key(self._store, key))
            item = QListWidgetItem(_format_key_label(key))
            if has_buffs:
                item.setForeground(Qt.white)
                item.setBackground(Qt.darkBlue)
            self._key_list.addItem(item)
            item.setData(Qt.ItemDataRole.UserRole, key)
        self._key_list.blockSignals(False)

    def _on_key_selected(self, current: QListWidgetItem | None, _previous: Any) -> None:
        for i in range(self._edit_lay.count()):
            w = self._edit_lay.itemAt(i)
            if w and w.widget():
                w.widget().setParent(None)

        if current is None:
            self._right_header.setText("选择左侧项目进行编辑")
            return

        key = current.data(Qt.ItemDataRole.UserRole)
        if not key:
            self._right_header.setText("选择左侧项目进行编辑")
            return

        self._right_header.setText(f"{_format_key_label(key)} 的乘区微调")
        self._render_editor(key)

    def _render_editor(self, key: str) -> None:
        entries = get_buffs_for_key(self._store, key)
        row_data: list[dict] = []

        for e in entries:
            row_data.append(
                {
                    "effect_type": e["effect_type"],
                    "value": str(e["value"] * 100),
                }
            )
        if not row_data:
            row_data.append({"effect_type": MANUAL_BUFF_ZONE_OPTIONS[0][0], "value": "0"})

        def _render_rows() -> None:
            for i in range(self._edit_lay.count()):
                w = self._edit_lay.itemAt(i)
                if w and w.widget():
                    w.widget().setParent(None)

            for idx, rd in enumerate(row_data):
                row = QWidget()
                row.setFixedHeight(36)
                row_lay = QHBoxLayout(row)
                row_lay.setContentsMargins(0, 0, 0, 0)
                row_lay.setSpacing(6)

                combo = QComboBox()
                combo.addItems([label for label, _ in MANUAL_BUFF_ZONE_OPTIONS])
                combo.setCurrentText(rd["effect_type"])
                combo.setFont(self._small)
                combo.setStyleSheet("""
                    QComboBox { background: #2B2B2B; color: #D1D1D1;
                        border: 1px solid #464646; border-radius: 4px;
                        padding: 2px 6px; min-width: 120px; }
                    QComboBox:hover { border-color: #2B6CB6; }
                    QComboBox::drop-down { border-left: 1px solid #464646; width: 20px; }
                    QComboBox QAbstractItemView {
                        background: #2B2B2B; color: #D1D1D1;
                        selection-background-color: #2B6CB6; }
                """)
                row_lay.addWidget(combo)

                plus_lbl = QLabel("+")
                plus_lbl.setFont(self._small)
                plus_lbl.setStyleSheet("color: #CCCCCC;")
                row_lay.addWidget(plus_lbl)

                spin = QDoubleSpinBox()
                spin.setRange(-9999.0, 9999.0)
                spin.setDecimals(1)
                spin.setValue(float(rd["value"]))
                spin.setFont(self._small)
                spin.setStyleSheet("""
                    QDoubleSpinBox { background: #2B2B2B; color: #D1D1D1;
                        border: 1px solid #464646; border-radius: 4px;
                        padding: 2px 4px; min-width: 70px; }
                    QDoubleSpinBox:focus { border-color: #2B6CB6; }
                """)
                row_lay.addWidget(spin)

                pct_lbl = QLabel("%")
                pct_lbl.setFont(self._small)
                pct_lbl.setStyleSheet("color: #CCCCCC;")
                row_lay.addWidget(pct_lbl)

                row_lay.addStretch()

                del_btn = QPushButton("×")
                del_btn.setFixedWidth(28)
                del_btn.setStyleSheet("""
                    QPushButton { background: #8B0000; color: white;
                        border-radius: 4px; font-weight: bold; }
                    QPushButton:hover { background: #FF0000; }
                """)
                del_btn.clicked.connect(lambda _, i=idx: (_remove_row(i), _commit()))
                row_lay.addWidget(del_btn)

                combo.currentTextChanged.connect(lambda _: _commit())
                spin.valueChanged.connect(lambda: _commit())

                self._edit_lay.insertWidget(self._edit_lay.count() - 1, row)

        def _remove_row(idx: int) -> None:
            if 0 <= idx < len(row_data):
                row_data.pop(idx)
            _render_rows()
            _commit()

        def _commit() -> None:
            result: list[dict[str, str | float]] = []
            widgets_in_lay = []
            for i in range(self._edit_lay.count()):
                w = self._edit_lay.itemAt(i)
                if w and w.widget() and w.widget() is not self._edit_lay.itemAt(self._edit_lay.count() - 1).widget():
                    widgets_in_lay.append(w.widget())

            for w in widgets_in_lay:
                children = w.findChildren(QComboBox) + w.findChildren(QDoubleSpinBox)
                combos = [c for c in children if isinstance(c, QComboBox)]
                spins = [c for c in children if isinstance(c, QDoubleSpinBox)]
                if combos and spins:
                    et = combos[0].currentText().strip()
                    val = spins[0].value()
                    if et:
                        result.append({"effect_type": et, "value": val / 100.0})

            set_buffs_for_key(self._store, key, result)
            self._refresh_key_list()

        _render_rows()

        add_btn = QPushButton("+ 添加乘区")
        add_btn.setFont(self._small)
        add_btn.setStyleSheet("""
            QPushButton { background: #2d6a4f; color: white;
                border-radius: 6px; padding: 6px; }
            QPushButton:hover { background: #40916c; }
        """)
        self._edit_lay.addWidget(add_btn)
