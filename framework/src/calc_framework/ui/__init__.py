# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""声明式 UI 渲染引擎 — ComputeSheet 计算表组件。

UI 组件按需导入，使只使用 ``calc_framework.ui.i18n`` 的 Web/无头环境无需 PySide6。
"""

from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from calc_framework.ui.compute_sheet import ComputeSheet
    from calc_framework.ui.controls import ControlSpec, format_node_value, infer_control
    from calc_framework.ui.layout import Layout, Section, load_layout, load_layout_json
    from calc_framework.ui.theme import ThemeManager
    from calc_framework.ui.viewer import CalcPackViewer

_EXPORTS = {
    "CalcPackViewer": ("calc_framework.ui.viewer", "CalcPackViewer"),
    "ComputeSheet": ("calc_framework.ui.compute_sheet", "ComputeSheet"),
    "ControlSpec": ("calc_framework.ui.controls", "ControlSpec"),
    "Layout": ("calc_framework.ui.layout", "Layout"),
    "Section": ("calc_framework.ui.layout", "Section"),
    "ThemeManager": ("calc_framework.ui.theme", "ThemeManager"),
    "format_node_value": ("calc_framework.ui.controls", "format_node_value"),
    "infer_control": ("calc_framework.ui.controls", "infer_control"),
    "load_layout": ("calc_framework.ui.layout", "load_layout"),
    "load_layout_json": ("calc_framework.ui.layout", "load_layout_json"),
}


def __getattr__(name: str) -> object:
    """按公开导出名称加载真实 UI 模块。"""
    try:
        module_name, attribute = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    value = getattr(import_module(module_name), attribute)
    globals()[name] = value
    return value


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
