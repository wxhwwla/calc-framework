"""GraphCompiler — 将 graph_editor 的 GraphDocument 编译为 DAGGraph。"""

from __future__ import annotations

from typing import Any

from calc_framework.dag.schema import (
    DAGGraph,
    DAGOutput,
    DAGVariable,
    BinaryNode,
    ConditionNode,
    ConstNode,
    UnaryNode,
    UserInputNode,
    VarNode,
)
from calc_framework.graph_editor.schema import (
    GraphDocument,
    GraphEdge,
    GraphNode,
)


def compile_graph(doc: GraphDocument) -> DAGGraph:
    """将可视化编辑器格式编译为 DAG 引擎格式。"""
    # ── 1. 构建端口→节点映射 ──
    # key: (target_node_id, target_port) → source_node_id
    port_inputs: dict[tuple[str, int], str] = {}
    for edge in doc.edges:
        port_inputs[(edge.to_node, edge.to_port)] = edge.from_node

    # 反向映射：source_node → (target_node, target_port)（用于 output 节点回溯）
    source_to_target: dict[str, list[tuple[str, int]]] = {}
    for edge in doc.edges:
        if edge.from_node not in source_to_target:
            source_to_target[edge.from_node] = []
        source_to_target[edge.from_node].append((edge.to_node, edge.to_port))

    # ── 2. 编译非 output 类型的节点 ──
    dag_nodes: dict[str, Any] = {}
    for node in doc.nodes:
        if node.type == "output":
            continue  # output 标记节点不进入 DAG
        dag_n = _compile_single_node(node, port_inputs)
        dag_nodes[node.id] = dag_n

    # ── 3. 编译变量声明 ──
    variables: dict[str, DAGVariable] = {}
    for path_str, raw in doc.external_variables.items():
        variables[path_str] = DAGVariable(
            type=str(raw.get("type", "float")),
            source=str(raw.get("source", "computed")),
            description=str(raw.get("description", "")),
        )
    # 自动发现 var 节点中的路径
    for node in doc.nodes:
        if node.type == "var" and node.config.path:
            if node.config.path not in variables:
                variables[node.config.path] = DAGVariable(type="float", source="computed")

    # ── 4. 编译输出 ──
    outputs: dict[str, DAGOutput] = {}
    for sec in doc.layout.sections:
        for node_id in sec.output_nodes:
            resolved = _resolve_output_node(node_id, port_inputs, doc)
            if resolved and resolved not in outputs:
                src_node = next((n for n in doc.nodes if n.id == node_id), None)
                label = src_node.label if src_node and src_node.label else resolved
                outputs[resolved] = DAGOutput(node=resolved, label=label)

    return DAGGraph(
        schema_version="dag-v1",
        name=doc.name,
        description=doc.description,
        variables=variables,
        nodes=dag_nodes,
        outputs=outputs,
    )


def _resolve_output_node(node_id: str, port_inputs: dict[tuple[str, int], str], doc: GraphDocument) -> str | None:
    """解析输出节点：如果 node_id 对应的是 output 标记节点，则回溯到它的输入源。"""
    src_node = next((n for n in doc.nodes if n.id == node_id), None)
    if src_node is None:
        return None
    if src_node.type != "output":
        return node_id  # 不是标记节点，直接使用
    # output 标记节点 → 找谁连到了它的 port 0
    source = port_inputs.get((node_id, 0))
    return source


def _compile_single_node(node: GraphNode, port_inputs: dict[tuple[str, int], str]) -> Any:
    """编译单个 GraphNode 为 DAG NodeType。"""
    cfg = node.config

    if node.type == "const":
        return ConstNode(value=cfg.value, label=node.label or "常量")

    if node.type == "var":
        return VarNode(path=cfg.path, label=node.label or "变量引用")

    if node.type == "user_input":
        return UserInputNode(
            default=cfg.default, min=cfg.min, max=cfg.max, step=cfg.step,
            label=node.label or "用户输入",
        )

    if node.type == "unary":
        inp = port_inputs.get((node.id, 0), "")
        return UnaryNode(op=node.op or "floor", input=inp, label=node.label or "一元运算")

    if node.type == "binary":
        lhs = port_inputs.get((node.id, 0), "")
        rhs = port_inputs.get((node.id, 1), "")
        return BinaryNode(op=node.op or "+", lhs=lhs, rhs=rhs, label=node.label or "二元运算")

    if node.type == "condition":
        cond = port_inputs.get((node.id, 0), "")
        true_val = port_inputs.get((node.id, 1), "")
        false_val = port_inputs.get((node.id, 2), "")
        return ConditionNode(cond=cond, true_val=true_val, false_val=false_val, label=node.label or "条件分支")

    raise ValueError(f"未知节点类型: {node.type}")
