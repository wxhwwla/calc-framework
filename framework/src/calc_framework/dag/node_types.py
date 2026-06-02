#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""DAG 节点类型定义。"""



from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

_VALID_UNARY_OPS = frozenset({"neg", "floor", "ceil", "abs", "sqrt", "ln", "log10", "sin", "cos", "tan", "asin", "acos", "atan"})

_VALID_BINARY_OPS = frozenset({"+", "-", "*", "/", "^", "min", "max", "mod"})

_VALID_NODE_TYPES = frozenset({"const", "var", "unary", "binary", "condition", "expr", "user_input", "call"})





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





def _collect_node_refs(node: NodeType) -> list[str]:
    """收集某节点引用的所有其他节点 ID（字符串）。内嵌节点直接展开。"""
    refs: list[str] = []

    def _extract(val: str | NodeType) -> None:
        if isinstance(val, str):
            refs.append(val)
        else:
            refs.extend(_collect_node_refs(val))

    if isinstance(node, UnaryNode):
        _extract(node.input)
    elif isinstance(node, BinaryNode):
        _extract(node.lhs)
        _extract(node.rhs)
    elif isinstance(node, ConditionNode):
        _extract(node.cond)
        _extract(node.true_val)
        _extract(node.false_val)
    elif isinstance(node, ExprNode):
        for v in node.inputs.values():
            _extract(v)
    elif isinstance(node, CallNode):
        for v in node.bindings.values():
            _extract(v)
    return refs
