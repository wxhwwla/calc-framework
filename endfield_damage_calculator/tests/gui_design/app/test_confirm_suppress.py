#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""确认刷新抑制（手动次数开关）测试。"""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from gui_design.app.confirm_orchestrator import schedule_confirm


class TestConfirmSuppress(unittest.TestCase):
    def test_schedule_confirm_skipped_when_suppressed(self) -> None:
        app = SimpleNamespace(
            _suppress_full_confirm_refresh=True,
            _confirm_after_id=None,
            app=SimpleNamespace(after_idle=lambda fn: "id"),
        )
        with patch("gui_design.app.confirm_orchestrator.handle_confirm") as mock_handle:
            schedule_confirm(app)  # type: ignore[arg-type]
        mock_handle.assert_not_called()


if __name__ == "__main__":
    unittest.main()
