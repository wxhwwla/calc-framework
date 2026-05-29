#!/usr/bin/env python3
"""主窗口启动尺寸测试。"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from utils.gui_window import apply_startup_maximized


class TestGuiWindow(unittest.TestCase):
    def test_apply_startup_maximized_schedules_idle_callback(self) -> None:
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

    @patch("utils.gui_window._try_zoomed_state", return_value=False)
    @patch("utils.gui_window._try_zoomed_attribute", return_value=True)
    def test_falls_back_to_zoomed_attribute(
        self, _mock_attr: MagicMock, _mock_zoom: MagicMock
    ) -> None:
        window = MagicMock()
        apply_startup_maximized(window)
        callback = window.after_idle.call_args[0][0]
        callback()

    @patch("utils.gui_window._try_zoomed_state", return_value=False)
    @patch("utils.gui_window._try_zoomed_attribute", return_value=False)
    @patch("utils.gui_window._geometry_fill_screen")
    def test_falls_back_to_geometry(
        self, mock_geom: MagicMock, _mock_attr: MagicMock, _mock_zoom: MagicMock
    ) -> None:
        window = MagicMock()
        apply_startup_maximized(window)
        callback = window.after_idle.call_args[0][0]
        callback()
        mock_geom.assert_called_once_with(window)

    @patch("utils.gui_window._try_zoomed_state", side_effect=Exception)
    def test_try_zoomed_state_returns_false_on_exception(self, _mock: MagicMock) -> None:
        window = MagicMock()
        result = apply_startup_maximized(window)
        self.assertIsNone(result)

    def test_apply_directly_when_after_idle_fails(self) -> None:
        window = MagicMock()
        window.after_idle.side_effect = Exception("no tk")
        apply_startup_maximized(window)

    @patch("utils.gui_window._try_zoomed_state", return_value=False)
    @patch("utils.gui_window._try_zoomed_attribute", side_effect=Exception)
    def test_try_zoomed_attribute_propagates_exception(
        self, _mock_attr: MagicMock, _mock_zoom: MagicMock
    ) -> None:
        window = MagicMock()
        window.winfo_screenwidth.return_value = 1920
        window.winfo_screenheight.return_value = 1080
        apply_startup_maximized(window)
        callback = window.after_idle.call_args[0][0]
        with self.assertRaises(Exception):
            callback()

    @patch("utils.gui_window._try_zoomed_state", return_value=False)
    @patch("utils.gui_window._try_zoomed_attribute", return_value=False)
    def test_geometry_fill_screen_small_display(self, _mock_attr: MagicMock, _mock_zoom: MagicMock) -> None:
        window = MagicMock()
        window.winfo_screenwidth.return_value = 320
        window.winfo_screenheight.return_value = 240
        apply_startup_maximized(window)
        callback = window.after_idle.call_args[0][0]
        callback()
        window.geometry.assert_not_called()


if __name__ == "__main__":
    unittest.main()
