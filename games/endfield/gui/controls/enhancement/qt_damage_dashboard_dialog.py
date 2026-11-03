# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""伤害仪表盘弹窗：饼图（轮转伤害构成）+ 柱状图（乘区占比）。"""

from __future__ import annotations

from calc_framework.ui.i18n import tr
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from utils.optional_deps import matplotlib_install_hint

from games.endfield.gui.shared.damage_visualization import (
    build_damage_pie_figure,
    build_improvement_bar_figure,
    damage_breakdown_from_skill_map,
    is_matplotlib_available,
)

from .qt_dialogs_styles import _SEC_BTN_STYLE

__all__ = ["QtDamageDashboardDialog"]


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

            btn = QPushButton(tr("common.close"))

            btn.setFont(small_font)

            btn.setStyleSheet(_SEC_BTN_STYLE)

            btn.clicked.connect(_on_close)

            layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)

        except Exception as exc:
            QMessageBox.critical(self, tr("desktop.endfield.dialogChartFailed"), str(exc))

            layout.addWidget(QLabel(f"图表渲染失败: {exc}"))
