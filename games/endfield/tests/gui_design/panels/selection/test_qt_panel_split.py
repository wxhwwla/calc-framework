# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""P2-07：``QtSelectionPanel`` 拆分后的结构与级联行为门禁。"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import pytest

_PANEL_MODULES = (
    "games.endfield.gui.panels.selection.qt_panel",
    "games.endfield.gui.panels.selection.qt_panel_build_mixin",
    "games.endfield.gui.panels.selection.qt_panel_events_mixin",
)


def _line_count(module_name: str) -> int:
    module = importlib.import_module(module_name)
    module_file = module.__file__
    assert module_file is not None
    return len(Path(module_file).read_text(encoding="utf-8").splitlines())


@pytest.fixture(scope="module", autouse=True)
def qapp():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app


@pytest.mark.parametrize("module_name", _PANEL_MODULES)
def test_panel_module_stays_within_target(module_name: str) -> None:
    assert _line_count(module_name) <= 400


def test_panel_inherits_split_mixins() -> None:
    from games.endfield.gui.panels.selection.qt_panel import QtSelectionPanel
    from games.endfield.gui.panels.selection.qt_panel_build_mixin import QtPanelBuildMixin
    from games.endfield.gui.panels.selection.qt_panel_events_mixin import QtPanelEventsMixin

    assert issubclass(QtSelectionPanel, QtPanelBuildMixin)
    assert issubclass(QtSelectionPanel, QtPanelEventsMixin)


def _data() -> list[dict[str, Any]]:
    return [
        {"名称": "A", "类型": "先锋", "星级": 4, "等级": [1, 2, 3]},
        {"名称": "B", "类型": "先锋", "星级": 5, "等级": [1, 2]},
        {"名称": "C", "类型": "术师", "星级": 5, "等级": [1, 2, 3, 4]},
    ]


def test_panel_cascade_and_level_presets(qapp) -> None:
    from games.endfield.gui.panels.selection.qt_panel import QtSelectionPanel
    from PySide6.QtGui import QFont

    panel = QtSelectionPanel(_data(), QFont())

    assert panel.select_by_name("B") is True
    assert panel.get_selected_data() is not None
    assert panel.get_selected_data()["名称"] == "B"
    assert panel.type_combo.currentText() == "先锋"
    assert panel.star_combo.currentText() == "5"

    panel._apply_level_preset(99)
    assert panel.level_slider.value() == 2
    assert panel.level_label_widget.text() == "2"

    panel._apply_level_preset(0)
    assert panel.level_slider.value() == 1
    assert panel.level_label_widget.text() == "1"


def test_panel_update_data_list_keeps_cascade_consistent(qapp) -> None:
    from games.endfield.gui.panels.selection.qt_panel import QtSelectionPanel
    from PySide6.QtGui import QFont

    panel = QtSelectionPanel(_data(), QFont())
    panel.update_data_list(
        [
            {"名称": "D", "类型": "近卫", "星级": 6, "等级": [1, 2, 3]},
        ]
    )

    assert panel.select_by_name("D") is True
    assert panel.type_combo.currentText() == "近卫"
    assert panel.get_level() == 1
