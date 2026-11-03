# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""图编辑器 — 选中节点的属性面板预览文本。

原逻辑嵌套在 ``__main__.main`` 的 ``_update_preview`` 闭包中；
它不依赖窗口状态，抽出后便于单独测试，也让入口文件回到可读规模。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..graph_editor_widget import GraphEditorWidget, NodeItem


def preview_text_for_node(canvas: GraphEditorWidget, node_item: NodeItem) -> str:
    """计算选中节点在属性面板中的预览文本。

    参数:
        canvas: 当前图编辑器画布。
        node_item: 选中的节点图元。

    返回:
        用于 ``PropPanel.set_preview_value`` 的预览文本。
    """
    from ...dag.engine import evaluate_graph
    from ..compiler import compile_graph
    from ..file_actions import collect_document

    node_id = node_item.node_id
    graph_node = node_item.to_graph_node()

    # 对于变量引用节点，显示引用路径
    if graph_node.type == "var":
        path = graph_node.config.path
        return f"引用: {path}" if path else "(未设置路径)"

    # 对于用户输入节点，显示默认值
    if graph_node.type == "user_input":
        return f"默认值: {graph_node.config.default}"

    # 对于常量节点，显示值
    if graph_node.type == "const":
        return f"{graph_node.config.value}"

    # 对于输出节点，追踪输入源的值
    if graph_node.type == "output":
        try:
            doc = collect_document(canvas)
            dag = compile_graph(doc)
            if not dag.nodes:
                return "—"
            res = evaluate_graph(dag, {})
            port_inputs = {}
            for e in doc.edges:
                port_inputs[(e.to_node, e.to_port)] = e.from_node
            source = port_inputs.get((node_id, 0))
            if source:
                val = res.node_values.get(source)
                if val is not None:
                    return f"{val:.6f}" if isinstance(val, float) else str(val)
                # 源可能是复合节点，值在 outputs 中
                val = res.outputs.get(source)
                if val is not None:
                    return f"{val:.6f}" if isinstance(val, float) else str(val)
                return "—"
            return "(未连接)"
        except Exception as e:
            return f"错误: {str(e)[:60]}"

    # 对于复合节点，尝试求值显示结果
    if graph_node.type == "composite":
        fallback = f"[{graph_node.label or '复合节点'}]"
        try:
            doc = collect_document(canvas)
            dag = compile_graph(doc)
            if not dag.nodes:
                return fallback
            res = evaluate_graph(dag, {})
            # 复合节点展开后，其子图输出节点的值在 node_values 中
            # 键格式为 {node_id}.{子图内节点id}
            for sub in dag.subgraphs.values():
                for out_def in sub.outputs.values():
                    expanded_key = f"{node_id}.{out_def.node}"
                    val = res.node_values.get(expanded_key)
                    if val is not None:
                        return f"{val:.6f}" if isinstance(val, float) else str(val)
            return fallback
        except Exception:
            return fallback

    # 对于计算节点（binary/unary/condition），尝试求值
    try:
        doc = collect_document(canvas)
        dag = compile_graph(doc)
        if not dag.nodes:
            return "—"
        res = evaluate_graph(dag, {})
        val = res.node_values.get(node_id)
        if val is not None:
            return f"{val:.6f}" if isinstance(val, float) else str(val)
        val = res.outputs.get(node_id)
        return f"{val:.6f}" if val is not None else "—"
    except Exception as e:
        err_msg = str(e)
        if len(err_msg) > 60:
            err_msg = err_msg[:57] + "..."
        return f"错误: {err_msg}"
