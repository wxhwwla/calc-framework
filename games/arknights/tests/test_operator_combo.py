# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""干员搜索 helper 测试。"""

from __future__ import annotations

import sys
from collections.abc import Iterator

import pytest
from PySide6.QtWidgets import QApplication, QComboBox

from games.arknights.gui.operator_combo import configure_operator_combobox, filter_operator_names


@pytest.fixture(scope="module")
def qapp() -> Iterator[QApplication]:
    existing = QApplication.instance()
    app = existing if isinstance(existing, QApplication) else QApplication(sys.argv)
    yield app


class TestConfigureOperatorCombobox:
    def test_selects_first_operator_without_current(self, qapp: QApplication) -> None:
        combo = QComboBox()
        combo.setEditable(True)
        combo.setPlaceholderText("搜索干员...")

        configure_operator_combobox(combo, ["能天使", "阿米娅"])

        assert combo.currentIndex() == 0
        assert combo.currentText() == "能天使"

    def test_preserves_current_operator(self, qapp: QApplication) -> None:
        combo = QComboBox()
        combo.setEditable(True)
        combo.setPlaceholderText("搜索干员...")

        configure_operator_combobox(combo, ["能天使", "阿米娅"], preserve="阿米娅")

        assert combo.currentText() == "阿米娅"


class TestFilterOperatorNames:
    def test_empty_query_returns_all(self) -> None:
        names = ["能天使", "阿米娅", "12F"]
        assert filter_operator_names(names, "") == names

    def test_substring_match(self) -> None:
        names = ["能天使", "阿米娅", "12F"]
        assert filter_operator_names(names, "能") == ["能天使"]

    def test_no_match(self) -> None:
        assert filter_operator_names(["能天使"], "xyz") == []
