#!/usr/bin/env python3
"""DAG schema 定义：数据类与图校验。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from .errors import DAGCompileError

_VALID_VAR_TYPES = frozenset({"float", "int", "bool", "str"})
_VALID_VAR_SOURCES = frozenset({"character", "weapon", "equipment", "enemy", "user_input", "computed"})
_VALID_UNARY_OPS = frozenset({"neg", "floor", "ceil", "abs", "sqrt"})
_VALID_BINARY_OPS = frozenset({"+", "-", "*", "/", "^", "min", "max"})
_VALID_NODE_TYPES = frozenset({"const", "var", "unary", "binary", "condition", "expr", "user_input", "call"})


@dataclass
class DAGVariable:
    """外部变量声明。"""
    type: str
    source: str
    description: str = ""
    default: float | int | bool | str | None = None
    min: float | None = None
    max: float | None = None


@dataclass
class ConstNode:
    """常量节点。"""
    type: Literal["const"] = "const"
    value: float = 0.0
    label: str = ""
    description: str = ""


@dataclass
class VarNode:
    """变量引用节点。"""
    type: Literal["var"] = "var"
    path: str = ""
    label: str = ""
    description: str = ""


@dataclass
class UnaryNode:
    """一元运算节点。"""
    type: Literal["unary"] = "unary"
    op: str = ""
    input: str = ""
    label: str = ""
    description: str = ""


@dataclass
class BinaryNode:
    """二元运算节点。"""
    type: Literal["binary"] = "binary"
    op: str = ""
    lhs: str = ""
    rhs: str = ""
    label: str = ""
    description: str = ""


@dataclass
class ConditionNode:
    """条件分支节点。"""
    type: Literal["condition"] = "condition"
    cond: str = ""
    true_val: str = ""
    false_val: str = ""
    label: str = ""
    description: str = ""


@dataclass
class ExprNode:
    """内联表达式节点。"""
    type: Literal["expr"] = "expr"
    expr: str = ""
    inputs: dict[str, str] = field(default_factory=dict)
    label: str = ""
    description: str = ""


@dataclass
class UserInputNode:
    """GUI 输入节点。"""
    type: Literal["user_input"] = "user_input"
    default: float = 0.0
    min: float = 0.0
    max: float = 100.0
    step: float = 1.0
    label: str = ""
    description: str = ""


@dataclass
class CallNode:
    """子图调用节点。"""
    type: Literal["call"] = "call"
    subgraph: str = ""
    bindings: dict[str, str] = field(default_factory=dict)
    label: str = ""
    description: str = ""


NodeType = ConstNode | VarNode | UnaryNode | BinaryNode | ConditionNode | ExprNode | UserInputNode | CallNode


@dataclass
class DAGOutput:
    """输出定义。"""
    node: str = ""
    label: str = ""
    format: str = ""
    is_primary: bool = False


@dataclass
class DAGSubgraph:
    """子图定义。"""
    description: str = ""
    parameters: dict[str, DAGVariable] = field(default_factory=dict)
    nodes: dict[str, NodeType] = field(default_factory=dict)
    outputs: dict[str, DAGOutput] = field(default_factory=dict)


@dataclass
class DAGGraph:
    """DAG 公式图。"""
    schema_version: str = "dag-v1"
    name: str = ""
    description: str = ""
    variables: dict[str, DAGVariable] = field(default_factory=dict)
    subgraphs: dict[str, DAGSubgraph] = field(default_factory=dict)
    nodes: dict[str, NodeType] = field(default_factory=dict)
    outputs: dict[str, DAGOutput] = field(default_factory=dict)


def _parse_variable(raw: dict[str, Any], var_path: str, *, allow_no_source: bool = False) -> DAGVariable:
    typ = raw.get("type")
    if not isinstance(typ, str) or typ not in _VALID_VAR_TYPES:
        raise DAGCompileError(f"变量 {var_path} 的 type 无效: {typ!r}")
    source = raw.get("source")
    if source is None and allow_no_source:
        source = "computed"
    if not isinstance(source, str) or source not in _VALID_VAR_SOURCES:
        raise DAGCompileError(f"变量 {var_path} 的 source 无效: {source!r}")
    return DAGVariable(
        type=typ,
        source=source,
        description=str(raw.get("description", "")),
        default=raw.get("default"),
        min=raw.get("min"),
        max=raw.get("max"),
    )


def _parse_node(raw: dict[str, Any]) -> NodeType:
    typ = raw.get("type")
    if not isinstance(typ, str) or typ not in _VALID_NODE_TYPES:
        raise DAGCompileError(f"未知的节点类型: {typ!r}")
    label = str(raw.get("label", ""))
    desc = str(raw.get("description", ""))

    if typ == "const":
        value = raw.get("value")
        if value is None:
            raise DAGCompileError("const 节点缺少 value")
        return ConstNode(value=float(value), label=label, description=desc)

    if typ == "var":
        path = raw.get("path")
        if not isinstance(path, str) or not path:
            raise DAGCompileError("var 节点缺少 path")
        return VarNode(path=path, label=label, description=desc)

    if typ == "unary":
        op = raw.get("op")
        if not isinstance(op, str) or op not in _VALID_UNARY_OPS:
            raise DAGCompileError(f"不支持的 unary op: {op!r}")
        inp = raw.get("input")
        if not isinstance(inp, str) or not inp:
            raise DAGCompileError("unary 节点缺少 input")
        return UnaryNode(op=op, input=inp, label=label, description=desc)

    if typ == "binary":
        op = raw.get("op")
        if not isinstance(op, str) or op not in _VALID_BINARY_OPS:
            raise DAGCompileError(f"不支持的 binary op: {op!r}")
        lhs = raw.get("lhs")
        if not isinstance(lhs, str) or not lhs:
            raise DAGCompileError("binary 节点缺少 lhs")
        rhs = raw.get("rhs")
        if not isinstance(rhs, str) or not rhs:
            raise DAGCompileError("binary 节点缺少 rhs")
        return BinaryNode(op=op, lhs=lhs, rhs=rhs, label=label, description=desc)

    if typ == "condition":
        cond = raw.get("cond")
        if not isinstance(cond, str) or not cond:
            raise DAGCompileError("condition 节点缺少 cond")
        tv = raw.get("true_val")
        if not isinstance(tv, str) or not tv:
            raise DAGCompileError("condition 节点缺少 true_val")
        fv = raw.get("false_val")
        if not isinstance(fv, str) or not fv:
            raise DAGCompileError("condition 节点缺少 false_val")
        return ConditionNode(cond=cond, true_val=tv, false_val=fv, label=label, description=desc)

    if typ == "expr":
        expr = raw.get("expr")
        if not isinstance(expr, str) or not expr:
            raise DAGCompileError("expr 节点缺少 expr")
        inputs = raw.get("inputs")
        parsed_inputs: dict[str, str] = {}
        if isinstance(inputs, dict):
            for k, v in inputs.items():
                if isinstance(k, str) and isinstance(v, str):
                    parsed_inputs[k] = v
        return ExprNode(expr=expr, inputs=parsed_inputs, label=label, description=desc)

    if typ == "user_input":
        default = float(raw.get("default", 0))
        min_val = float(raw.get("min", 0))
        max_val = float(raw.get("max", 100))
        step = float(raw.get("step", 1))
        return UserInputNode(default=default, min=min_val, max=max_val, step=step, label=label, description=desc)

    if typ == "call":
        subgraph = raw.get("subgraph")
        if not isinstance(subgraph, str) or not subgraph:
            raise DAGCompileError("call 节点缺少 subgraph")
        bindings = raw.get("bindings")
        parsed_bindings: dict[str, str] = {}
        if isinstance(bindings, dict):
            for k, v in bindings.items():
                if isinstance(k, str) and isinstance(v, str):
                    parsed_bindings[k] = v
        return CallNode(subgraph=subgraph, bindings=parsed_bindings, label=label, description=desc)

    raise DAGCompileError(f"未处理的节点类型: {typ}")


def _parse_output(raw: dict[str, Any]) -> DAGOutput:
    node = raw.get("node")
    if not isinstance(node, str) or not node:
        raise DAGCompileError("output 缺少 node")
    label = raw.get("label")
    if not isinstance(label, str) or not label:
        raise DAGCompileError("output 缺少 label")
    format_spec = str(raw.get("format", ""))
    is_primary = bool(raw.get("is_primary", False))
    return DAGOutput(node=node, label=label, format=format_spec, is_primary=is_primary)


def _parse_subgraph(raw: dict[str, Any]) -> DAGSubgraph:
    desc = str(raw.get("description", ""))
    params_raw = raw.get("parameters")
    params: dict[str, DAGVariable] = {}
    if isinstance(params_raw, dict):
        for pname, pval in params_raw.items():
            if isinstance(pval, dict):
                params[pname] = _parse_variable(pval, pname, allow_no_source=True)

    nodes_raw = raw.get("nodes")
    nodes: dict[str, NodeType] = {}
    if isinstance(nodes_raw, dict):
        for nid, ndef in nodes_raw.items():
            if isinstance(ndef, dict):
                nodes[nid] = _parse_node(ndef)

    outputs_raw = raw.get("outputs")
    outputs: dict[str, DAGOutput] = {}
    if isinstance(outputs_raw, dict):
        for oid, odef in outputs_raw.items():
            if isinstance(odef, dict):
                outputs[oid] = _parse_output(odef)

    _validate_references(nodes, {}, set(params.keys()))

    return DAGSubgraph(description=desc, parameters=params, nodes=nodes, outputs=outputs)


def _collect_node_refs(node: NodeType) -> list[str]:
    """收集某节点引用的所有其他节点 ID。"""
    refs: list[str] = []
    if isinstance(node, UnaryNode):
        refs.append(node.input)
    elif isinstance(node, BinaryNode):
        refs.extend([node.lhs, node.rhs])
    elif isinstance(node, ConditionNode):
        refs.extend([node.cond, node.true_val, node.false_val])
    elif isinstance(node, ExprNode):
        refs.extend(node.inputs.values())
    elif isinstance(node, CallNode):
        refs.extend(node.bindings.values())
    return refs


def _validate_references(nodes: dict[str, NodeType], subgraphs: dict[str, DAGSubgraph], params: set[str] | None = None) -> None:
    known_params = params or set()
    for nid, node in nodes.items():
        refs = _collect_node_refs(node)
        for ref in refs:
            if ref in nodes:
                continue
            if ref in known_params:
                continue
            if "." in ref:
                call_id = ref.split(".")[0]
                if call_id in nodes and isinstance(nodes[call_id], CallNode):
                    continue
            raise DAGCompileError(f"节点 {nid} 引用了不存在的节点: {ref}")


def validate_graph(raw: dict[str, Any]) -> DAGGraph:
    """校验并解析 DAG JSON 字典为 DAGGraph。

    Raises:
        DAGCompileError: 任何 schema 违规
    """
    if not isinstance(raw, dict):
        raise DAGCompileError("DAG 配置必须是字典")

    schema_version = raw.get("schema_version")
    if schema_version != "dag-v1":
        raise DAGCompileError(f"不支持的 schema_version: {schema_version!r}，需要 'dag-v1'")

    name = raw.get("name")
    if not isinstance(name, str) or not name:
        raise DAGCompileError("缺少 name")

    description = str(raw.get("description", ""))

    variables_raw = raw.get("variables")
    variables: dict[str, DAGVariable] = {}
    if isinstance(variables_raw, dict):
        for vpath, vdef in variables_raw.items():
            if isinstance(vdef, dict):
                variables[vpath] = _parse_variable(vdef, vpath)

    subgraphs_raw = raw.get("subgraphs")
    subgraphs: dict[str, DAGSubgraph] = {}
    if isinstance(subgraphs_raw, dict):
        for sid, sdef in subgraphs_raw.items():
            if isinstance(sdef, dict):
                subgraphs[sid] = _parse_subgraph(sdef)

    nodes_raw = raw.get("nodes")
    if not isinstance(nodes_raw, dict) or not nodes_raw:
        raise DAGCompileError("缺少 nodes 或 nodes 为空")

    nodes: dict[str, NodeType] = {}
    for nid, ndef in nodes_raw.items():
        if isinstance(ndef, dict):
            nodes[nid] = _parse_node(ndef)
    if not nodes:
        raise DAGCompileError("nodes 为空")

    _validate_references(nodes, subgraphs)

    for nid, node in nodes.items():
        if isinstance(node, VarNode):
            if node.path not in variables:
                raise DAGCompileError(f"var 节点 {nid} 引用了未声明的变量: {node.path}")
        if isinstance(node, CallNode):
            if node.subgraph not in subgraphs:
                raise DAGCompileError(f"call 节点 {nid} 引用了不存在的子图: {node.subgraph}")

    outputs_raw = raw.get("outputs")
    if not isinstance(outputs_raw, dict):
        raise DAGCompileError("缺少 outputs")

    outputs: dict[str, DAGOutput] = {}
    for oid, odef in outputs_raw.items():
        if isinstance(odef, dict):
            out = _parse_output(odef)
            ref_node = out.node
            if "." in ref_node:
                base = ref_node.split(".")[0]
            else:
                base = ref_node
            if base not in nodes:
                raise DAGCompileError(f"output {oid} 引用了不存在的节点: {ref_node}")
            outputs[oid] = out

    return DAGGraph(
        schema_version=schema_version,
        name=name,
        description=description,
        variables=variables,
        subgraphs=subgraphs,
        nodes=nodes,
        outputs=outputs,
    )
