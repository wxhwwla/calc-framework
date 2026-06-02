#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""DAG 序列化：JSON 文件 ↔ DAGGraph 互转。



模板引用（``"template"`` 字段）在加载时自动展开。"""



from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .schema import (
    BinaryNode,
    CallNode,
    ConditionNode,
    ConstNode,
    DAGGraph,
    DAGSubgraph,
    DAGVariable,
    ExprNode,
    NodeType,
    UnaryNode,
    UserInputNode,
    VarNode,
    validate_graph,
)
from .templates import expand_template_refs


def _variable_to_dict(var: DAGVariable) -> dict[str, Any]:

    """将 DAGVariable 序列化为字典。"""
    d: dict[str, Any] = {"type": var.type, "source": var.source}

    if var.description:

        d["description"] = var.description

    if var.default is not None:

        d["default"] = var.default

    if var.min is not None:

        d["min"] = var.min

    if var.max is not None:

        d["max"] = var.max

    return d





def _ref_to_json(ref: str | NodeType) -> str | dict[str, Any]:
    """将节点引用（字符串节点名或内联节点）转为可 JSON 序列化的值。"""
    if isinstance(ref, str):
        return ref
    return _node_to_dict(ref)


    """将节点序列化为字典。"""
def _node_to_dict(node: NodeType) -> dict[str, Any]:
    base: dict[str, Any] = {}
    if isinstance(node, ConstNode):
        base = {"type": "const", "value": node.value}
    elif isinstance(node, VarNode):
        base = {"type": "var", "path": node.path}
    elif isinstance(node, UnaryNode):
        base = {"type": "unary", "op": node.op, "input": _ref_to_json(node.input)}
    elif isinstance(node, BinaryNode):
        base = {"type": "binary", "op": node.op, "lhs": _ref_to_json(node.lhs), "rhs": _ref_to_json(node.rhs)}
    elif isinstance(node, ConditionNode):
        base = {
            "type": "condition",
            "cond": _ref_to_json(node.cond),
            "true_val": _ref_to_json(node.true_val),
            "false_val": _ref_to_json(node.false_val),
        }
    elif isinstance(node, ExprNode):
        base = {"type": "expr", "expr": node.expr}
        if node.inputs:
            base["inputs"] = dict(node.inputs)
    elif isinstance(node, UserInputNode):
        base = {
            "type": "user_input",
            "default": node.default,
            "min": node.min,
            "max": node.max,
            "step": node.step,
        }
    elif isinstance(node, CallNode):
        base = {"type": "call", "subgraph": node.subgraph}
        if node.bindings:
            base["bindings"] = dict(node.bindings)
    if node.label:
        base["label"] = node.label
    if node.description:
        base["description"] = node.description
    return base





    """将 DAGSubgraph 序列化为字典。"""
def _subgraph_to_dict(sub: DAGSubgraph) -> dict[str, Any]:

    d: dict[str, Any] = {}

    if sub.description:

        d["description"] = sub.description

    d["parameters"] = {k: _variable_to_dict(v) for k, v in sub.parameters.items()}

    d["nodes"] = {k: _node_to_dict(v) for k, v in sub.nodes.items()}

    d["outputs"] = {k: asdict(v) for k, v in sub.outputs.items()}

    return d





def dag_to_dict(graph: DAGGraph) -> dict[str, Any]:

    """将 DAGGraph 转换为可序列化的字典。"""

    d: dict[str, Any] = {

        "schema_version": graph.schema_version,

        "name": graph.name,

    }

    if graph.description:

        d["description"] = graph.description

    if graph.variables:

        d["variables"] = {k: _variable_to_dict(v) for k, v in graph.variables.items()}

    if graph.subgraphs:

        d["subgraphs"] = {k: _subgraph_to_dict(v) for k, v in graph.subgraphs.items()}

    d["nodes"] = {k: _node_to_dict(v) for k, v in graph.nodes.items()}

    d["outputs"] = {k: asdict(v) for k, v in graph.outputs.items()}

    return d





def dag_from_dict(raw: dict[str, Any]) -> DAGGraph:

    """从字典解析并校验 DAGGraph。



    自动展开模板引用节点后再进行校验。

    """

    raw = expand_template_refs(raw)

    return validate_graph(raw)





def load_dag(path: str | Path) -> DAGGraph:

    """从 JSON 文件加载 DAGGraph。"""

    text = Path(path).read_text(encoding="utf-8")

    raw = json.loads(text)

    return dag_from_dict(raw)





def save_dag(graph: DAGGraph, path: str | Path) -> None:

    """将 DAGGraph 保存为 JSON 文件。"""

    d = dag_to_dict(graph)

    text = json.dumps(d, ensure_ascii=False, indent=2)

    Path(path).write_text(text, encoding="utf-8")

