#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""手动次数开关轻量刷新测试。"""

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from gui_design.multi_skill_controls import on_manual_skill_counts_switch_changed


class TestManualSkillCountsSwitch(unittest.TestCase):
    def _app_stub(self, **extra: object) -> SimpleNamespace:
        base = dict(
            _confirm_refresh_signature=None,
            right_scroll=None,
            game_data=MagicMock(),
            big_font=MagicMock(),
            small_font=MagicMock(),
            _single_skill_preview_candidates=lambda: [],
            app=SimpleNamespace(after=lambda _ms, fn: fn()),
        )
        base.update(extra)
        return SimpleNamespace(**base)

    def test_switch_change_skips_full_confirm_refresh(self) -> None:
        loadout = MagicMock()
        loadout.calculation_mode = "single_hit"
        loadout.confirm_refresh_signature.return_value = ("single_hit", "sig")

        app = self._app_stub()

        with patch(
            "gui_design.loadout_state.read_loadout_from_app",
            return_value=loadout,
        ) as mock_read, patch(
            "gui_design.enhancement_controls.refresh_damage_snapshot",
        ) as mock_snap, patch(
            "gui_design.search_controls.refresh_search_estimate",
        ) as mock_est, patch(
            "gui_design.confirm_orchestrator.run_confirm_refresh",
        ) as mock_full:
            on_manual_skill_counts_switch_changed(app)  # type: ignore[arg-type]

        mock_read.assert_called_once_with(app, ensure_segment_rows=False)
        mock_snap.assert_called_once()
        mock_est.assert_called_once()
        mock_full.assert_not_called()
        self.assertEqual(app._confirm_refresh_signature, ("single_hit", "sig"))
        self.assertFalse(app._suppress_full_confirm_refresh)

    def test_multi_skill_mode_refreshes_right_column_only(self) -> None:
        loadout = MagicMock()
        loadout.calculation_mode = "multi_skill_search"
        loadout.confirm_refresh_signature.return_value = ("multi",)

        right_scroll = MagicMock()
        app = self._app_stub(right_scroll=right_scroll)

        with patch(
            "gui_design.loadout_state.read_loadout_from_app",
            return_value=loadout,
        ), patch(
            "gui_design.enhancement_controls.refresh_damage_snapshot",
        ), patch(
            "gui_design.search_controls.refresh_search_estimate",
        ), patch(
            "gui_design.display_request.build_display_request",
            return_value=MagicMock(),
        ), patch(
            "gui_design.display_view.refresh_right_column_from_request",
        ) as mock_right, patch(
            "gui_design.confirm_orchestrator.run_confirm_refresh",
        ) as mock_full:
            on_manual_skill_counts_switch_changed(app)  # type: ignore[arg-type]

        mock_right.assert_called_once()
        mock_full.assert_not_called()


if __name__ == "__main__":
    unittest.main()
