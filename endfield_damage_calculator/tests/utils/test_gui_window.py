#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""主窗口启动尺寸测试。"""

import unittest
from unittest.mock import MagicMock, patch

from utils.gui_window import apply_startup_maximized


class TestGuiWindow(unittest.TestCase):
    def test_apply_startup_maximized_schedules_idle_callback(self):
        window = MagicMock()
        apply_startup_maximized(window)
        window.after_idle.assert_called_once()

    @patch("utils.gui_window._try_zoomed_state", return_value=True)
    def test_idle_callback_uses_zoomed_when_available(self, _mock_zoom: MagicMock) -> None:
        window = MagicMock()
        apply_startup_maximized(window)
        callback = window.after_idle.call_args[0][0]
        callback()
        window.update_idletasks.assert_called()


if __name__ == "__main__":
    unittest.main()
