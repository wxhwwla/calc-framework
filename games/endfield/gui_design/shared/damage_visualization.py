#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""伤害构成可视化（matplotlib 嵌入 GUI，可选依赖）。"""



from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)

class DamageSlice:

    """饼图/柱状图单段。"""



    label: str

    value: float





def is_matplotlib_available() -> bool:

    from utils.optional_deps import is_matplotlib_available as _probe



    return _probe()





def damage_breakdown_from_skill_map(skill_damage: dict[str, float]) -> tuple[DamageSlice, ...]:

    """从技能名→伤害映射生成切片（过滤非正数）。"""

    slices = [DamageSlice(label=name, value=float(dmg)) for name, dmg in skill_damage.items() if float(dmg) > 0]

    return tuple(slices)





def build_damage_pie_figure(

    slices: Sequence[DamageSlice],

    *,

    title: str = "伤害构成",

) -> Any:

    """构建饼图 Figure（调用方负责 plt.close）。"""

    from utils.gui.chart_theme import (
        chart_theme_dark,
        configure_matplotlib_gui_style,
        series_color,
        style_axes,
        style_figure,
    )



    configure_matplotlib_gui_style()

    import matplotlib.pyplot as plt



    theme = chart_theme_dark()

    labels = [s.label for s in slices]

    values = [s.value for s in slices]

    fig, ax = plt.subplots(figsize=(5, 4), dpi=100)

    style_figure(fig, theme)

    style_axes(ax, theme)

    if not values:

        ax.text(

            0.5,

            0.5,

            "无数据",

            ha="center",

            va="center",

            color=theme.text_muted,

        )

    else:

        colors = [series_color(theme, i) for i in range(len(values))]

        ax.pie(

            values,

            labels=labels,

            autopct="%1.1f%%",

            startangle=90,

            colors=colors,

            textprops={"color": theme.text, "fontsize": 10},

            wedgeprops={"edgecolor": theme.border, "linewidth": 0.8},

        )

    ax.set_title(title, color=theme.text)

    fig.tight_layout()

    return fig





def build_improvement_bar_figure(

    items: Sequence[tuple[str, float]],

    *,

    title: str = "相对基准提升率",

    ylabel: str = "提升 %",

) -> Any:

    """构建柱状图（默认用于提升率；亦可传入乘区占比等百分比序列）。"""

    from utils.gui.chart_theme import (
        bar_colors,
        chart_theme_dark,
        configure_matplotlib_gui_style,
        style_axes,
        style_figure,
    )



    configure_matplotlib_gui_style()

    import matplotlib.pyplot as plt



    theme = chart_theme_dark()

    labels = [name for name, _ in items]

    values = [val for _, val in items]

    fig, ax = plt.subplots(figsize=(6, 4), dpi=100)

    style_figure(fig, theme)

    style_axes(ax, theme)

    colors = bar_colors(theme, len(values))

    if values:

        max_idx = max(range(len(values)), key=lambda i: values[i])

        colors[max_idx] = theme.accent

    ax.bar(labels, values, color=colors, edgecolor=theme.border, linewidth=0.6)

    ax.set_title(title, color=theme.text)

    ax.set_ylabel(ylabel, color=theme.text)

    ax.tick_params(axis="x", rotation=25, labelsize=9)

    for tick in ax.get_xticklabels():

        tick.set_color(theme.text_secondary)

    ax.axhline(0, color=theme.border, linewidth=0.8)

    ax.grid(axis="y", linestyle="--", alpha=0.35)

    fig.tight_layout()

    return fig

