#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""干员下拉搜索（QCompleter 子串匹配，对齐 Web Autocomplete）。"""

from __future__ import annotations

from PySide6.QtCore import QStringListModel, Qt
from PySide6.QtWidgets import QComboBox, QCompleter


def filter_operator_names(names: list[str], query: str) -> list[str]:
    """按名称子串筛选（与 Web ``filter_operator_index`` 搜索语义一致）。"""
    needle = query.strip()
    if not needle:
        return list(names)
    return [name for name in names if needle in name]


def configure_operator_combobox(combo: QComboBox, names: list[str], *, preserve: str = "") -> None:
    """刷新干员列表并启用子串自动完成。"""
    combo.blockSignals(True)
    current = preserve or combo.currentText()
    combo.clear()
    if names:
        combo.addItems(names)

    completer = QCompleter(QStringListModel(names, combo), combo)
    completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
    completer.setFilterMode(Qt.MatchFlag.MatchContains)
    completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
    combo.setCompleter(completer)

    if current and current in names:
        combo.setCurrentText(current)
    elif current:
        combo.setEditText(current)
    combo.blockSignals(False)


__all__ = ["configure_operator_combobox", "filter_operator_names"]
