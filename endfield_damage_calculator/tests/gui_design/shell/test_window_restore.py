#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""窗口最小化/恢复时的布局与确认刷新防抖测试。"""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from gui_design.app.confirm_orchestrator import (
    WINDOW_RESTORE_SETTLE_MS,
    handle_confirm,
    schedule_confirm,
)
from gui_design.layout.gui_layout import control_dock_layout_needs_update


class TestControlDockLayoutNeedsUpdate(unittest.TestCase):
    def test_same_width_and_compact_skips_relayout(self) -> None:
        self.assertFalse(
            control_dock_layout_needs_update(
                1600,
                last_width=1600,
                last_compact=False,
            )
        )

    def test_width_change_triggers_relayout(self) -> None:
        self.assertTrue(
            control_dock_layout_needs_update(
                1200,
                last_width=1600,
                last_compact=False,
            )
        )

    def test_compact_mode_change_triggers_relayout(self) -> None:
        self.assertTrue(
            control_dock_layout_needs_update(
                1400,
                last_width=1600,
                last_compact=False,
            )
        )


class TestConfirmRestoreDefer(unittest.TestCase):
    def test_schedule_confirm_defers_while_restore_settling(self) -> None:
        after_calls: list[tuple[int, object]] = []

        def fake_after(ms: int, fn: object) -> str:
            after_calls.append((ms, fn))
            return "after-id"

        app = SimpleNamespace(
            _suppress_full_confirm_refresh=False,
            _confirm_after_id=None,
            _confirm_refresh_signature=None,
            _restore_settling=True,
            _current_calculation_mode=lambda: "zone_snapshot",
            app=SimpleNamespace(
                state=lambda: "normal",
                after=fake_after,
                after_idle=lambda fn: fake_after(0, fn),
            ),
        )

        with patch("gui_design.app.confirm_orchestrator.run_confirm_refresh") as mock_run:
            with patch(
                "gui_design.app.confirm_orchestrator.confirm_signature_now",
                return_value=("sig",),
            ):
                with patch("gui_design.app.confirm_orchestrator.get_session_operation_log"):
                    schedule_confirm(app)  # type: ignore[arg-type]

                self.assertEqual(len(after_calls), 1)
                self.assertEqual(after_calls[0][0], 0)
                mock_run.assert_not_called()

                after_calls[0][1]()  # type: ignore[operator]
                self.assertEqual(len(after_calls), 2)
                self.assertEqual(after_calls[1][0], WINDOW_RESTORE_SETTLE_MS)
                mock_run.assert_not_called()

                app._restore_settling = False
                after_calls[1][1]()  # type: ignore[operator]
                mock_run.assert_called_once()

    def test_handle_confirm_reschedules_when_restore_settling(self) -> None:
        app = SimpleNamespace(
            _suppress_full_confirm_refresh=False,
            _confirm_after_id=None,
            _restore_settling=True,
            _confirm_refresh_signature=("sig",),
            app=SimpleNamespace(
                state=lambda: "normal",
                after=lambda _ms, fn: fn() or "id",
                after_idle=lambda fn: fn(),
            ),
        )

        with patch("gui_design.app.confirm_orchestrator.schedule_confirm") as mock_schedule:
            handle_confirm(app, force=False)  # type: ignore[arg-type]

        mock_schedule.assert_called_once_with(app)


if __name__ == "__main__":
    unittest.main()
