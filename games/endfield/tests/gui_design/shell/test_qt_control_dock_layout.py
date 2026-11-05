# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""QtControlDock 列拆分：搜索列/多技能列可放入共享外壳区域。

操作按钮由顶部工具条承载，因此操作列不再占用高级页可见布局，但仍作为
dock 的子控件保留（既有信号/回调测试依赖这些按钮实例）。
"""

from __future__ import annotations

import unittest

from calc_framework.ui.calculator_shell import CalculatorPage
from games.endfield.gui.shell.qt_control_dock import QtControlDock
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QWidget


class TestQtControlDockLayout(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not QApplication.instance():
            cls._app = QApplication([])
        cls._font = QFont()

    def _dock(self) -> QtControlDock:
        return QtControlDock(big_font=self._font, small_font=self._font)

    def test_dock_exposes_search_and_multi_columns(self) -> None:
        dock = self._dock()

        self.assertIsInstance(dock._col_search, QWidget)
        self.assertIsInstance(dock._col_multi, QWidget)
        self.assertIsInstance(dock._col_actions, QWidget)

    def test_action_column_stays_available_but_out_of_dock_layout(self) -> None:
        dock = self._dock()
        layout = dock.layout()

        self.assertIsNotNone(layout)
        assert layout is not None
        self.assertEqual(layout.indexOf(dock._col_actions), -1)
        self.assertGreaterEqual(layout.indexOf(dock._col_search), 0)
        self.assertGreaterEqual(layout.indexOf(dock._col_multi), 0)

    def test_columns_and_enemy_panel_can_move_into_page_zones(self) -> None:
        dock = self._dock()
        page = CalculatorPage(
            top_left_title="敌人",
            top_right_title="技能",
            bottom_left_title="乘区",
            bottom_right_title="总伤",
        )

        page.zone("top_left").add_widget(dock._enemy_panel)
        page.zone("top_right").add_widget(dock._col_multi)
        page.zone("bottom_left").add_widget(dock._col_search)

        self.assertIs(dock._enemy_panel.parent(), page.zone("top_left"))
        self.assertIs(dock._col_multi.parent(), page.zone("top_right"))
        self.assertIs(dock._col_search.parent(), page.zone("bottom_left"))

    def test_more_settings_visibility_still_tracks_toggle(self) -> None:
        dock = self._dock()

        self.assertFalse(dock._more_settings_body.isVisibleTo(dock))
        dock._more_settings_btn.click()
        self.assertTrue(dock._more_settings_body.isVisibleTo(dock))


if __name__ == "__main__":
    unittest.main()
