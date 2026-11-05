# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""CalcPackViewer 事件处理 Mixin。"""

from __future__ import annotations

from typing import Any, cast

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QFileDialog, QWidget

from ..config.entity_meta import (
    EntityMetaError,
    normalize_entity_input_rules,
    rule_matches,
)
from ..logging import get_logger
from .i18n import tr
from .viewer_help_content import build_viewer_help
from .viewer_plugin_manager import PluginManagerDialog

logger = get_logger(__name__)


class CalcPackViewerEventMixin:
    """CalcPackViewer 事件处理 Mixin。"""

    # Mixin 属性占位 — 由 CalcPackViewer 提供（Pylance 类型识别）
    _theme_manager: Any
    _status_label: Any
    _compute_sheet: Any
    _entity_selectors: Any
    _level_spin: Any
    _asset_temp_dir: Any
    _meta: Any
    _layout: Any
    _entity_data: Any

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
        """切换实体或等级时只标记待确认，点击确认后才求值。"""
        if self._compute_sheet is None:
            return
        self._mark_pending()

    def _displayed_input_paths(self) -> list[str]:
        """返回 layout 中声明的输入控件路径（用于条件禁用校验）。"""
        if not self._layout:
            return []
        paths: list[str] = []
        for section in self._layout.sections:
            if section.type != "inputs":
                continue
            for path in section.variables:
                if path not in paths:
                    paths.append(path)
        return paths

    def _apply_entity_input_rules(self) -> None:
        """按 ``meta.entity_input_rules`` 启用/禁用当前实体无关的输入。

        字段缺失或为空的实体视为「未知」，其相关输入保持可编辑，
        让玩家自行决定，而不是替玩家做假设。
        """
        sheet = self._compute_sheet
        if sheet is None:
            return
        paths = self._displayed_input_paths()
        try:
            rules = normalize_entity_input_rules(
                self._meta.get("entity_input_rules"),
                data_files=self._entity_source_records(),
                user_input_paths=paths,
            )
        except EntityMetaError as exc:
            logger.warning("entity_input_rules 配置无效，已忽略条件禁用: %s", exc)
            rules = []

        selected = self._selected_entity_names()
        disabled: dict[str, str] = {}
        for rule in rules:
            record = self._entity_data.get(rule["source"], {}).get(selected.get(rule["source"], ""))
            if not isinstance(record, dict) or not rule_matches(rule, record):
                continue
            reason = str(rule.get("reason") or "")
            for path in rule["disable"]:
                disabled.setdefault(path, reason)

        for path in paths:
            if path in disabled:
                sheet.set_input_enabled(path, False, reason=disabled[path])
            else:
                sheet.set_input_enabled(path, True)

    def closeEvent(self, event: Any) -> None:  # noqa: N802
        if self._asset_temp_dir:
            self._asset_temp_dir.cleanup()
            self._asset_temp_dir = None
        super().closeEvent(event)
