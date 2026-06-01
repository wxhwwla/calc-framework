#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""DAG 公式引擎：schema / sandbox / engine / subgraph / serializer / debugger / state。

用法::

    from calc_framework.dag import (
        DAGGraph, DAGVariable, DAGOutput, DAGSubgraph,
        DAGService, DAGResult, DAGState,
        VarNode, BinaryNode, ConstNode, ExprNode,
        dag_to_dict, dag_from_dict, load_dag, save_dag,
    )
"""

from calc_framework.dag.engine import DAGResult, topological_sort
from calc_framework.dag.errors import (
    DAGCompileError,
    DAGCycleError,
    DAGError,
    DAGRuntimeError,
    DAGSecurityError,
)
from calc_framework.dag.sandbox import (
    evaluate,
    list_functions,
    parse_expr,
    register_function,
    validate_expr,
)
from calc_framework.dag.schema import (
    BinaryNode,
    CallNode,
    ConditionNode,
    ConstNode,
    DAGGraph,
    DAGOutput,
    DAGSubgraph,
    DAGVariable,
    ExprNode,
    UnaryNode,
    UserInputNode,
    VarNode,
    validate_graph,
)
from calc_framework.dag.serializer import dag_from_dict, dag_to_dict, load_dag, save_dag
from calc_framework.dag.service import DAGService
from calc_framework.dag.state import DAGState
from calc_framework.dag.subgraph import expand_subgraphs
from calc_framework.dag.templates import (
    expand_template_refs,
    list_templates,
    register_template,
)

__all__ = [
    # Core types
    "DAGGraph",
    "DAGVariable",
    "DAGOutput",
    "DAGSubgraph",
    # Nodes
    "BinaryNode",
    "CallNode",
    "ConditionNode",
    "ConstNode",
    "ExprNode",
    "UnaryNode",
    "UserInputNode",
    "VarNode",
    # Engine
    "DAGService",
    "DAGResult",
    "DAGState",
    "topological_sort",
    "validate_graph",
    "expand_subgraphs",
    # Serialization
    "dag_to_dict",
    "dag_from_dict",
    "load_dag",
    "save_dag",
    # Sandbox
    "register_function",
    "list_functions",
    "parse_expr",
    "validate_expr",
    "evaluate",
    # Templates
    "register_template",
    "list_templates",
    "expand_template_refs",
    # Errors
    "DAGError",
    "DAGCompileError",
    "DAGSecurityError",
    "DAGRuntimeError",
    "DAGCycleError",
]
