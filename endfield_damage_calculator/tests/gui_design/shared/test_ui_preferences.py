#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ui_preferences 偏好读取与启动页策略测试。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from gui_design.shared.ui_preferences import (
    PAGE_ADVANCED,
    PAGE_MAIN,
    STARTUP_MODE_ALWAYS_MAIN,
    STARTUP_MODE_REMEMBER_LAST,
    load_ui_preferences,
    record_char_advanced_expanded,
    record_weapon_advanced_expanded,
    record_last_page,
    resolve_startup_page,
    save_ui_preferences,
)


class TestUiPreferences(unittest.TestCase):
    def test_load_defaults_when_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            prefs = load_ui_preferences(base_dir=Path(tmp))
        self.assertEqual(prefs["startup_page_mode"], STARTUP_MODE_ALWAYS_MAIN)
        self.assertEqual(prefs["last_page"], PAGE_MAIN)
        self.assertTrue(prefs["char_advanced_expanded"])
        self.assertTrue(prefs["weapon_advanced_expanded"])

    def test_resolve_startup_page_by_mode(self) -> None:
        remember = {
            "startup_page_mode": STARTUP_MODE_REMEMBER_LAST,
            "last_page": PAGE_ADVANCED,
        }
        always = {
            "startup_page_mode": STARTUP_MODE_ALWAYS_MAIN,
            "last_page": PAGE_ADVANCED,
        }
        self.assertEqual(resolve_startup_page(remember), PAGE_ADVANCED)
        self.assertEqual(resolve_startup_page(always), PAGE_MAIN)

    def test_save_and_reload_preferences(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            save_ui_preferences(
                {
                    "startup_page_mode": STARTUP_MODE_REMEMBER_LAST,
                    "last_page": PAGE_ADVANCED,
                },
                base_dir=base,
            )
            loaded = load_ui_preferences(base_dir=base)
        self.assertEqual(loaded["startup_page_mode"], STARTUP_MODE_REMEMBER_LAST)
        self.assertEqual(loaded["last_page"], PAGE_ADVANCED)
        self.assertTrue(loaded["char_advanced_expanded"])
        self.assertTrue(loaded["weapon_advanced_expanded"])

    def test_save_and_reload_weapon_skill_expanded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            save_ui_preferences(
                {
                    "startup_page_mode": STARTUP_MODE_ALWAYS_MAIN,
                    "last_page": PAGE_MAIN,
                    "weapon_advanced_expanded": False,
                },
                base_dir=base,
            )
            loaded = load_ui_preferences(base_dir=base)
        self.assertFalse(loaded["weapon_advanced_expanded"])

    def test_save_and_reload_char_skill_levels_expanded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            save_ui_preferences(
                {
                    "startup_page_mode": STARTUP_MODE_ALWAYS_MAIN,
                    "last_page": PAGE_MAIN,
                    "char_advanced_expanded": False,
                },
                base_dir=base,
            )
            loaded = load_ui_preferences(base_dir=base)
        self.assertFalse(loaded["char_advanced_expanded"])

    def test_record_weapon_advanced_expanded(self) -> None:
        updated = record_weapon_advanced_expanded(
            {"startup_page_mode": STARTUP_MODE_ALWAYS_MAIN, "last_page": PAGE_MAIN},
            expanded=False,
        )
        self.assertFalse(updated["weapon_advanced_expanded"])

    def test_record_char_advanced_expanded(self) -> None:
        updated = record_char_advanced_expanded(
            {"startup_page_mode": STARTUP_MODE_ALWAYS_MAIN, "last_page": PAGE_MAIN},
            expanded=False,
        )
        self.assertFalse(updated["char_advanced_expanded"])

    def test_record_last_page_normalizes_invalid_value(self) -> None:
        updated = record_last_page(
            {"startup_page_mode": STARTUP_MODE_REMEMBER_LAST, "last_page": PAGE_ADVANCED},
            page="unknown",
        )
        self.assertEqual(updated["last_page"], PAGE_MAIN)


if __name__ == "__main__":
    unittest.main()

