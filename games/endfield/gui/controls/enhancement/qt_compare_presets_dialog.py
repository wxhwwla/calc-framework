# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""多方案对比弹窗：选择多个预设 JSON，并行评估并展示排名。"""

from __future__ import annotations

from pathlib import Path

from calc_framework.ui.i18n import tr
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QLabel,
    QMessageBox,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from utils.operation_log import LogLevel, get_session_operation_log

from games.endfield.data_loading.loader import get_characters, get_equipments, get_weapons
from games.endfield.gui.app.loadout_preset import LoadoutPreset, import_presets_from_json_text
from games.endfield.gui.controls.search.search_settings import resolve_parallel_workers
from games.endfield.gui.shared.preset_batch_compare import compare_presets_parallel

from .qt_dialogs_styles import _HINT_COLOR

__all__ = ["QtComparePresetsDialog"]


class QtComparePresetsDialog(QDialog):
    """选择多个预设 JSON，并行评估并展示排名。"""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        big_font: QFont,
        small_font: QFont,
        build_preset_fn,
        enemy_defense: float = 100.0,
        enemy_resistance: float = 0.0,
        ignore_resistance: float = 0.0,
        imbalance_vulnerability_coeff: float = 1.3,
        is_unbalanced: bool = False,
        workers_choice: str = "自动",
    ) -> None:
        super().__init__(parent)

        self.setWindowTitle(tr("desktop.endfield.dialogCompareTitle"))

        self.resize(640, 480)

        self.setMinimumSize(500, 350)

        self._big = big_font

        self._small = small_font

        self._build_preset_fn = build_preset_fn

        self._enemy_defense = enemy_defense

        self._workers = resolve_parallel_workers(workers_choice)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(12, 12, 12, 12)

        paths, _ = QFileDialog.getOpenFileNames(
            self,
            tr("desktop.endfield.dialogCompareFilePicker"),
            "",
            "JSON (*.json)",
        )

        if not paths:
            self._no_data = True

            layout.addWidget(QLabel(tr("desktop.endfield.dialogNoFilesSelected")))

            return

        self._no_data = False

        presets: list[LoadoutPreset] = []

        try:
            for p in paths:
                presets.extend(import_presets_from_json_text(Path(p).read_text(encoding="utf-8")))

            presets.insert(0, build_preset_fn())

        except Exception as exc:
            QMessageBox.warning(self, tr("desktop.endfield.dialogReadPresetFailed"), str(exc))

            self._no_data = True

            return

        if len(presets) < 2:
            QMessageBox.information(
                self,
                tr("desktop.endfield.dialogNeedTwoPlansTitle"),
                tr("desktop.endfield.dialogNeedTwoPlansMsg"),
            )

            self._no_data = True

            return

        chars = get_characters()

        weps = get_weapons()

        eqs = get_equipments()

        rows = compare_presets_parallel(
            presets,
            characters=chars,
            weapons=weps,
            equipments=eqs,
            enemy_defense=enemy_defense,
            max_workers=self._workers,
        )

        get_session_operation_log().record(
            LogLevel.USER,
            "preset_compare",
            {"count": len(presets), "workers": self._workers},
        )

        header = QLabel(tr("desktop.endfield.dialogCompareHeader", count=len(presets), workers=self._workers))

        header.setFont(small_font)

        header.setStyleSheet(_HINT_COLOR)

        layout.addWidget(header)

        scroll = QScrollArea()

        scroll.setWidgetResizable(True)

        scroll.setFrameShape(QFrame.Shape.NoFrame)

        body = QWidget()

        body_layout = QVBoxLayout(body)

        body_layout.setContentsMargins(0, 0, 0, 0)

        body_layout.setSpacing(4)

        for idx, row in enumerate(rows, start=1):
            if row.error:
                text = tr(
                    "desktop.endfield.dialogCompareRowError",
                    idx=idx,
                    label=row.label,
                    error=row.error,
                )

                color = "#FF6B6B"

            else:
                text = tr(
                    "desktop.endfield.dialogCompareRowOk",
                    idx=idx,
                    label=row.label,
                    damage=f"{row.final_damage:.1f}",
                    summary=row.loadout_summary,
                )

                color = "#B8B8B8"

            lbl = QLabel(text)

            lbl.setFont(small_font)

            lbl.setStyleSheet(f"color: {color};")

            lbl.setWordWrap(True)

            body_layout.addWidget(lbl)

        body_layout.addStretch()

        scroll.setWidget(body)

        layout.addWidget(scroll, stretch=1)

        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)

        btn_box.rejected.connect(self.reject)

        layout.addWidget(btn_box)
