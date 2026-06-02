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
    # Nodes
    "BinaryNode",
    "CallNode",
    "ConditionNode",
    "ConstNode",
    "DAGCompileError",
    "DAGCycleError",
    # Errors
    "DAGError",
    # Core types
    "DAGGraph",
    "DAGOutput",
    "DAGResult",
    "DAGRuntimeError",
    "DAGSecurityError",
    # Engine
    "DAGService",
    "DAGState",
    "DAGSubgraph",
    "DAGVariable",
    "ExprNode",
    "UnaryNode",
    "UserInputNode",
    "VarNode",
    "dag_from_dict",
    # Serialization
    "dag_to_dict",
    "evaluate",
    "expand_subgraphs",
    "expand_template_refs",
    "list_functions",
    "list_templates",
    "load_dag",
    "parse_expr",
    # Sandbox
    "register_function",
    # Templates
    "register_template",
    "save_dag",
    "topological_sort",
    "validate_expr",
    "validate_graph",
]
