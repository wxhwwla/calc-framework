# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""CalcPackViewer 事件处理 Mixin。"""

from __future__ import annotations

from typing import Any, cast

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QFileDialog, QWidget

from .i18n import tr
from .viewer_help_content import build_viewer_help
from .viewer_plugin_manager import PluginManagerDialog


class CalcPackViewerEventMixin:
    """CalcPackViewer 事件处理 Mixin。"""

    # Mixin 属性占位 — 由 CalcPackViewer 提供（Pylance 类型识别）
    _theme_manager: Any
    _status_label: Any
    _splitter: Any
    _compute_sheet: Any
    _entity_selectors: Any
    _level_spin: Any
    _asset_temp_dir: Any

    def _show_help(self) -> None:
        """显示内置帮助对话框（F1）。"""
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
                from ._qt_backend import apply_font

                apply_font(theme, cast(QWidget, self))
            theme_name = theme.get("name", key) if theme else key
            self._status_label.setText(tr("desktop.viewer.themeSwitched", name=theme_name))

    def _toggle_left_panel(self) -> None:
        """切换左侧栏的显示/隐藏。"""
        if self._splitter is None:
            return
        sizes = self._splitter.sizes()
        if sizes[0] > 0:
            self._splitter.setSizes([0, sizes[0] + sizes[1] + sizes[2], 0])
        else:
            self._splitter.setSizes([220, max(400, sizes[1] - 220), max(100, sizes[2])])

    def _toggle_right_panel(self) -> None:
        """切换右侧栏的显示/隐藏。"""
        if self._splitter is None:
            return
        sizes = self._splitter.sizes()
        if sizes[2] > 0:
            self._splitter.setSizes([sizes[0], sizes[0] + sizes[1] + sizes[2], 0])
        else:
            self._splitter.setSizes([max(100, sizes[0]), max(400, sizes[1] - 200), 200])

    def _show_plugin_manager_dialog(self) -> None:
        """显示插件管理器对话框。"""
        dialog = PluginManagerDialog(self, self._status_label.setText)  # type: ignore[arg-type]
        dialog.exec()

    def _open_file(self) -> None:
        """打开文件选择对话框加载 .calcpack。"""
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

        from .viewer_evaluator import build_entity_status_text

        selected: dict[str, str] = {}
        for src, combo in self._entity_selectors.items():
            if combo.currentIndex() >= 0:
                selected[src] = combo.currentText()
        lv = self._level_spin.value() if self._level_spin else 90
        self._status_label.setText(build_entity_status_text(selected, selected, lv))

    def resizeEvent(self, event: Any) -> None:  # noqa: N802
        """窗口大小变化时自动调整侧栏布局。"""
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
