#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""matplotlib 图表主题：与 CustomTkinter 外观/颜色主题同步。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

# CustomTkinter 命名灰阶 → 十六进制（与官方主题一致）
_CTK_GRAY_HEX: dict[str, str] = {
    "gray10": "#1A1A1A",
    "gray14": "#242424",
    "gray17": "#2B2B2B",
    "gray20": "#333333",
    "gray28": "#464646",
    "gray41": "#666666",
    "gray53": "#828282",
    "gray60": "#999999",
    "gray65": "#A6A6A6",
    "gray74": "#BFBFBF",
    "gray81": "#D1D1D1",
    "gray86": "#DBDBDB",
    "gray92": "#EBEBEB",
}

# GUI 内手写强调色（与 enhancement_controls 等一致）
_GUI_ACCENT = "#FF6B6B"
_GUI_TEXT_SECONDARY = "#CCCCCC"
_GUI_TEXT_MUTED = "#B8B8B8"
_GUI_PANEL = "#2A2A2A"

_matplotlib_gui_style_configured = False


@dataclass(frozen=True)
class ChartTheme:
    """嵌入 CTk 的图表配色。"""

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


def _appearance_index() -> int:
    """0=浅色，1=深色（与 CTk 主题元组下标一致）。"""
    import customtkinter as ctk

    mode = str(ctk.get_appearance_mode()).lower()
    return 0 if mode == "light" else 1


def resolve_ctk_color(value: Any, *, mode_index: int | None = None) -> str:
    """将 ThemeManager 颜色项解析为 #RRGGBB。"""
    idx = _appearance_index() if mode_index is None else mode_index
    if isinstance(value, (list, tuple)):
        raw = value[idx] if len(value) > idx else value[-1]
    else:
        raw = value
    text = str(raw).strip()
    if text.startswith("#"):
        return text
    return _CTK_GRAY_HEX.get(text, text)


def chart_theme_from_ctk() -> ChartTheme:
    """从当前 CTk 外观模式与 blue 主题生成图表配色。"""
    import customtkinter as ctk

    theme = ctk.ThemeManager.theme
    idx = _appearance_index()
    frame_bg = resolve_ctk_color(theme["CTkFrame"]["fg_color"], mode_index=idx)
    label_text = resolve_ctk_color(theme["CTkLabel"]["text_color"], mode_index=idx)
    btn_fg = resolve_ctk_color(theme["CTkButton"]["fg_color"], mode_index=idx)
    btn_hover = resolve_ctk_color(theme["CTkButton"]["hover_color"], mode_index=idx)
    border = resolve_ctk_color(theme["CTkFrame"]["border_color"], mode_index=idx)
    app_bg = resolve_ctk_color(theme["CTk"]["fg_color"], mode_index=idx)

    if idx == 1:
        figure_bg = app_bg
        axes_bg = _GUI_PANEL if _GUI_PANEL else frame_bg
        text_secondary = _GUI_TEXT_SECONDARY
        text_muted = _GUI_TEXT_MUTED
        series = (
            btn_fg,
            "#3B8ED0",
            _GUI_ACCENT,
            btn_hover,
            "#5BA3D9",
            "#36719F",
            "#7EB8E8",
            "#C75C5C",
        )
    else:
        figure_bg = app_bg
        axes_bg = frame_bg
        text_secondary = resolve_ctk_color(["gray28", "gray41"], mode_index=idx)
        text_muted = resolve_ctk_color(["gray41", "gray53"], mode_index=idx)
        series = (
            btn_fg,
            "#3B8ED0",
            _GUI_ACCENT,
            btn_hover,
            "#5BA3D9",
            "#144870",
            "#7EB8E8",
            "#E07A7A",
        )

    return ChartTheme(
        figure_bg=figure_bg,
        axes_bg=axes_bg,
        text=label_text,
        text_secondary=text_secondary,
        text_muted=text_muted,
        accent=_GUI_ACCENT,
        primary=btn_fg,
        primary_hover=btn_hover,
        border=border,
        grid=border,
        series_colors=series,
    )


def configure_matplotlib_gui_style() -> None:
    """配置 matplotlib 字体 + 与 CTk 一致的全局样式（幂等）。"""
    global _matplotlib_gui_style_configured
    from utils.gui_fonts import configure_matplotlib_font

    configure_matplotlib_font()
    if _matplotlib_gui_style_configured:
        return

    import matplotlib.pyplot as plt

    chart = chart_theme_from_ctk()
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
    """柱状图配色：默认主色，最大值用强调色。"""
    if count <= 0:
        return []
    return [theme.primary] * count
