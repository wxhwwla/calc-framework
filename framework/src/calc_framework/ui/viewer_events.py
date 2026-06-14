# SPDX-License-Identifier: AGPL-3.0
"""CalcPackViewer 事件处理 Mixin。"""

from __future__ import annotations

from typing import Any

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QFileDialog

from .i18n import tr
from .viewer_help_content import build_viewer_help
from .viewer_plugin_manager import PluginManagerDialog


class CalcPackViewerEventMixin:
    """CalcPackViewer 事件处理 Mixin。"""

    # 被 Mixin 依赖的属性（由 CalcPackViewer 提供）：
    # _theme_manager, _status_label, _splitter, _compute_sheet,
    # _entity_selectors, _level_spin, _asset_temp_dir

    def _show_help(self) -> None:
        from utils.gui.help_dialog import HelpDialog

        dialog = HelpDialog(build_viewer_help, self, title=tr("desktop.viewer.helpDialogTitle"))  # type: ignore[arg-type]
        dialog.exec()

    def _on_theme_switched(self, action: QAction) -> None:
        key = action.data()
        if key:
            stylesheet = self._theme_manager.switch(key)
            self.setStyleSheet(stylesheet)
            theme = self._theme_manager.get_theme(key)
            if theme:
                self._theme_manager.apply_font(theme, self)
            self._status_label.setText(tr("desktop.viewer.themeSwitched", name=theme.get("name", key)))

    def _toggle_left_panel(self) -> None:
        if self._splitter is None:
            return
        sizes = self._splitter.sizes()
        if sizes[0] > 0:
            self._splitter.setSizes([0, sizes[0] + sizes[1] + sizes[2], 0])
        else:
            self._splitter.setSizes([220, max(400, sizes[1] - 220), max(100, sizes[2])])

    def _toggle_right_panel(self) -> None:
        if self._splitter is None:
            return
        sizes = self._splitter.sizes()
        if sizes[2] > 0:
            self._splitter.setSizes([sizes[0], sizes[0] + sizes[1] + sizes[2], 0])
        else:
            self._splitter.setSizes([max(100, sizes[0]), max(400, sizes[1] - 200), 200])

    def _show_plugin_manager_dialog(self) -> None:
        dialog = PluginManagerDialog(self, self._status_label.setText)  # type: ignore[arg-type]
        dialog.exec()

    def _open_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,  # type: ignore[arg-type] — mixin, runtime is QMainWindow
            tr("desktop.viewer.menuOpenCalcpack"),
            "",  # type: ignore[arg-type]
            "CalcPack (*.calcpack);;ZIP (*.zip);;All Files (*)",
        )
        if path:
            self.load_calcpack(path)

    def _on_entity_changed(self) -> None:
        """当用户切换实体或更改等级时重新求值。"""
        if self._compute_sheet is None:
            return

        context = self._build_current_context()
        self._compute_sheet._base_context = context
        self._compute_sheet.evaluate()

        selected = []
        for src, combo in self._entity_selectors.items():
            if combo.currentIndex() >= 0:
                selected.append(f"{src}={combo.currentText()}")
        lv = self._level_spin.value() if self._level_spin else 90
        self._status_label.setText(f"已求值 — {', '.join(selected) if selected else '自定义输入'} Lv.{lv}")

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if self._splitter is None:
            return
        width = event.size().width()
        if width < 800:
            self._splitter.setSizes([0, width, 0])
        elif width < 1100:
            sizes = self._splitter.sizes()
            if sizes[0] > 180:
                self._splitter.setSizes([180, width - 360, 180])
        elif self._splitter.sizes()[0] == 0 and self._splitter.sizes()[2] == 0:
            self._splitter.setSizes([220, width - 420, 200])

    def closeEvent(self, event: Any) -> None:  # noqa: N802
        if self._asset_temp_dir:
            self._asset_temp_dir.cleanup()
            self._asset_temp_dir = None
        super().closeEvent(event)
