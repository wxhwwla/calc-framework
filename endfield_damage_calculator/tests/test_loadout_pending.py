#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""配装待确认：展示签名与按钮状态。"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from gui_design.confirm_refresh import build_display_pending_signature
from gui_design.loadout_pending import (
    CONFIRM_BTN_TEXT_DEFAULT,
    CONFIRM_BTN_TEXT_PENDING,
    capture_confirmed_display_signature,
    is_loadout_pending_confirm,
    mark_loadout_pending,
    sync_confirm_button_pending_state,
)


class TestDisplayPendingSignature(unittest.TestCase):
    def test_excludes_search_scope_fields(self) -> None:
        base = dict(
            calculation_mode="zone_snapshot",
            char_name="A",
            char_level=90,
            weapon_name="W",
            weapon_level=90,
            trust_level=0,
            skill_levels=(1, 0, 0),
            weapon_specials=("", 1, "", 1, "", 0, "", 1, 0, "", 1, 0),
            use_manual_multi_skill_counts=False,
            multi_skill_manual_counts={},
            damage_component_mode="skill_and_abnormal",
            use_expected_crit=False,
            include_conditional_equipment_crit=False,
            extra_crit_rate=0.0,
            extra_crit_damage=0.0,
            physical_abnormal_counts={},
            spell_abnormal_counts={},
            enemy_defense=100.0,
        )
        sig_a = build_display_pending_signature(**base)
        self.assertEqual(sig_a, build_display_pending_signature(**base))

    def test_level_change_changes_signature(self) -> None:
        common = dict(
            calculation_mode="zone_snapshot",
            char_name="A",
            char_level=90,
            weapon_name="W",
            weapon_level=90,
            trust_level=0,
            skill_levels=(1, 0, 0),
            weapon_specials=("", 1, "", 1, "", 0, "", 1, 0, "", 1, 0),
            use_manual_multi_skill_counts=False,
            multi_skill_manual_counts={},
            damage_component_mode="skill_and_abnormal",
            use_expected_crit=False,
            include_conditional_equipment_crit=False,
            extra_crit_rate=0.0,
            extra_crit_damage=0.0,
            physical_abnormal_counts={},
            spell_abnormal_counts={},
            enemy_defense=100.0,
        )
        sig_90 = build_display_pending_signature(**common)
        common["char_level"] = 80
        sig_80 = build_display_pending_signature(**common)
        self.assertNotEqual(sig_90, sig_80)


class TestLoadoutPendingUi(unittest.TestCase):
    def _make_app(self, *, confirmed: tuple, current: tuple) -> MagicMock:
        app = MagicMock()
        app._confirmed_display_signature = confirmed
        app._pending_ui_after_id = None
        app._confirm_button_default_styles = {}
        app.main_confirm_btn = MagicMock()
        app.confirm_btn = MagicMock()
        app.main_confirm_btn.cget.side_effect = lambda key: (
            "#1f538d" if key == "fg_color" else "#14375e"
        )
        app.confirm_btn.cget.side_effect = lambda key: (
            "#1f538d" if key == "fg_color" else "#14375e"
        )

        def _read_loadout(*_args, **_kwargs):
            state = MagicMock()
            state.display_pending_signature.return_value = current
            return state

        return app

    def test_pending_when_signatures_differ(self) -> None:
        app = self._make_app(confirmed=("a",), current=("b",))
        with patch(
            "gui_design.loadout_pending.read_loadout_from_app",
            return_value=MagicMock(display_pending_signature=lambda: ("b",)),
        ):
            self.assertTrue(is_loadout_pending_confirm(app))

    def test_not_pending_when_signatures_match(self) -> None:
        app = self._make_app(confirmed=("same",), current=("same",))
        with patch(
            "gui_design.loadout_pending.read_loadout_from_app",
            return_value=MagicMock(display_pending_signature=lambda: ("same",)),
        ):
            self.assertFalse(is_loadout_pending_confirm(app))

    def test_sync_buttons_show_pending_text(self) -> None:
        app = self._make_app(confirmed=("a",), current=("b",))
        with patch(
            "gui_design.loadout_pending.read_loadout_from_app",
            return_value=MagicMock(display_pending_signature=lambda: ("b",)),
        ):
            sync_confirm_button_pending_state(app)
        app.main_confirm_btn.configure.assert_called()
        app.confirm_btn.configure.assert_called()
        pending_call = app.main_confirm_btn.configure.call_args_list[-1]
        self.assertEqual(pending_call.kwargs.get("text"), CONFIRM_BTN_TEXT_PENDING)

    def test_capture_confirmed_clears_pending_style(self) -> None:
        app = self._make_app(confirmed=("old",), current=("old",))
        with patch(
            "gui_design.loadout_pending.read_loadout_from_app",
            return_value=MagicMock(display_pending_signature=lambda: ("old",)),
        ):
            capture_confirmed_display_signature(app)
        self.assertEqual(app._confirmed_display_signature, ("old",))
        texts = [
            call.kwargs.get("text")
            for call in app.main_confirm_btn.configure.call_args_list
            if "text" in call.kwargs
        ]
        self.assertIn(CONFIRM_BTN_TEXT_DEFAULT, texts)


if __name__ == "__main__":
    unittest.main()
