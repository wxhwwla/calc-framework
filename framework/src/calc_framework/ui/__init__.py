# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""声明式 UI 渲染引擎 — ComputeSheet 计算表组件。

用法::

    from calc_framework.ui import (
        ComputeSheet, ControlSpec, infer_control,
        Layout, Section, load_layout,
        CalcPackViewer, ThemeManager, format_node_value,
    )
"""

from calc_framework.ui.compute_sheet import ComputeSheet
from calc_framework.ui.controls import ControlSpec, format_node_value, infer_control
from calc_framework.ui.layout import Layout, Section, load_layout, load_layout_json
from calc_framework.ui.theme import ThemeManager
from calc_framework.ui.viewer import CalcPackViewer

__all__ = [
    "CalcPackViewer",
    "ComputeSheet",
    "ControlSpec",
    "Layout",
    "Section",
    "ThemeManager",
    "format_node_value",
    "infer_control",
    "load_layout",
    "load_layout_json",
]
