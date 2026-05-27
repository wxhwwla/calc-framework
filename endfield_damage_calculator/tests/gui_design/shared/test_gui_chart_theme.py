#!/usr/bin/env python3
"""matplotlib 图表与 CTk 主题同步。"""

from __future__ import annotations

import unittest

from utils.gui_chart_theme import (
    chart_theme_from_ctk,
    configure_matplotlib_gui_style,
    reset_matplotlib_gui_style_for_tests,
    resolve_ctk_color,
)


class TestGuiChartTheme(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from utils.platform_win32_patch import apply_platform_win32_patch

        apply_platform_win32_patch()
        import customtkinter as ctk

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

    def test_resolve_ctk_gray_to_hex(self) -> None:
        self.assertEqual(resolve_ctk_color("gray17", mode_index=1), "#2B2B2B")
        self.assertEqual(resolve_ctk_color(["#3B8ED0", "#1F6AA5"], mode_index=1), "#1F6AA5")

    def test_dark_theme_matches_gui_palette(self) -> None:
        theme = chart_theme_from_ctk()
        self.assertEqual(theme.figure_bg, "#242424")
        self.assertEqual(theme.axes_bg, "#2A2A2A")
        self.assertEqual(theme.text, "#DCE4EE")
        self.assertEqual(theme.primary, "#1F6AA5")
        self.assertEqual(theme.accent, "#FF6B6B")

    def test_configure_matplotlib_gui_style_sets_dark_figure(self) -> None:
        reset_matplotlib_gui_style_for_tests()
        configure_matplotlib_gui_style()
        import matplotlib.pyplot as plt

        self.assertEqual(plt.rcParams["figure.facecolor"], "#242424")
        self.assertEqual(plt.rcParams["axes.facecolor"], "#2A2A2A")


if __name__ == "__main__":
    unittest.main()
