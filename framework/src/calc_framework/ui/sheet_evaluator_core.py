# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""sheet_evaluator 的纯逻辑层 — 无 PySide6 依赖。

从 sheet_evaluator.py 提取而来，包含：
- var_to_dict: DAGVariable → dict 转换
- merge_context: context 合并逻辑
- render_html_from_values: HTML 输出渲染

GUI 层的 read_input / update_outputs / build_context / render_html
仍留在 sheet_evaluator.py，作为 Qt 包装调用本模块的纯函数。
"""

from __future__ import annotations

from typing import Any

from ..dag.schema import DAGVariable
from .layout import Layout


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


def merge_context(
    base_context: dict[str, Any],
    user_values: dict[str, Any],
    user_context_overrides: dict[str, tuple[str, list[str]]],
    context_overrides: dict[str, Any],
) -> dict[str, Any]:
    """构建 DAG 求值的完整 context（纯逻辑，不读取 Qt 控件）。

    合并 base_context + user_values + user_context_overrides + context_overrides。

    Parameters
    ----------
    base_context : dict
        基础 context（来自数据加载层）。
    user_values : dict
        user_input 变量的当前值，key 为完整路径如 "user.加成"。
    user_context_overrides : dict
        用户输入到 context 的映射规则。
        value 为 (target_path, merge_keys)，merge_keys 中 "override" 替换、"add" 累加。
    context_overrides : dict
        直接覆盖的 context 值，key 为 "ns.key" 格式。
    """
    context = dict(base_context)

    for user_path, value in user_values.items():
        parts = user_path.split(".", 1)
        if len(parts) == 2:
            context.setdefault(parts[0], {})[parts[1]] = value

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


def build_context_from_values(
    base_context: dict[str, Any],
    variables: dict[str, DAGVariable | dict[str, Any]],
    user_values: dict[str, Any],
    user_context_overrides: dict[str, tuple[str, list[str]]],
    context_overrides: dict[str, Any],
) -> dict[str, Any]:
    """构建 DAG 求值的完整 context（纯逻辑，不读取 Qt 控件）。

    与 merge_context 相同，但接受 variables 参数以保持与旧 API 的签名兼容。
    variables 参数未使用，仅保留签名一致性。
    """
    return merge_context(base_context, user_values, user_context_overrides, context_overrides)


def render_html_from_values(
    layout: Layout,
    output_values: dict[str, str],
) -> str:
    """将输出面板渲染为 HTML 表格（纯逻辑，不读取 QLabel）。

    Parameters
    ----------
    layout : Layout
        布局描述。
    output_values : dict
        输出名称到已格式化文本的映射。缺失的 key 显示为 "--"。
    """
    parts: list[str] = ['<table style="width:100%;border-collapse:collapse;">']
    for sec in layout.sections:
        if sec.type != "outputs":
            continue
        parts.append(
            f'<tr style="background:#2B6CB6;color:white;">'
            f'<td colspan="2" style="padding:4px 8px;font-weight:bold;">'
            f"{sec.title}</td></tr>"
        )
        for out_name in sec.outputs:
            val = output_values.get(out_name, "--")
            parts.append(
                f'<tr><td style="padding:2px 8px;">{out_name}</td><td style="padding:2px 8px;text-align:right;">{val}</td></tr>'
            )
    parts.append("</table>")
    return "\n".join(parts)
