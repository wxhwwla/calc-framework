# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""search_controller — 搜索编排纯逻辑（无 PySide6 依赖）。

从 endfield_search.py 提取的搜索耗时展示和警告决策逻辑。
可被 GUI / Web / CLI / 测试直接复用。
"""

from __future__ import annotations

from dataclasses import dataclass


def format_search_duration(seconds: float) -> str:
    """将搜索耗时秒数格式化为人类可读文案。

    从 endfield_search.py ActionsSearchMixin._refresh_search_estimate() 提取。

    参数：
        seconds: 预估耗时（秒），0 或负数返回 "N/A"。

    返回：
        如 "45s"、"3min"、"1.5h"、"N/A"。
    """
    if seconds <= 0:
        return "N/A"
    mins = seconds / 60
    if mins >= 60:
        return f"{mins / 60:.1f}h"
    if mins >= 1:
        return f"{mins:.0f}min"
    return f"{seconds:.0f}s"


def should_warn_search_combinations(estimated_seconds: float, threshold: float = 120.0) -> bool:
    """判断搜索预估耗时是否超过警告阈值。

    从 endfield_search.py ActionsSearchMixin._on_full_search() 的警告逻辑提取。

    参数：
        estimated_seconds: 预估耗时（秒）。
        threshold: 警告阈值（秒），默认 120（2 分钟）。

    返回：
        True 表示应弹出确认对话框。
    """
    return estimated_seconds >= threshold


@dataclass
class SearchEstimateDisplay:
    """搜索预估展示数据。

    属性：
        duration_text: 格式化的耗时文案
        should_warn: 是否应弹出确认对话框
        estimated_seconds: 原始预估秒数
    """

    duration_text: str
    should_warn: bool
    estimated_seconds: float

    @classmethod
    def from_seconds(cls, seconds: float, threshold: float = 120.0) -> SearchEstimateDisplay:
        """从秒数构建展示数据。"""
        return cls(
            duration_text=format_search_duration(seconds),
            should_warn=should_warn_search_combinations(seconds, threshold),
            estimated_seconds=seconds,
        )
