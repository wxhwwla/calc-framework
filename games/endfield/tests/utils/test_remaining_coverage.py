# SPDX-License-Identifier: AGPL-3.0
from __future__ import annotations



import json

import os

import tempfile

import tkinter as tk

from pathlib import Path

from unittest.mock import MagicMock, patch



from utils.gui.chart_theme import (

    ChartTheme,

    chart_theme_dark,

    configure_matplotlib_gui_style,

    style_axes,

    style_figure,

)

from utils.gui.fonts import (

    configure_matplotlib_font,

    matplotlib_sans_serif_families,

    system_font_family,

)

from utils.gui.window import (

    _geometry_fill_screen,

    _try_zoomed_attribute,

    _try_zoomed_state,

    apply_startup_maximized,

)

from utils.optional_deps import (

    format_missing_gui_extras,

    format_missing_lines,

    format_missing_runtime_dependencies,

    is_matplotlib_available,

    missing_dependencies,

    missing_runtime_packages,

    OptionalDependency,

    ensure_runtime_dependencies,

)

from utils.platform_win32_patch import apply_platform_win32_patch

from utils.search_format import format_duration_human, format_workload_estimate_line





# ── gui_window.py ──────────────────────────────────────────────────────────



class TestGuiWindowDetail:

    def test_try_zoomed_state_success(self) -> None:

        win = MagicMock()

        assert _try_zoomed_state(win) is True

        win.state.assert_called_once_with("zoomed")



    def test_try_zoomed_state_failure(self) -> None:

        win = MagicMock()

        win.state.side_effect = Exception("no")

        assert _try_zoomed_state(win) is False



    def test_try_zoomed_attribute_success(self) -> None:

        win = MagicMock()

        assert _try_zoomed_attribute(win) is True

        win.attributes.assert_called_once_with("-zoomed", True)



    def test_try_zoomed_attribute_failure(self) -> None:

        win = MagicMock()

        win.attributes.side_effect = Exception("no")

        assert _try_zoomed_attribute(win) is False



    def test_geometry_fill_screen_normal(self) -> None:

        win = MagicMock()

        win.winfo_screenwidth.return_value = 1920

        win.winfo_screenheight.return_value = 1080

        _geometry_fill_screen(win)

        win.geometry.assert_called_once()



    def test_geometry_fill_screen_small(self) -> None:

        win = MagicMock()

        win.winfo_screenwidth.return_value = 320

        win.winfo_screenheight.return_value = 240

        _geometry_fill_screen(win)

        win.geometry.assert_not_called()



    def test_geometry_fill_screen_exception(self) -> None:

        win = MagicMock()

        win.winfo_screenwidth.side_effect = Exception("no")

        _geometry_fill_screen(win)



    def test_apply_calls_geometry_when_both_zoom_fail(self) -> None:

        win = MagicMock()

        win.state.side_effect = Exception("no zoomed")

        win.attributes.side_effect = Exception("no attr")

        win.winfo_screenwidth.return_value = 1920

        win.winfo_screenheight.return_value = 1080



        def side_effect(fn):

            fn()



        win.after_idle.side_effect = side_effect

        apply_startup_maximized(win)

        win.geometry.assert_called_once()



    def test_apply_startup_maximized(self) -> None:

        win = MagicMock()



        def side_effect(fn):

            fn()



        win.after_idle.side_effect = side_effect

        apply_startup_maximized(win)

        win.after_idle.assert_called_once()



    def test_apply_startup_maximized_no_after_idle(self) -> None:

        win = MagicMock()

        win.after_idle.side_effect = Exception("no after_idle")

        apply_startup_maximized(win)





# ── platform_win32_patch.py ────────────────────────────────────────────────



class TestPlatformWin32PatchDetail:

    def test_apply_twice_returns_early(self) -> None:

        apply_platform_win32_patch()

        apply_platform_win32_patch()





# ── gui_chart_theme.py ─────────────────────────────────────────────────────



class TestGuiChartTheme:

    def test_chart_theme_dark_returns_dataclass(self) -> None:

        theme = chart_theme_dark()

        assert isinstance(theme, ChartTheme)

        assert theme.figure_bg == "#1E1E1E"



    def test_configure_matplotlib_gui_style(self) -> None:

        from utils.gui.chart_theme import reset_matplotlib_gui_style_for_tests

        reset_matplotlib_gui_style_for_tests()

        configure_matplotlib_gui_style()



    def test_configure_matplotlib_gui_style_idempotent(self) -> None:

        from utils.gui.chart_theme import reset_matplotlib_gui_style_for_tests

        reset_matplotlib_gui_style_for_tests()

        configure_matplotlib_gui_style()

        configure_matplotlib_gui_style()



    def test_style_axes(self) -> None:

        ax = MagicMock()

        theme = chart_theme_dark()

        style_axes(ax, theme)

        ax.set_facecolor.assert_called_once()

        ax.tick_params.assert_called_once()



    def test_style_figure(self) -> None:

        fig = MagicMock()

        theme = chart_theme_dark()

        style_figure(fig, theme)

        fig.patch.set_facecolor.assert_called_once()



    def test_series_color(self) -> None:

        from utils.gui.chart_theme import series_color

        theme = chart_theme_dark()

        c0 = series_color(theme, 0)

        c1 = series_color(theme, 1)

        assert c0 != c1

        c8 = series_color(theme, 8)

        assert c8 == c0





# ── gui_fonts.py ───────────────────────────────────────────────────────────



class TestGuiFonts:

    def test_matplotlib_sans_serif_families_tcl_error(self) -> None:

        with patch("utils.gui_fonts.system_font_family", side_effect=tk.TclError("no tk")):

            families = matplotlib_sans_serif_families()

            assert len(families) >= 2



    def test_matplotlib_sans_serif_families_with_valid_font(self) -> None:

        with patch("utils.gui_fonts.system_font_family", return_value="CustomFont"):

            families = matplotlib_sans_serif_families()

            assert families[0] == "CustomFont"

            assert any("DejaVu" in f for f in families)



    def test_matplotlib_sans_serif_families_contains_dejavu(self) -> None:

        families = matplotlib_sans_serif_families()

        assert any("DejaVu" in f for f in families)



    def test_configure_matplotlib_font(self) -> None:

        from utils.gui.fonts import reset_matplotlib_font_config_for_tests

        reset_matplotlib_font_config_for_tests()

        configure_matplotlib_font()



    def test_configure_matplotlib_font_idempotent(self) -> None:

        from utils.gui.fonts import reset_matplotlib_font_config_for_tests

        reset_matplotlib_font_config_for_tests()

        configure_matplotlib_font()

        configure_matplotlib_font()





# ── optional_deps.py ──────────────────────────────────────────────────────



class TestOptionalDepsDetail:

    def test_missing_dependencies_empty_input(self) -> None:

        result = missing_dependencies([])

        assert result == []



    def test_format_missing_lines_non_empty_probe(self) -> None:

        dep = OptionalDependency(feature="xyz", module="__nonexist_module__", pip_hint="pip")

        result = format_missing_lines([dep])

        assert "pip" in result

        assert "xyz" in result



    def test_format_missing_gui_extras_missing(self) -> None:

        text = format_missing_gui_extras()

        assert isinstance(text, str)





# ── search_format.py ──────────────────────────────────────────────────────



class TestSearchFormatDetail:

    def test_format_duration_human_large(self) -> None:

        result = format_duration_human(99999)

        assert "27 小时" in result and "分" in result



    def test_format_workload_estimate_zero_total(self) -> None:

        wl = MagicMock(total_combinations=0, weapon_count=0, loadout_combinations=0)

        dur = MagicMock(estimated_seconds=0, max_workers=1)

        text = format_workload_estimate_line(workload=wl, duration=dur)

        assert "0" in text

