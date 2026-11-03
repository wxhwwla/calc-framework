# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""图编辑器页面 — 节点预览文本计算。

原逻辑嵌套在 ``_GraphEditorPage._update_preview`` 中；它不依赖页面
``self``，抽出后便于单独测试，也避免页面模块继续膨胀。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from calc_framework.graph_editor.graph_editor_widget import GraphEditorWidget, NodeItem


def preview_text_for_node(canvas: GraphEditorWidget, node_item: NodeItem) -> str:
    """计算选中节点在属性面板中的预览文本。

    参数:
        canvas: 当前图编辑器画布。
        node_item: 选中的节点图元。

    返回:
        用于 ``PropPanel.set_preview_value`` 的预览文本。
    """
    from calc_framework.dag.engine import evaluate_graph
    from calc_framework.graph_editor.compiler import compile_graph
    from calc_framework.graph_editor.file_actions import collect_document

    node_id = node_item.node_id
    graph_node = node_item.to_graph_node()

    if graph_node.type == "var":
        path = graph_node.config.path
        return f"引用: {path}" if path else "(未设置路径)"
    if graph_node.type == "user_input":
        return f"默认值: {graph_node.config.default}"
    if graph_node.type == "const":
        return f"{graph_node.config.value}"

    # 对于 output / composite / binary 等节点，尝试编译求值
    try:
        doc = collect_document(canvas)
        dag = compile_graph(doc)
        if not dag.nodes:
            return "—"
        res = evaluate_graph(dag, {})

        if graph_node.type == "output":
            port_inputs = {}
            for e in doc.edges:
                port_inputs[(e.to_node, e.to_port)] = e.from_node
            source = port_inputs.get((node_id, 0))
            if source:
                val = res.node_values.get(source)
                if val is not None:
                    return f"{val:.6f}" if isinstance(val, float) else str(val)
                val = res.outputs.get(source)
                if val is not None:
                    return f"{val:.6f}" if isinstance(val, float) else str(val)
            return "(未连接)" if source is None else "—"

        if graph_node.type == "composite":
            for sub in dag.subgraphs.values():
                for out_def in sub.outputs.values():
                    expanded_key = f"{node_id}.{out_def.node}"
                    val = res.node_values.get(expanded_key)
                    if val is not None:
                        return f"{val:.6f}" if isinstance(val, float) else str(val)
            return f"[{graph_node.label or '复合节点'}]"

        val = res.node_values.get(node_id)
        if val is not None:
            return f"{val:.6f}" if isinstance(val, float) else str(val)
        val = res.outputs.get(node_id)
        return f"{val:.6f}" if val is not None else "—"
    except Exception as e:
        return f"错误: {str(e)[:60]}"
