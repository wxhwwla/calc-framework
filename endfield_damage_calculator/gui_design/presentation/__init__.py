#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
无 CustomTkinter 的展示与预览文案/快照。

子模块：
- display_lines：属性列、15 乘区、单段伤害文案
- preview_lines：单/多技能快速预览
- damage_snapshot：仪表盘与历史用伤害摘要
- search_results_lines：全量遍历结果报告
"""

from . import damage_snapshot, display_lines, preview_lines, search_results_lines

__all__ = [
    "damage_snapshot",
    "display_lines",
    "preview_lines",
    "search_results_lines",
]
