#!/usr/bin/env python3
"""DAG 求值引擎：拓扑排序 + 节点求值。"""

from __future__ import annotations

import operator as op
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from .errors import DAGCycleError, DAGRuntimeError
from .sandbox import evaluate as sandbox_evaluate
from .sandbox import parse_expr
from .schema import (
    BinaryNode,
    ConditionNode,
    ConstNode,
    DAGGraph,
    ExprNode,
    NodeType,
    UnaryNode,
    UserInputNode,
    VarNode,
)
from .subgraph import expand_subgraphs

_BINARY_OPS: dict[str, Any] = {
    "+": op.add,
    "-": op.sub,
    "*": op.mul,
    "/": op.truediv,
    "^": pow,
    "min": min,
    "max": max,
}

_UNARY_OPS: dict[str, Any] = {
    "neg": op.neg,
    "floor": lambda x: float(int(x) if x >= 0 else int(x) - 1),
    "ceil": lambda x: float(int(x) + 1 if x > int(x) else int(x)),
    "abs": abs,
    "sqrt": lambda x: float(x ** 0.5),
}


@dataclass
class DAGResult:
    """DAG 求值结果。"""
    outputs: dict[str, float] = field(default_factory=dict)
    node_values: dict[str, float] = field(default_factory=dict)
    execution_order: list[str] = field(default_factory=list)


def topological_sort(graph: DAGGraph) -> list[str]:
    """对图中的节点做拓扑排序，返回执行顺序。

    Raises:
        DAGCycleError: 存在循环依赖
    """
    in_degree: dict[str, int] = {nid: 0 for nid in graph.nodes}
    adj: dict[str, list[str]] = {nid: [] for nid in graph.nodes}

    for nid, node in graph.nodes.items():
        refs = _node_dependencies(node)
        for ref in refs:
            if ref in adj:
                adj[ref].append(nid)
                in_degree[nid] += 1

    queue: deque[str] = deque(nid for nid, deg in in_degree.items() if deg == 0)
    order: list[str] = []

    while queue:
        nid = queue.popleft()
        order.append(nid)
        for downstream in adj[nid]:
            in_degree[downstream] -= 1
            if in_degree[downstream] == 0:
                queue.append(downstream)

    if len(order) != len(graph.nodes):
        remaining = [nid for nid, deg in in_degree.items() if deg > 0]
        raise DAGCycleError(f"循环依赖: {remaining}")

    return order


def _node_dependencies(node: NodeType) -> list[str]:
    """返回节点的直接依赖节点 ID 列表。"""
    if isinstance(node, UnaryNode):
        return [node.input]
    if isinstance(node, BinaryNode):
        return [node.lhs, node.rhs]
    if isinstance(node, ConditionNode):
        return [node.cond, node.true_val, node.false_val]
    if isinstance(node, ExprNode):
        return list(node.inputs.values())
    return []


def _eval_single_node(node: NodeType, values: dict[str, float], context: dict[str, Any]) -> float:
    """求值单个节点，依赖节点的值已在 values 中。"""
    if isinstance(node, ConstNode):
        return node.value
    if isinstance(node, VarNode):
        val = _resolve_path(context, node.path)
        if val is None:
            raise DAGRuntimeError(f"变量 {node.path} 未在上下文或默认值中找到")
        return float(val)
    if isinstance(node, UserInputNode):
        return node.default
    if isinstance(node, UnaryNode):
        inp = values[node.input]
        fn = _UNARY_OPS.get(node.op)
        if fn is None:
            raise DAGRuntimeError(f"未知一元运算: {node.op}")
        return float(fn(inp))
    if isinstance(node, BinaryNode):
        lhs = values[node.lhs]
        rhs = values[node.rhs]
        fn = _BINARY_OPS.get(node.op)
        if fn is None:
            raise DAGRuntimeError(f"未知二元运算: {node.op}")
        try:
            return float(fn(lhs, rhs))
        except ZeroDivisionError:
            raise DAGRuntimeError(f"节点 {node.label or node.op} 除零错误")
    if isinstance(node, ConditionNode):
        cond_val = values[node.cond]
        if bool(cond_val):
            return values[node.true_val]
        return values[node.false_val]
    if isinstance(node, ExprNode):
        scope = {var_name: values[nid] for var_name, nid in node.inputs.items()}
        tree = parse_expr(node.expr)
        return sandbox_evaluate(tree, scope)
    raise DAGRuntimeError(f"不支持的节点类型: {type(node).__name__}")


def _resolve_path(context: dict[str, Any], path: str) -> Any:
    """按点分隔路径在上下文中取值。"""
    parts = path.split(".")
    cursor: Any = context
    for part in parts:
        if isinstance(cursor, dict):
            cursor = cursor.get(part)
        else:
            return None
        if cursor is None:
            return None
    return cursor


def evaluate_graph(graph: DAGGraph, context: dict[str, Any]) -> DAGResult:
    """展开子图、拓扑排序、求值所有节点，返回结果。

    数据上下文按变量声明的 source 分区，例如:
        context = {"character": {"力量": 100}, "weapon": {"基础攻击": 50}}
    """
    context = _apply_defaults(graph, context)
    expanded = expand_subgraphs(graph)
    order = topological_sort(expanded)
    values: dict[str, float] = {}
    for nid in order:
        node = expanded.nodes[nid]
        values[nid] = _eval_single_node(node, values, context)

    outputs: dict[str, float] = {}
    for oid, odef in expanded.outputs.items():
        ref = odef.node
        if ref in values:
            outputs[oid] = values[ref]

    return DAGResult(
        outputs=outputs,
        node_values=values,
        execution_order=order,
    )


def _apply_defaults(graph: DAGGraph, context: dict[str, Any]) -> dict[str, Any]:
    """将变量声明中的默认值填入上下文（如果上下文中没有对应值）。"""
    result = {}
    for key, section in context.items():
        if isinstance(section, dict):
            result[key] = dict(section)
        else:
            result[key] = section

    for path, var in graph.variables.items():
        if var.default is None:
            continue
        parts = path.split(".")
        if len(parts) != 2:
            continue
        section, field = parts
        if section not in result:
            result[section] = {}
        if isinstance(result[section], dict) and field not in result[section]:
            result[section][field] = var.default

    return result
