#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""DAG 图算法：拓扑排序与节点工具函数。"""

from __future__ import annotations

from collections import Counter, deque
from typing import Any

from calc_framework.logging import get_logger

from .errors import DAGCycleError
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

logger = get_logger(__name__)


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

    orig_in_degree = dict(in_degree)
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
        logger.error("检测到循环依赖: %s", remaining)
        raise DAGCycleError(f"循环依赖: {remaining}")

    degree_dist = Counter(orig_in_degree.values())
    dist_desc = ", ".join(f"入度={k} × {v}" for k, v in sorted(degree_dist.items()))
    logger.info("拓扑排序: %d 个节点 (%s)", len(order), dist_desc)
    logger.debug("执行顺序: %s", order)
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


def _node_display(node: NodeType) -> str:
    """返回节点的可读描述（用于日志）。"""
    if isinstance(node, ConstNode):
        return f"Const({node.value})"
    if isinstance(node, VarNode):
        return f"Var({node.path})"
    if isinstance(node, UserInputNode):
        return f"UserInput(default={node.default})"
    if isinstance(node, UnaryNode):
        return f"Unary({node.op}, input={node.input})"
    if isinstance(node, BinaryNode):
        return f"Binary({node.op}, lhs={node.lhs}, rhs={node.rhs})"
    if isinstance(node, ConditionNode):
        return f"Condition(cond={node.cond})"
    if isinstance(node, ExprNode):
        return f"Expr({node.expr}, inputs={dict(node.inputs)})"
    return type(node).__name__


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
