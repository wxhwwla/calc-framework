# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""QtAttributeColumns 嵌入式模式：三张表可分别放入共享外壳区域。"""

from __future__ import annotations

import unittest

from calc_framework.ui.calculator_shell import CalculatorPage
from games.endfield.gui.shared.display_view.qt_columns import QtAttributeColumns
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QTableWidget


class TestQtColumnsEmbedded(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not QApplication.instance():
            cls._app = QApplication([])
        cls._font = QFont()

    def _columns(self, *, embedded: bool) -> QtAttributeColumns:
        return QtAttributeColumns(big_font=self._font, small_font=self._font, embedded=embedded)

    def test_embedded_mode_does_not_build_three_column_layout(self) -> None:
        columns = self._columns(embedded=True)

        self.assertIsNone(columns.layout())
        self.assertEqual(len(columns.findChildren(QTableWidget)), 3)

    def test_embedded_tables_can_be_placed_in_separate_zones(self) -> None:
        columns = self._columns(embedded=True)
        page = CalculatorPage(
            top_left_title="角色",
            top_right_title="武器",
            bottom_left_title="基础",
            bottom_right_title="加成",
        )

        page.zone("bottom_left").add_widget(columns.char_table)
        page.zone("bottom_right").add_widget(columns.weapon_table)
        page.zone("top_left").add_widget(columns.zone_table)

        self.assertIs(columns.char_table.parent(), page.zone("bottom_left"))
        self.assertIs(columns.weapon_table.parent(), page.zone("bottom_right"))
        self.assertIs(columns.zone_table.parent(), page.zone("top_left"))

    def test_default_mode_keeps_all_tables_in_one_row(self) -> None:
        columns = self._columns(embedded=False)
        layout = columns.layout()

        self.assertIsNotNone(layout)
        assert layout is not None
        self.assertEqual(layout.count(), 3)
        self.assertEqual(len(columns.findChildren(QTableWidget)), 3)


if __name__ == "__main__":
    unittest.main()
