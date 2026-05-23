#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""主界面列布局契约测试。"""

import unittest

from gui_design.gui_layout import (
    APP_COLUMN_WEIGHTS,
    CHAR_ATTR_COLUMN,
    CHAR_COLUMN,
    CONTROL_DOCK_COLUMNSPAN,
    CONTROL_DOCK_ROW,
    MAIN_CONTENT_ROW,
    WEAPON_ATTR_COLUMN,
    WEAPON_COLUMN,
    ZONE_COLUMN,
)


class TestGuiLayoutContract(unittest.TestCase):
    def test_main_grid_five_columns_with_bottom_control_dock(self):
        """上排五列 + 底栏横跨左侧四列，乘区通高。"""
        self.assertEqual(APP_COLUMN_WEIGHTS, (0, 0, 1, 1, 5))
        self.assertEqual(CHAR_COLUMN, 0)
        self.assertEqual(WEAPON_COLUMN, 1)
        self.assertEqual(CHAR_ATTR_COLUMN, 2)
        self.assertEqual(WEAPON_ATTR_COLUMN, 3)
        self.assertEqual(ZONE_COLUMN, 4)
        self.assertEqual(CONTROL_DOCK_ROW, 1)
        self.assertEqual(MAIN_CONTENT_ROW, 0)
        self.assertEqual(CONTROL_DOCK_COLUMNSPAN, 4)


if __name__ == "__main__":
    unittest.main()
