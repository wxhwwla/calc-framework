#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""PySide6 增强工具弹窗：计算历史 / 多方案对比 / 伤害仪表盘。"""

from __future__ import annotations

from pathlib import Path

from calc_framework.ui.i18n import tr
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from utils.operation_log import LogLevel, get_session_operation_log
from utils.optional_deps import matplotlib_install_hint

from games.endfield.data_loading.loader import get_characters, get_equipments, get_weapons
from games.endfield.gui.app.loadout_preset import (
    LoadoutPreset,
    import_presets_from_json_text,
)
from games.endfield.gui.controls.search.search_settings import resolve_parallel_workers
from games.endfield.gui.shared.calc_history import CalculationHistory
from games.endfield.gui.shared.damage_visualization import (
    build_damage_pie_figure,
    build_improvement_bar_figure,
    damage_breakdown_from_skill_map,
    is_matplotlib_available,
)
from games.endfield.gui.shared.preset_batch_compare import compare_presets_parallel

_SMALL_LABEL = "color: #CCCCCC;"

_HINT_COLOR = "color: #888888;"

_SEC_BTN_STYLE = """

    QPushButton {

        background-color: transparent; color: #D1D1D1;

        border: 1px solid #464646; border-radius: 6px; padding: 6px 16px;

    }

    QPushButton:hover { border-color: #2B6CB6; color: white; }

"""

_PRIMARY_BTN_STYLE = """

    QPushButton {

        background-color: #2B6CB6; color: white;

        border-radius: 6px; padding: 6px 16px; font-weight: bold;

    }

    QPushButton:hover { background-color: #3182CE; }

"""


# ═══════════════════════════════════════════════════════

#  1. 计算历史

# ═══════════════════════════════════════════════════════


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
        """初始化实例。"""

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


# ═══════════════════════════════════════════════════════

#  2. 多方案对比

# ═══════════════════════════════════════════════════════


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
        """初始化实例。"""


# ═══════════════════════════════════════════════════════

#  3. 伤害仪表盘

# ═══════════════════════════════════════════════════════


class QtDamageDashboardDialog(QDialog):
    """伤害仪表盘：饼图（轮转伤害构成）+ 柱状图（乘区占比）。"""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        big_font: QFont,
        small_font: QFont,
        snapshot=None,
    ) -> None:
        super().__init__(parent)

        self.setWindowTitle(tr("desktop.endfield.dialogDashboardTitle"))

        self.resize(960, 480)

        self.setMinimumSize(700, 350)

        self._big = big_font

        self._small = small_font

        layout = QVBoxLayout(self)

        layout.setContentsMargins(12, 12, 12, 12)

        if snapshot is None:
            QMessageBox.information(
                self,
                tr("common.noData"),
                tr("desktop.endfield.dialogDashboardNoDataMsg"),
            )

            layout.addWidget(QLabel(tr("common.noData")))

            return

        if not is_matplotlib_available():
            QMessageBox.warning(
                self,
                tr("desktop.endfield.dialogNeedMatplotlib"),
                tr("desktop.endfield.dialogInstallMatplotlibHint", hint=matplotlib_install_hint()),
            )

            layout.addWidget(QLabel(tr("desktop.endfield.dialogNeedMatplotlib")))

            return

        from games.endfield.calc.skills.segments import segment_display_label

        rotation_damage = dict(snapshot.segment_totals)

        pie_slices = damage_breakdown_from_skill_map(
            {segment_display_label(key): value for key, value in rotation_damage.items() if value > 0}
        )

        fig = build_damage_pie_figure(pie_slices, title=tr("desktop.endfield.dialogPieRotationTitle"))

        zone_items = tuple(sorted(snapshot.zone_share_percent.items(), key=lambda item: -item[1]))

        bar_fig = build_improvement_bar_figure(
            zone_items,
            title=tr("desktop.endfield.dialogBarZoneTitle"),
            ylabel=tr("desktop.endfield.dialogBarZoneYLabel"),
        )

        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg

            canvas_row = QHBoxLayout()

            canvas1 = FigureCanvasQTAgg(fig)

            canvas2 = FigureCanvasQTAgg(bar_fig)

            canvas_row.addWidget(canvas1, stretch=1)

            canvas_row.addWidget(canvas2, stretch=1)

            layout.addLayout(canvas_row, stretch=1)

            def _on_close() -> None:
                plt.close(fig)

                plt.close(bar_fig)

                self.accept()
                """on close。"""

            btn = QPushButton(tr("common.close"))

            btn.setFont(small_font)

            btn.setStyleSheet(_SEC_BTN_STYLE)

            btn.clicked.connect(_on_close)

            layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)

        except Exception as exc:
            QMessageBox.critical(self, tr("desktop.endfield.dialogChartFailed"), str(exc))

            layout.addWidget(QLabel(f"图表渲染失败: {exc}"))
        """初始化实例。"""
