#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DamageCalculatorApp 轻量集成测试（构造主窗口并调用关键辅助方法）。"""

from __future__ import annotations

import unittest
from unittest.mock import patch

import pytest

from tests.gui_fixtures import ctk_available

pytestmark = pytest.mark.integration


class TestDamageCalculatorAppIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not ctk_available():
            raise unittest.SkipTest("需要可用的 CustomTkinter / Tcl")
        from data.loader import preload_game_data

        preload_game_data()

    def test_construct_app_and_invoke_helpers(self) -> None:
        with patch("utils.gui_window.apply_startup_maximized"):
            from gui_design.gui import DamageCalculatorApp

            app = DamageCalculatorApp()
            try:
                app.app.withdraw()
                counts = app._manual_multi_skill_counts()
                self.assertEqual(counts["战技"], 1)
                mode = app._current_calculation_mode()
                self.assertIn(mode, ("zone_snapshot", "single_hit", "single_skill_search", "multi_skill_search"))
                fixed = app._build_fixed_loadout_selection()
                self.assertEqual(fixed.fixed_count(), 0)
                self.assertIsNotNone(app.char_panel)
                self.assertIsNotNone(app.weapon_panel)
                from gui_design.confirm_orchestrator import confirm_signature_now

                sig = confirm_signature_now(app)
                self.assertIsInstance(sig, tuple)
            finally:
                app.app.destroy()

    def test_on_window_resize_no_crash(self) -> None:
        with patch("utils.gui_window.apply_startup_maximized"):
            from gui_design.gui import DamageCalculatorApp

            app = DamageCalculatorApp()
            try:
                app.app.withdraw()
                app._on_window_resize(type("E", (), {"widget": app.app, "width": 800, "height": 600})())
            finally:
                app.app.destroy()


if __name__ == "__main__":
    unittest.main()
