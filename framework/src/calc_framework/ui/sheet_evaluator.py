# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""ComputeSheet 求值逻辑 — 读取 user_input → 构建 context → 解析 outputs。

从 compute_sheet.py 拆分而来。

纯逻辑函数（var_to_dict、build_context_from_values、render_html_from_values）
已提取到 ``sheet_evaluator_core.py``，可被 Web/CLI/测试直接使用。
"""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QLabel,
    QLineEdit,
    QSlider,
    QSpinBox,
    QWidget,
)

from ..dag.engine import DAGResult
from ..dag.schema import DAGVariable
from ..logging import get_logger
from .controls import ControlSpec, format_node_value
from .layout import Layout
from .sheet_evaluator_core import (
    build_context_from_values,
    render_html_from_values,
    var_to_dict,
)

logger = get_logger(__name__)

# Re-export for backward compatibility
__all__ = [
    "build_context",
    "build_context_from_values",
    "read_input",
    "render_html",
    "render_html_from_values",
    "update_outputs",
    "var_to_dict",
]


def read_input(
    path: str,
    input_widgets: dict[str, tuple[QWidget, ControlSpec]],
    variables: dict[str, DAGVariable | dict[str, Any]],
) -> Any:
    """从输入控件读取一个变量的当前值。"""
    entry = input_widgets.get(path)
    if entry is None:
        raw_var = variables.get(path)
        if raw_var is None:
            return 0
        vd = var_to_dict(raw_var)
        return vd.get("default", 0)
    w, spec = entry
    if isinstance(w, QSlider):
        val = w.value()
        if spec.step < 1:
            return val / 100.0
        return val
    if isinstance(w, QDoubleSpinBox):
        return w.value()
    if isinstance(w, QSpinBox):
        return w.value()
    if isinstance(w, QCheckBox):
        return w.isChecked()
    if isinstance(w, QComboBox):
        return w.currentText()
    if isinstance(w, QLineEdit):
        try:
            return float(w.text())
        except ValueError:
            return 0.0
    return 0


def build_context(
    base_context: dict[str, Any],
    variables: dict[str, DAGVariable | dict[str, Any]],
    input_widgets: dict[str, tuple[QWidget, ControlSpec]],
    user_context_overrides: dict[str, tuple[str, list[str]]],
    context_overrides: dict[str, Any],
) -> dict[str, Any]:
    """构建 DAG 求值的完整 context。

    合并 base_context + user_input 值 + user_context_overrides + context_overrides。
    """
    # 先用 read_input 从控件读取所有 user_input 值
    user_values: dict[str, Any] = {}
    for path, var in variables.items():
        vd = var_to_dict(var)
        source = vd.get("source", "")
        if source == "user_input":
            value = read_input(path, input_widgets, variables)
            user_values[path] = value

    # 委托给纯函数构建 context
    return build_context_from_values(
        base_context,
        variables,
        user_values,
        user_context_overrides,
        context_overrides,
    )


def update_outputs(
    result: DAGResult,
    layout: Layout,
    output_labels: dict[str, QLabel],
    output_formats: dict[str, str],
) -> None:
    """将 DAG 求值结果更新到输出标签。"""
    for sec in layout.sections:
        if sec.type != "outputs":
            continue
        for out_name in sec.outputs:
            label = output_labels.get(out_name)
            if label is None:
                continue
            value = result.outputs.get(out_name)
            fmt = output_formats.get(out_name, ".4f")
            label.setText(format_node_value(value, fmt))


def render_html(layout: Layout, output_labels: dict[str, QLabel]) -> str:
    """将当前输出面板渲染为 HTML 表格。"""
    # 从 QLabel 提取文本值
    output_values: dict[str, str] = {}
    for sec in layout.sections:
        if sec.type != "outputs":
            continue
        for out_name in sec.outputs:
            label = output_labels.get(out_name)
            output_values[out_name] = label.text() if label else "--"

    # 委托给纯函数渲染 HTML
    return render_html_from_values(layout, output_values)
