# SPDX-License-Identifier: AGPL-3.0
"""ComputeSheet 求值逻辑 — 读取 user_input → 构建 context → 解析 outputs。

从 compute_sheet.py 拆分而来。
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

logger = get_logger(__name__)


def var_to_dict(var: DAGVariable | dict[str, Any]) -> dict[str, Any]:
    """将 DAGVariable 或 dict 统一转换为 dict。"""
    if isinstance(var, dict):
        return var
    return {
        "type": var.type,
        "source": var.source,
        "description": var.description,
        "default": var.default,
        "min": var.min,
        "max": var.max,
    }


def read_input(
    path: str,
    input_widgets: dict[str, tuple[QWidget, ControlSpec]],
    variables: dict[str, DAGVariable],
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
    variables: dict[str, DAGVariable],
    input_widgets: dict[str, tuple[QWidget, ControlSpec]],
    user_context_overrides: dict[str, tuple[str, list[str]]],
    context_overrides: dict[str, Any],
) -> dict[str, Any]:
    """构建 DAG 求值的完整 context。

    合并 base_context + user_input 值 + user_context_overrides + context_overrides。
    """
    context = dict(base_context)

    user_values: dict[str, float] = {}
    for path, var in variables.items():
        vd = var_to_dict(var)
        source = vd.get("source", "")
        if source == "user_input":
            value = read_input(path, input_widgets, variables)
            parts = path.split(".", 1)
            if len(parts) == 2:
                context.setdefault(parts[0], {})[parts[1]] = value
            user_values[path] = value

    for user_path, (target_path, merge_keys) in user_context_overrides.items():
        uv = user_values.get(user_path)
        if uv is None:
            continue
        parts = target_path.split(".", 1)
        if len(parts) != 2:
            continue
        ns, key = parts
        for mk in merge_keys:
            if mk == "override":
                context.setdefault(ns, {})[key] = uv
            elif mk == "add":
                current = context.get(ns, {}).get(key, 0.0)
                context.setdefault(ns, {})[key] = current + uv

    for path, value in context_overrides.items():
        parts = path.split(".", 1)
        if len(parts) == 2:
            context.setdefault(parts[0], {})[parts[1]] = value

    return context


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
    parts: list[str] = ['<table style="width:100%;border-collapse:collapse;">']
    for sec in layout.sections:
        if sec.type != "outputs":
            continue
        parts.append(
            f'<tr style="background:#2B6CB6;color:white;">'
            f'<td colspan="2" style="padding:4px 8px;font-weight:bold;">'
            f'{sec.title}</td></tr>'
        )
        for out_name in sec.outputs:
            label = output_labels.get(out_name)
            val = label.text() if label else "--"
            parts.append(
                f"<tr>"
                f'<td style="padding:2px 8px;">{out_name}</td>'
                f'<td style="padding:2px 8px;text-align:right;">{val}</td>'
                f"</tr>"
            )
    parts.append("</table>")
    return "\n".join(parts)
