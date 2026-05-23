#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""伤害构成可视化（matplotlib 嵌入 GUI，可选依赖）。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Sequence


@dataclass(frozen=True)
class DamageSlice:
    """饼图/柱状图单段。"""

    label: str
    value: float


def is_matplotlib_available() -> bool:
    try:
        import matplotlib  # noqa: F401

        return True
    except ImportError:
        return False


def damage_breakdown_from_skill_map(skill_damage: dict[str, float]) -> tuple[DamageSlice, ...]:
    """从技能名→伤害映射生成切片（过滤非正数）。"""
    slices = [
        DamageSlice(label=name, value=float(dmg))
        for name, dmg in skill_damage.items()
        if float(dmg) > 0
    ]
    return tuple(slices)


def build_damage_pie_figure(
    slices: Sequence[DamageSlice],
    *,
    title: str = "伤害构成",
) -> Any:
    """构建饼图 Figure（调用方负责 plt.close）。"""
    import matplotlib.pyplot as plt

    labels = [s.label for s in slices]
    values = [s.value for s in slices]
    fig, ax = plt.subplots(figsize=(5, 4), dpi=100)
    if not values:
        ax.text(0.5, 0.5, "无数据", ha="center", va="center")
    else:
        ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
    ax.set_title(title)
    fig.tight_layout()
    return fig


def build_improvement_bar_figure(
    items: Sequence[tuple[str, float]],
    *,
    title: str = "相对基准提升率",
    ylabel: str = "提升 %",
) -> Any:
    """构建柱状图（默认用于提升率；亦可传入乘区占比等百分比序列）。"""
    import matplotlib.pyplot as plt

    labels = [name for name, _ in items]
    values = [val for _, val in items]
    fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
    ax.bar(labels, values, color="#4ECDC4")
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.axhline(0, color="#888888", linewidth=0.8)
    fig.tight_layout()
    return fig
