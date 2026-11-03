# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""计算历史弹窗：最近 10 次计算 + 恢复配置。"""

from __future__ import annotations

from calc_framework.ui.i18n import tr
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from games.endfield.gui.app.loadout_preset import LoadoutPreset
from games.endfield.gui.shared.calc_history import CalculationHistory

from .qt_dialogs_styles import _HINT_COLOR, _SEC_BTN_STYLE

__all__ = ["QtCalcHistoryDialog"]


class QtCalcHistoryDialog(QDialog):
    """计算历史（最近 10 次）+ 恢复此配置按钮。"""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        big_font: QFont,
        small_font: QFont,
        history: CalculationHistory,
        apply_fn=None,
    ) -> None:
        super().__init__(parent)

        self.setWindowTitle(tr("desktop.endfield.dialogHistTitle"))

        self.resize(520, 420)

        self.setMinimumSize(400, 300)

        self._big = big_font

        self._small = small_font

        self._history = history

        self._apply_fn = apply_fn

        layout = QVBoxLayout(self)

        layout.setContentsMargins(12, 12, 12, 12)

        scroll = QScrollArea()

        scroll.setWidgetResizable(True)

        scroll.setFrameShape(QFrame.Shape.NoFrame)

        scroll.setStyleSheet("QScrollArea { background: transparent; }")

        body = QWidget()

        body_layout = QVBoxLayout(body)

        body_layout.setContentsMargins(0, 0, 0, 0)

        body_layout.setSpacing(4)

        entries = history.list_entries()

        if not entries:
            lbl = QLabel(tr("common.noData"))

            lbl.setFont(small_font)

            lbl.setStyleSheet(_HINT_COLOR)

            body_layout.addWidget(lbl)

        else:
            for idx, entry in enumerate(entries):
                card = QFrame()

                card.setStyleSheet("QFrame { background-color: #2a2a2a; border-radius: 6px; }")

                card_layout = QVBoxLayout(card)

                card_layout.setContentsMargins(8, 6, 8, 6)

                text = QLabel(f"{entry.label}\n{entry.summary}")

                text.setFont(small_font)

                text.setStyleSheet("color: #CCCCCC;")

                text.setWordWrap(True)

                card_layout.addWidget(text)

                restore_btn = QPushButton(tr("desktop.endfield.dialogRestoreConfig"))

                restore_btn.setFont(small_font)

                restore_btn.setStyleSheet(_SEC_BTN_STYLE)

                restore_btn.clicked.connect(lambda _, i=idx: self._restore(i))

                card_layout.addWidget(restore_btn, alignment=Qt.AlignmentFlag.AlignRight)

                body_layout.addWidget(card)

        body_layout.addStretch()

        scroll.setWidget(body)

        layout.addWidget(scroll, stretch=1)

        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)

        btn_box.rejected.connect(self.reject)

        layout.addWidget(btn_box)

    def _restore(self, index: int) -> None:
        """恢复指定索引的历史配置到面板。"""

        snap = self._history.get_snapshot(index)

        if not snap:
            return

        if self._apply_fn:
            try:
                self._apply_fn(LoadoutPreset.from_dict(snap))

                self.accept()

            except Exception as exc:
                QMessageBox.warning(self, tr("desktop.endfield.dialogRestoreFailed"), str(exc))
