#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""DAG schema 定义：数据类与图校验。

此模块是兼容性入口。类型定义已拆分到:

  - :mod:`calc_framework.dag.node_types` — 节点类型 (ConstNode, VarNode, …)
  - :mod:`calc_framework.dag.graph_types` — 图结构类型 (DAGVariable, DAGGraph, …)

所有符号从此 re-export，现有 ``from calc_framework.dag.schema import …`` 不受影响。
"""

from calc_framework.dag.graph_types import (
    DAGGraph,
    DAGOutput,
    DAGSubgraph,
    DAGVariable,
    validate_graph,
)
from calc_framework.dag.node_types import (
    BinaryNode,
    CallNode,
    ConditionNode,
    ConstNode,
    ExprNode,
    NodeType,
    UnaryNode,
    UserInputNode,
    VarNode,
)

__all__ = [
    "BinaryNode",
    "CallNode",
    "ConditionNode",
    "ConstNode",
    "DAGGraph",
    "DAGOutput",
    "DAGSubgraph",
    "DAGVariable",
    "ExprNode",
    "NodeType",
    "UnaryNode",
    "UserInputNode",
    "VarNode",
    "validate_graph",
]
