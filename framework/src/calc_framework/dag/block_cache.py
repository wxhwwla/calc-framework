#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""DAG 块级缓存机制。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .graph import _resolve_path
from .schema import CallNode, ConstNode, DAGGraph, VarNode


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
    """计算输入字典的哈希值。"""
    return hash(tuple(sorted(inputs.items())))


def _compute_block_inputs(
    graph: DAGGraph,
    context: dict[str, Any],
) -> dict[str, dict[str, float]]:
    """预计算各块调用节点的输入值（用于缓存键）。

    解析可直接从 context 或 const 节点获取的输入；
    块到块依赖使用源块 ID 的哈希作为代理。
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
            elif isinstance(source_node, CallNode):
                inputs[param_name] = hash(source_nid)
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
