#!/usr/bin/env python3
"""matplotlib 图表主题：暗色系列配色（PySide6 Fusion Dark）。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_FIGURE_BG = "#1E1E1E"
_AXES_BG = "#2A2A2A"
_TEXT = "#E0E0E0"
_TEXT_SECONDARY = "#CCCCCC"
_TEXT_MUTED = "#B8B8B8"
_ACCENT = "#FF6B6B"
_PRIMARY = "#2B6CB6"
_PRIMARY_HOVER = "#3182CE"
_BORDER = "#464646"

_DARK_SERIES = (
    _PRIMARY,
    "#3B8ED0",
    _ACCENT,
    _PRIMARY_HOVER,
    "#5BA3D9",
    "#36719F",
    "#7EB8E8",
    "#C75C5C",
)

_DARK_GRID = "#373737"
_DARK_LEGEND_BG = "#2A2A2A"


@dataclass
class ChartTheme:
    figure_bg: str = _FIGURE_BG
    axes_bg: str = _AXES_BG
    text: str = _TEXT
    text_secondary: str = _TEXT_SECONDARY
    text_muted: str = _TEXT_MUTED
    accent: str = _ACCENT
    primary: str = _PRIMARY
    primary_hover: str = _PRIMARY_HOVER
    border: str = _BORDER
    grid: str = _DARK_GRID
    legend_bg: str = _DARK_LEGEND_BG
    series: tuple[str, ...] = _DARK_SERIES


def chart_theme_dark() -> ChartTheme:
    return ChartTheme()


def configure_matplotlib_gui_style() -> dict[str, Any]:
    global _MATPLOTLIB_GUI_STYLE_CONFIGURED
    if _MATPLOTLIB_GUI_STYLE_CONFIGURED:
        return {}
    _MATPLOTLIB_GUI_STYLE_CONFIGURED = True
    import matplotlib.pyplot as plt
    rc = {
        "figure.facecolor": _FIGURE_BG,
        "axes.facecolor": _AXES_BG,
        "axes.edgecolor": _BORDER,
        "axes.labelcolor": _TEXT,
        "axes.titlecolor": _TEXT,
        "xtick.color": _TEXT_SECONDARY,
        "ytick.color": _TEXT_SECONDARY,
        "grid.color": _DARK_GRID,
        "text.color": _TEXT,
        "legend.facecolor": _DARK_LEGEND_BG,
        "legend.edgecolor": _BORDER,
        "legend.labelcolor": _TEXT,
        "figure.subplot.left": 0.1,
        "figure.subplot.right": 0.92,
        "figure.subplot.top": 0.92,
        "figure.subplot.bottom": 0.12,
    }
    plt.rcParams.update(rc)
    return rc


def apply_dark_theme() -> dict[str, Any]:
    return configure_matplotlib_gui_style()


def style_axes(ax: Any, theme: ChartTheme | None = None) -> None:
    if theme is None:
        theme = chart_theme_dark()
    ax.set_facecolor(theme.axes_bg)
    ax.tick_params(colors=theme.text_secondary)
    for spine in ax.spines.values():
        spine.set_color(theme.border)
    ax.xaxis.label.set_color(theme.text)
    ax.yaxis.label.set_color(theme.text)
    ax.title.set_color(theme.text)


def style_figure(fig: Any, theme: ChartTheme | None = None) -> None:
    if theme is None:
        theme = chart_theme_dark()
    fig.patch.set_facecolor(theme.figure_bg)


def series_color(theme: ChartTheme | None = None, index: int = 0) -> str:
    if theme is None:
        theme = chart_theme_dark()
    return theme.series[index % len(theme.series)]


def bar_colors(theme: ChartTheme | None = None, count: int = 1) -> list[str]:
    if theme is None:
        theme = chart_theme_dark()
    return [theme.series[i % len(theme.series)] for i in range(count)]


_MATPLOTLIB_GUI_STYLE_CONFIGURED = False


def reset_matplotlib_gui_style_for_tests() -> None:
    global _MATPLOTLIB_GUI_STYLE_CONFIGURED
    _MATPLOTLIB_GUI_STYLE_CONFIGURED = False


_DARK_PALETTE = {
    "figure_bg": _FIGURE_BG,
    "axes_bg": _AXES_BG,
    "text": _TEXT,
    "text_secondary": _TEXT_SECONDARY,
    "text_muted": _TEXT_MUTED,
    "accent": _ACCENT,
    "primary": _PRIMARY,
    "primary_hover": _PRIMARY_HOVER,
    "border": _BORDER,
    "grid": _DARK_GRID,
    "legend_bg": _DARK_LEGEND_BG,
    "series": list(_DARK_SERIES),
}
