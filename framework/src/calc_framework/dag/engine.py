#!/usr/bin/env python3
"""DAG 求值引擎：拓扑排序 + 节点求值。"""

from __future__ import annotations

import math
import operator as op
import time
from collections import Counter, deque
from dataclasses import dataclass, field
from typing import Any

from .errors import DAGCycleError, DAGRuntimeError
from .sandbox import evaluate as sandbox_evaluate
from .sandbox import parse_expr
from .schema import (
    BinaryNode,
    CallNode,
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
from calc_framework.logging import get_logger

logger = get_logger(__name__)

_BINARY_OPS: dict[str, Any] = {
    "+": op.add,
    "-": op.sub,
    "*": op.mul,
    "/": op.truediv,
    "^": pow,
    "min": min,
    "max": max,
    "mod": lambda a, b: a % b if b != 0 else 0.0,
}

_UNARY_OPS: dict[str, Any] = {
    "neg": op.neg,
    "floor": lambda x: float(int(x) if x >= 0 else int(x) - 1),
    "ceil": lambda x: float(int(x) + 1 if x > int(x) else int(x)),
    "abs": abs,
    "sqrt": lambda x: float(x ** 0.5),
    "ln": math.log,
    "log10": math.log10,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
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


def _log_node_failure(logger_obj: Any, nid: str, node: NodeType, values: dict[str, float], exc: Exception) -> None:
    """记录节点求值失败的详细上下文。"""
    detail = _node_display(node)
    available = {k: v for k, v in values.items() if k in _node_dependencies(node)}
    logger_obj.error("节点 %s 求值失败: %s | 可用输入: %s | 错误: %s",
                     nid, detail, available, exc)


def _eval_single_node(node: NodeType, values: dict[str, float], context: dict[str, Any]) -> float:
    """求值单个节点，依赖节点的值已在 values 中。"""
    if isinstance(node, ConstNode):
        return node.value
    if isinstance(node, VarNode):
        val = _resolve_path(context, node.path)
        if val is None:
            logger.warning("变量 %s 未在上下文中找到（将使用默认值）", node.path)
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
            logger.warning("节点 %s 除零错误 (lhs=%s, rhs=%s)", node.label or node.op, lhs, rhs)
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


# ── Block-level caching ─────────────────────────────────


@dataclass
class BlockCacheEntry:
    """单块的缓存条目。"""
    input_hash: int
    outputs: dict[str, float]


class BlockCache:
    """块级缓存 — 跟踪每个块的输入签名和输出值。

    当块的输入值未变化时，跳过块内求值，直接使用缓存输出。
    """

    def __init__(self) -> None:
        self._blocks: dict[str, BlockCacheEntry] = {}

    def get(self, block_id: str, bound_inputs: dict[str, float]) -> dict[str, float] | None:
        sig = _compute_input_hash(bound_inputs)
        entry = self._blocks.get(block_id)
        if entry is not None and entry.input_hash == sig:
            return dict(entry.outputs)
        return None

    def put(self, block_id: str, bound_inputs: dict[str, float], outputs: dict[str, float]) -> None:
        self._blocks[block_id] = BlockCacheEntry(
            input_hash=_compute_input_hash(bound_inputs),
            outputs=dict(outputs),
        )

    def invalidate(self, block_id: str) -> None:
        self._blocks.pop(block_id, None)

    def invalidate_all(self) -> None:
        self._blocks.clear()


def _compute_input_hash(inputs: dict[str, float]) -> int:
    return hash(tuple(sorted(inputs.items())))


def _compute_block_inputs(
    graph: DAGGraph,
    context: dict[str, Any],
) -> dict[str, dict[str, float]]:
    """预计算各块调用节点的输入值（用于缓存键）。

    只解析可直接从 context 或 const 节点获取的输入；
    依赖其他块输出的输入无法在此阶段确定。
    """
    result: dict[str, dict[str, float]] = {}
    for nid, node in graph.nodes.items():
        if not isinstance(node, CallNode):
            continue
        inputs: dict[str, float] = {}
        for param_name, source_nid in node.bindings.items():
            source_node = graph.nodes.get(source_nid)
            if isinstance(source_node, ConstNode):
                inputs[param_name] = source_node.value
            elif isinstance(source_node, VarNode):
                val = _resolve_path(context, source_node.path)
                if val is not None:
                    inputs[param_name] = float(val)
        if inputs:
            result[nid] = inputs
    return result


def _build_block_membership(expanded: DAGGraph, graph: DAGGraph) -> dict[str, set[str]]:
    """构建块 ID → 展开后节点 ID 集合的映射。"""
    result: dict[str, set[str]] = {}
    for nid, node in graph.nodes.items():
        if not isinstance(node, CallNode):
            continue
        prefix = f"{nid}."
        members = {eid for eid in expanded.nodes if eid.startswith(prefix)}
        result[nid] = members
    return result


def _resolve_block_outputs(
    graph: DAGGraph,
    expanded: DAGGraph,
    block_id: str,
    values: dict[str, float],
) -> dict[str, float]:
    """从求值结果中提取块的输出值。"""
    node = graph.nodes.get(block_id)
    if not isinstance(node, CallNode):
        return {}
    sub = graph.subgraphs.get(node.subgraph)
    if sub is None:
        return {}
    outputs: dict[str, float] = {}
    for oid, odef in sub.outputs.items():
        expanded_id = f"{block_id}.{odef.node}"
        if expanded_id in values:
            outputs[oid] = values[expanded_id]
        # Also check ref_map resolution (primary output)
    if not outputs:
        # Fallback: primary output
        primary = _get_primary_output_node(expanded, node, block_id)
        if primary and primary in values:
            outputs["result"] = values[primary]
    return outputs


def _get_primary_output_node(expanded: DAGGraph, call_node: CallNode, call_id: str) -> str | None:
    """获取块的主输出在展开图中的节点 ID。"""
    sub = expanded.subgraphs.get(call_node.subgraph)
    if sub is None:
        return None
    for oid, odef in sub.outputs.items():
        if odef.is_primary:
            return f"{call_id}.{odef.node}"
    # Fallback: first output
    if sub.outputs:
        first_oid = next(iter(sub.outputs))
        return f"{call_id}.{sub.outputs[first_oid].node}"
    return None


def evaluate_graph(
    graph: DAGGraph,
    context: dict[str, Any],
    block_cache: BlockCache | None = None,
) -> DAGResult:
    """展开子图、拓扑排序、求值所有节点，返回结果。

    数据上下文按变量声明的 source 分区，例如:
        context = {"character": {"力量": 100}, "weapon": {"基础攻击": 50}}
    """
    logger.info("开始 DAG 求值: %d 个变量, %d 个输出",
                 len(graph.variables), len(graph.outputs))
    context = _apply_defaults(graph, context)

    # ── Block cache pre-computation ────────────────────
    cached_outputs: dict[str, dict[str, float]] = {}
    cached_primary_nodes: set[str] = set()
    if block_cache is not None:
        block_inputs = _compute_block_inputs(graph, context)
        for block_id, inputs in block_inputs.items():
            cached = block_cache.get(block_id, inputs)
            if cached is not None:
                cached_outputs[block_id] = cached
                logger.debug("块 %s 缓存命中, 跳过求值", block_id)

    expanded = expand_subgraphs(graph)

    # ── Build block membership ─────────────────────────
    block_membership: dict[str, set[str]] = {}
    skip_nodes: set[str] = set()
    if cached_outputs:
        block_membership = _build_block_membership(expanded, graph)
        for block_id in cached_outputs:
            members = block_membership.get(block_id, set())
            skip_nodes.update(members)
            # Resolve primary output node ID
            call_node = graph.nodes.get(block_id)
            if isinstance(call_node, CallNode):
                primary = _get_primary_output_node(expanded, call_node, block_id)
                if primary:
                    cached_primary_nodes.add(primary)

    order = topological_sort(expanded)
    values: dict[str, float] = {}

    # Inject cached primary output values so downstream refs resolve
    for block_id, outputs in cached_outputs.items():
        call_node = graph.nodes.get(block_id)
        if not isinstance(call_node, CallNode):
            continue
        primary = _get_primary_output_node(expanded, call_node, block_id)
        if primary:
            # Use first output value as the block's representative value
            first_val = next(iter(outputs.values()), 0.0)
            values[primary] = first_val
            logger.debug("块 %s 注入缓存输出: %s = %s", block_id, primary, first_val)

    for nid in order:
        if nid in skip_nodes:
            continue
        node = expanded.nodes[nid]
        t0 = time.perf_counter()
        try:
            values[nid] = _eval_single_node(node, values, context)
        except DAGRuntimeError as exc:
            _log_node_failure(logger, nid, node, values, exc)
            raise
        elapsed_ms = (time.perf_counter() - t0) * 1000
        logger.debug("节点 %s [%s] 求值完成: %s (耗时 %.3f ms)",
                     nid, type(node).__name__, values.get(nid, "?"), elapsed_ms)

    outputs: dict[str, float] = {}
    for oid, odef in expanded.outputs.items():
        ref = odef.node
        if ref in values:
            outputs[oid] = values[ref]
        else:
            logger.warning("输出 %s 引用的节点 %s 无求值结果", oid, ref)

    # ── Cache newly evaluated blocks ───────────────────
    if block_cache is not None:
        for block_id, members in block_membership.items():
            if block_id in cached_outputs:
                continue
            block_node = graph.nodes.get(block_id)
            if not isinstance(block_node, CallNode):
                continue
            bound_inputs = _compute_block_inputs(graph, context).get(block_id, {})
            block_outs = _resolve_block_outputs(graph, expanded, block_id, values)
            if block_outs and bound_inputs:
                block_cache.put(block_id, bound_inputs, block_outs)
                logger.debug("块 %s 缓存已更新: %s", block_id, block_outs)
            elif block_outs:
                # Cache even without all inputs resolved
                block_cache.put(block_id, bound_inputs, block_outs)

    logger.info("DAG 求值完成: %d 个输出, %d 个节点执行 (缓存跳过 %d 节点)",
                 len(outputs), len(order) - len(skip_nodes), len(skip_nodes))
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
