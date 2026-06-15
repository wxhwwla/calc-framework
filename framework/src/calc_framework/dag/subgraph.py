#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""子图展开：将 call 节点内联为普通节点。"""

from __future__ import annotations

from copy import deepcopy

from calc_framework.logging import get_logger

from .schema import (
    BinaryNode,
    CallNode,
    ConditionNode,
    DAGGraph,
    DAGOutput,
    ExprNode,
    NodeType,
    UnaryNode,
    VarNode,
)

logger = get_logger(__name__)


def _prefixed_node(node: NodeType, prefix: str) -> NodeType:
    n = deepcopy(node)

    if isinstance(n, UnaryNode):
        n.input = f"{prefix}.{n.input}"

    elif isinstance(n, BinaryNode):
        n.lhs = f"{prefix}.{n.lhs}"

        n.rhs = f"{prefix}.{n.rhs}"

    elif isinstance(n, ConditionNode):
        n.cond = f"{prefix}.{n.cond}"

        n.true_val = f"{prefix}.{n.true_val}"

        n.false_val = f"{prefix}.{n.false_val}"

    elif isinstance(n, ExprNode):
        n.inputs = {k: f"{prefix}.{v}" for k, v in n.inputs.items()}

    elif isinstance(n, CallNode):
        n.bindings = {k: f"{prefix}.{v}" for k, v in n.bindings.items()}

    elif isinstance(n, VarNode):
        n.path = f"{prefix}.{n.path}"

    return n


def _apply_ref_map_to_node(node: NodeType, ref_map: dict[str, str]) -> NodeType:
    def _map(ref: str) -> str:
        visited = set()

        while ref in ref_map:
            if ref in visited:
                break

            visited.add(ref)

            ref = ref_map[ref]

        return ref

    if isinstance(node, UnaryNode):
        node.input = _map(node.input)

    elif isinstance(node, BinaryNode):
        node.lhs = _map(node.lhs)

        node.rhs = _map(node.rhs)

    elif isinstance(node, ConditionNode):
        node.cond = _map(node.cond)

        node.true_val = _map(node.true_val)

        node.false_val = _map(node.false_val)

    elif isinstance(node, ExprNode):
        node.inputs = {k: _map(v) for k, v in node.inputs.items()}

    elif isinstance(node, CallNode):
        node.bindings = {k: _map(v) for k, v in node.bindings.items()}

    elif isinstance(node, VarNode):
        node.path = _map(node.path)

    return node


def expand_subgraphs(graph: DAGGraph) -> DAGGraph:
    logger.debug("开始子图展开: %d 个节点, %d 个子图", len(graph.nodes), len(graph.subgraphs))

    expanded = DAGGraph(
        schema_version=graph.schema_version,
        name=graph.name,
        description=graph.description,
        variables=dict(graph.variables),
        subgraphs=dict(graph.subgraphs),
        nodes={},
        outputs={},
    )

    for nid, node in graph.nodes.items():
        expanded.nodes[nid] = deepcopy(node)

    ref_map: dict[str, str] = {}

    changed = True

    while changed:
        changed = False

        call_items = [(nid, node) for nid, node in expanded.nodes.items() if isinstance(node, CallNode)]

        for call_id, call_node in call_items:
            sub = graph.subgraphs.get(call_node.subgraph)

            if sub is None:
                del expanded.nodes[call_id]

                continue

            changed = True

            del expanded.nodes[call_id]

            for snid, snode in sub.nodes.items():
                prefixed_id = f"{call_id}.{snid}"

                prefixed = _prefixed_node(snode, call_id)

                expanded.nodes[prefixed_id] = prefixed

            for pbinding_name, target_nid in call_node.bindings.items():
                if target_nid:
                    ref_map[f"{call_id}.{pbinding_name}"] = target_nid

            for sub_oid, sub_odef in sub.outputs.items():
                resolved = f"{call_id}.{sub_odef.node}"

                if f"{call_id}.{sub_oid}" != resolved:
                    ref_map[f"{call_id}.{sub_oid}"] = resolved

            primary_outputs = {oid: odef for oid, odef in sub.outputs.items() if odef.is_primary}

            if primary_outputs:
                first_primary = next(iter(primary_outputs.values()))

                call_out = f"{call_id}.{first_primary.node}"

                if call_id != call_out:
                    ref_map[call_id] = call_out

            elif sub.outputs:
                first_output = next(iter(sub.outputs.values()))

                call_out = f"{call_id}.{first_output.node}"

                if call_id != call_out:
                    ref_map[call_id] = call_out

    for node in expanded.nodes.values():
        _apply_ref_map_to_node(node, ref_map)

    _finalize_outputs(expanded, graph, ref_map)

    logger.debug("子图展开完成: %d 个节点, %d 个输出", len(expanded.nodes), len(expanded.outputs))

    return expanded


def _finalize_outputs(expanded: DAGGraph, original: DAGGraph, ref_map: dict[str, str]) -> None:
    new_outputs: dict[str, DAGOutput] = {}

    for oid, odef in original.outputs.items():
        resolved = ref_map.get(odef.node, odef.node)

        if resolved in expanded.nodes:
            new_outputs[oid] = DAGOutput(
                node=resolved,
                label=odef.label,
                is_primary=odef.is_primary,
            )

        else:
            new_outputs[oid] = odef

    expanded.outputs = new_outputs
