#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""主界面列布局契约测试。"""

import unittest

from gui_design.gui import APP_COLUMN_WEIGHTS


class TestGuiLayoutContract(unittest.TestCase):
    def test_main_grid_column_weights(self):
        """主界面应为 6 列：配装区固定宽，属性列均分，乘区占剩余空间。"""
        self.assertEqual(APP_COLUMN_WEIGHTS, (0, 0, 1, 1, 1, 5))


if __name__ == "__main__":
    unittest.main()
