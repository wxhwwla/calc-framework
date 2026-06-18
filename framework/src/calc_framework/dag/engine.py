#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""DAG 求值引擎：拓扑排序 + 节点求值。"""

from __future__ import annotations

import math
import operator as op
import time
from dataclasses import dataclass, field
from typing import Any

from calc_framework.logging import get_logger

from .block_cache import (
    BlockCache,
    _build_block_membership,
    _compute_block_inputs,
    _get_primary_output_node,
    _resolve_block_outputs,
)
from .errors import DAGRuntimeError
from .graph import _node_dependencies, _node_display, _resolve_path, topological_sort
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
from .state import (
    DAGState,
    compute_affected_nodes,
    compute_context_hash,
    compute_required_nodes,
    find_changed_paths,
    flatten_context,
    propagate_dirty,
)
from .subgraph import expand_subgraphs

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
    "sqrt": lambda x: float(x**0.5),
    "ln": math.log,
    "log10": math.log10,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
}


@dataclass
class DAGResult:
    """DAG 求值结果。"""

    outputs: dict[str, float] = field(default_factory=dict)

    node_values: dict[str, float] = field(default_factory=dict)

    execution_order: list[str] = field(default_factory=list)


def _log_node_failure(logger_obj: Any, nid: str, node: NodeType, values: dict[str, float], exc: Exception) -> None:
    """记录节点求值失败的详细上下文。"""

    detail = _node_display(node)

    available = {k: v for k, v in values.items() if k in _node_dependencies(node)}

    logger_obj.error("节点 %s 求值失败: %s | 可用输入: %s | 错误: %s", nid, detail, available, exc)


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


def evaluate_graph(
    graph: DAGGraph,
    context: dict[str, Any],
    block_cache: BlockCache | None = None,
    dag_state: DAGState | None = None,
) -> DAGResult:
    """展开子图、拓扑排序、求值所有节点，返回结果。

    支持增量求值（通过 ``dag_state`` 参数保留跨调用状态）：

    - 首次调用传入 ``dag_state=DAGState()``，引擎自动填充状态。

    - 后续调用传入同一状态对象，仅重算上下文变化的节点。

    - 上下文未变化时完全跳过求值（返回缓存结果）。

    支持惰性求值（通过 ``graph`` 的 outputs 定义）：

    - 只求值对输出有贡献的节点，跳过"死节点"。

    数据上下文按变量声明的 source 分区，例如:

        context = {"character": {"力量": 100}, "weapon": {"基础攻击": 50}}

    """

    logger.info("开始 DAG 求值: %d 个变量, %d 个输出", len(graph.variables), len(graph.outputs))

    context = _apply_defaults(graph, context)

    # ── 增量求值：检测上下文变化 ─────────────────────

    incremental_skip: set[str] = set()

    changed_paths: set[str] = set()

    new_context_hash = compute_context_hash(context)

    new_flat_context = flatten_context(context)

    if dag_state is not None and dag_state.context_hash != 0:
        if dag_state.context_hash == new_context_hash:
            logger.debug("增量求值: 上下文未变化, 跳过全部求值")

            dag_state.evaluation_count += 1

            return DAGResult(
                outputs=dict(dag_state.prev_outputs),
                node_values=dict(dag_state.node_values),
                execution_order=list(dag_state.node_values.keys()),
            )

        changed_paths = find_changed_paths(dag_state.prev_flat_context, new_flat_context)

        if changed_paths:
            logger.debug("增量求值: %d 个上下文路径变化", len(changed_paths))

    # ── Block cache pre-computation ────────────────────

    cached_outputs: dict[str, dict[str, float]] = {}

    cached_primary_nodes: set[str] = set()

    re_evaluated_blocks: set[str] = set()

    if block_cache is not None:
        block_inputs = _compute_block_inputs(graph, context)

        block_dependents: dict[str, set[str]] = {}

        for nid, node in graph.nodes.items():
            if not isinstance(node, CallNode):
                continue

            for _param_name, source_nid in node.bindings.items():
                source_node = graph.nodes.get(source_nid)

                if isinstance(source_node, CallNode):
                    block_dependents.setdefault(source_nid, set()).add(nid)

        for block_id, inputs in block_inputs.items():
            cached = block_cache.get(block_id, inputs)

            if cached is not None:
                cached_outputs[block_id] = cached

                logger.debug("块 %s 缓存命中, 跳过求值", block_id)

            else:
                re_evaluated_blocks.add(block_id)

                block_cache.invalidate(block_id)

                to_invalidate = {block_id}

                while to_invalidate:
                    bid = to_invalidate.pop()

                    for dep_id in block_dependents.get(bid, set()):
                        if dep_id not in re_evaluated_blocks:
                            re_evaluated_blocks.add(dep_id)

                            block_cache.invalidate(dep_id)

                            cached_outputs.pop(dep_id, None)

                            to_invalidate.add(dep_id)

    expanded = expand_subgraphs(graph)

    # ── 增量求值：脏节点传播 ───────────────────────────

    if dag_state is not None and dag_state.context_hash != 0 and changed_paths:
        seed = compute_affected_nodes(graph, changed_paths)

        if seed:
            incremental_skip = propagate_dirty(expanded.nodes, seed)

            logger.debug("增量求值: %d 个种子节点 -> %d 个脏节点待重算", len(seed), len(incremental_skip))

    # ── 惰性求值：从展开图的输出引用反向遍历 ──────────

    # 注意：使用展开图(expanded)而非原始图的输出引用，

    # 因为子图展开后节点ID改变（如 block_add → block_add.sum）

    required_nodes: set[str] | None = None

    if expanded.outputs:
        output_refs = {odef.node for odef in expanded.outputs.values()}

        required_nodes = compute_required_nodes(expanded.nodes, output_refs)

        if required_nodes and len(required_nodes) < len(expanded.nodes):
            logger.debug("惰性求值: %d / %d 节点被输出引用", len(required_nodes), len(expanded.nodes))

    # ── Build block membership ─────────────────────────

    block_membership: dict[str, set[str]] = {}

    skip_nodes: set[str] = set()

    if cached_outputs:
        block_membership = _build_block_membership(expanded, graph)

        for block_id in cached_outputs:
            members = block_membership.get(block_id, set())

            skip_nodes.update(members)

            call_node = graph.nodes.get(block_id)

            if isinstance(call_node, CallNode):
                primary = _get_primary_output_node(expanded, call_node, block_id)

                if primary:
                    cached_primary_nodes.add(primary)

    order = topological_sort(expanded)

    values: dict[str, float] = dict(dag_state.node_values) if dag_state is not None else {}

    # Inject cached primary output values so downstream refs resolve

    for block_id, outputs in cached_outputs.items():
        call_node = graph.nodes.get(block_id)

        if not isinstance(call_node, CallNode):
            continue

        primary = _get_primary_output_node(expanded, call_node, block_id)

        if primary:
            first_val = next(iter(outputs.values()), 0.0)

            values[primary] = first_val

            logger.debug("块 %s 注入缓存输出: %s = %s", block_id, primary, first_val)

    evaluated_count = 0

    for nid in order:
        if nid in skip_nodes:
            continue

        if required_nodes is not None and nid not in required_nodes:
            continue

        if incremental_skip and nid not in incremental_skip and nid in values:
            continue

        node = expanded.nodes[nid]

        t0 = time.perf_counter()

        try:
            values[nid] = _eval_single_node(node, values, context)

        except DAGRuntimeError as exc:
            _log_node_failure(logger, nid, node, values, exc)

            raise

        elapsed_ms = (time.perf_counter() - t0) * 1000

        evaluated_count += 1

        logger.debug("节点 %s [%s] 求值完成: %s (耗时 %.3f ms)", nid, type(node).__name__, values.get(nid, "?"), elapsed_ms)

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
                block_cache.put(block_id, bound_inputs, block_outs)

    # ── Update DAGState for next incremental call ──────

    if dag_state is not None:
        dag_state.node_values = dict(values)

        dag_state.prev_outputs = dict(outputs)

        dag_state.prev_flat_context = new_flat_context

        dag_state.context_hash = new_context_hash

        dag_state.evaluation_count += 1

    logger.info(
        "DAG 求值完成: %d 个输出, %d 个节点执行 (跳过 %d 个缓存/惰性节点)",
        len(outputs),
        evaluated_count,
        len(order) - evaluated_count - len(skip_nodes),
    )

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
