#!/usr/bin/env python3
"""confirm_selection 集成测试（真实 CTk 滚动区 + 模拟面板）。"""

from __future__ import annotations

import unittest

import pytest

pytestmark = pytest.mark.integration
from tests.fixtures.gui_fixtures import build_mock_app, ctk_available, destroy_mock_app_root


class TestPropertyDisplayIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not ctk_available():
            raise unittest.SkipTest("需要可用的 CustomTkinter / Tcl")
        import customtkinter as ctk

        cls._root = ctk.CTk()
        cls._root.withdraw()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._root.destroy()

    def setUp(self) -> None:
        import customtkinter as ctk

        self.app = build_mock_app(root=self._root)
        self.char_scroll = ctk.CTkScrollableFrame(self._root)
        self.weapon_scroll = ctk.CTkScrollableFrame(self._root)
        self.right_scroll = ctk.CTkScrollableFrame(self._root)

    def tearDown(self) -> None:
        for frame in (self.char_scroll, self.weapon_scroll, self.right_scroll):
            for child in frame.winfo_children():
                child.destroy()
        destroy_mock_app_root(self.app)

    def test_confirm_selection_populates_zone_snapshot(self) -> None:
        from gui_design.shared.display_view import confirm_selection

        confirm_selection(
            self.char_scroll,
            self.weapon_scroll,
            self.right_scroll,
            self.app.char_panel,
            self.app.weapon_panel,
            self.app.big_font,
            self.app.small_font,
            calculation_mode="zone_snapshot",
            enemy_defense=120.0,
        )
        children = self.right_scroll.winfo_children()
        self.assertGreater(len(children), 0)
        texts = [getattr(c, "cget", lambda _k: "")("text") for c in children]
        joined = " ".join(t for t in texts if t)
        self.assertIn("乘区", joined)

    def test_confirm_single_hit_mode(self) -> None:
        from gui_design.shared.display_view import confirm_selection

        confirm_selection(
            self.char_scroll,
            self.weapon_scroll,
            self.right_scroll,
            self.app.char_panel,
            self.app.weapon_panel,
            self.app.big_font,
            self.app.small_font,
            calculation_mode="single_hit",
            enemy_defense=100.0,
        )
        joined = " ".join(getattr(c, "cget", lambda _k: "")("text") for c in self.right_scroll.winfo_children())
        self.assertIn("最终伤害", joined)


if __name__ == "__main__":
    unittest.main()
