#!/usr/bin/env python3
"""matplotlib 图表主题：暗色系列配色（PySide6 Fusion Dark）。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Qt Fusion Dark 调色板常量
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

_matplotlib_gui_style_configured = False


@dataclass(frozen=True)
class ChartTheme:
    """嵌入 PySide6 暗色 GUI 的图表配色。"""

    figure_bg: str
    axes_bg: str
    text: str
    text_secondary: str
    text_muted: str
    accent: str
    primary: str
    primary_hover: str
    border: str
    grid: str
    series_colors: tuple[str, ...]


def chart_theme_dark() -> ChartTheme:
    """生成 Qt Fusion Dark 匹配的图表配色。"""
    return ChartTheme(
        figure_bg=_FIGURE_BG,
        axes_bg=_AXES_BG,
        text=_TEXT,
        text_secondary=_TEXT_SECONDARY,
        text_muted=_TEXT_MUTED,
        accent=_ACCENT,
        primary=_PRIMARY,
        primary_hover=_PRIMARY_HOVER,
        border=_BORDER,
        grid=_BORDER,
        series_colors=_DARK_SERIES,
    )


def configure_matplotlib_gui_style() -> None:
    """配置 matplotlib 字体 + 暗色样式（幂等，绘图前调用）。"""
    global _matplotlib_gui_style_configured
    from utils.gui_fonts import configure_matplotlib_font

    configure_matplotlib_font()
    if _matplotlib_gui_style_configured:
        return

    import matplotlib.pyplot as plt

    chart = chart_theme_dark()
    plt.rcParams.update(
        {
            "figure.facecolor": chart.figure_bg,
            "axes.facecolor": chart.axes_bg,
            "axes.edgecolor": chart.border,
            "axes.labelcolor": chart.text,
            "axes.titlecolor": chart.text,
            "xtick.color": chart.text_secondary,
            "ytick.color": chart.text_secondary,
            "text.color": chart.text,
            "grid.color": chart.grid,
            "grid.alpha": 0.35,
        }
    )
    _matplotlib_gui_style_configured = True


def reset_matplotlib_gui_style_for_tests() -> None:
    """测试专用：允许重复配置。"""
    global _matplotlib_gui_style_configured
    from utils.gui_fonts import reset_matplotlib_font_config_for_tests

    reset_matplotlib_font_config_for_tests()
    _matplotlib_gui_style_configured = False


def style_axes(ax: Any, theme: ChartTheme) -> None:
    """将单个子图背景/刻度/边框与主题对齐。"""
    ax.set_facecolor(theme.axes_bg)
    ax.tick_params(colors=theme.text_secondary, which="both")
    for spine in ax.spines.values():
        spine.set_color(theme.border)


def style_figure(fig: Any, theme: ChartTheme) -> None:
    """设置 Figure 背景。"""
    fig.patch.set_facecolor(theme.figure_bg)


def series_color(theme: ChartTheme, index: int) -> str:
    """按序取系列色（循环）。"""
    colors = theme.series_colors
    return colors[index % len(colors)]


def bar_colors(theme: ChartTheme, count: int) -> list[str]:
    """柱状图配色：默认主色。"""
    return [theme.primary] * max(0, count)
