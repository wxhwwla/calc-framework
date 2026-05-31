# SPDX-License-Identifier: AGPL-3.0
from __future__ import annotations

from unittest.mock import MagicMock, patch

from utils.gui_window import (
    _geometry_fill_screen,
    _try_zoomed_attribute,
    _try_zoomed_state,
    apply_startup_maximized,
)


class TestTryZoomedState:
    def test_success(self) -> None:
        win = MagicMock()
        assert _try_zoomed_state(win) is True
        win.state.assert_called_once_with("zoomed")

    def test_failure(self) -> None:
        win = MagicMock()
        win.state.side_effect = Exception("no zoom")
        assert _try_zoomed_state(win) is False


class TestTryZoomedAttribute:
    def test_success(self) -> None:
        win = MagicMock()
        assert _try_zoomed_attribute(win) is True
        win.attributes.assert_called_once_with("-zoomed", True)

    def test_failure(self) -> None:
        win = MagicMock()
        win.attributes.side_effect = Exception("no attr")
        assert _try_zoomed_attribute(win) is False


class TestGeometryFillScreen:
    def test_normal_screen(self) -> None:
        win = MagicMock()
        win.winfo_screenwidth.return_value = 1920
        win.winfo_screenheight.return_value = 1080
        _geometry_fill_screen(win)
        args, _ = win.geometry.call_args
        assert "1920" in args[0]

    def test_small_screen_skips(self) -> None:
        win = MagicMock()
        win.winfo_screenwidth.return_value = 320
        win.winfo_screenheight.return_value = 240
        _geometry_fill_screen(win)
        win.geometry.assert_not_called()

    def test_exception_does_not_crash(self) -> None:
        win = MagicMock()
        win.winfo_screenwidth.side_effect = Exception("no screen")
        _geometry_fill_screen(win)


class TestApplyStartupMaximized:
    def test_calls_internal(self) -> None:
        win = MagicMock()

        def side_effect(fn):
            fn()

        win.after_idle.side_effect = side_effect
        apply_startup_maximized(win)
        win.after_idle.assert_called_once()

    def test_after_idle_exception(self) -> None:
        win = MagicMock()
        win.after_idle.side_effect = Exception("no after_idle")
        apply_startup_maximized(win)
