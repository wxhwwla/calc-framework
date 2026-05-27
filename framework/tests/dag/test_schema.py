#!/usr/bin/env python3
"""DAG schema 定义与校验单元测试。"""

import pytest

from calc_framework.dag.errors import DAGCompileError
from calc_framework.dag.schema import (
    DAGVariable,
    ConstNode,
    VarNode,
    UnaryNode,
    BinaryNode,
    ConditionNode,
    ExprNode,
    UserInputNode,
    CallNode,
    validate_graph,
)


_MINIMAL_GRAPH: dict = {
    "schema_version": "dag-v1",
    "name": "最小测试图",
    "variables": {
        "x": {"type": "float", "source": "computed"},
    },
    "nodes": {
        "x_node": {"type": "var", "path": "x"},
        "result": {"type": "binary", "op": "+", "lhs": "x_node", "rhs": "x_node"},
    },
    "outputs": {
        "sum": {"node": "result", "label": "和"},
    },
}


class TestValidateMinimalGraph:
    """最小合法图。"""

    def test_minimal_graph_valid(self) -> None:
        g = validate_graph(_MINIMAL_GRAPH)
        assert g.name == "最小测试图"
        assert g.schema_version == "dag-v1"
        assert len(g.nodes) == 2
        assert len(g.outputs) == 1

    def test_missing_schema_version_rejected(self) -> None:
        bad = {**{k: v for k, v in _MINIMAL_GRAPH.items() if k != "schema_version"}}
        with pytest.raises(DAGCompileError, match="schema_version"):
            validate_graph(bad)

    def test_wrong_schema_version_rejected(self) -> None:
        bad = {**_MINIMAL_GRAPH, "schema_version": "dag-v0"}
        with pytest.raises(DAGCompileError, match="schema_version"):
            validate_graph(bad)

    def test_missing_name_rejected(self) -> None:
        bad = {**{k: v for k, v in _MINIMAL_GRAPH.items() if k != "name"}}
        with pytest.raises(DAGCompileError, match="name"):
            validate_graph(bad)

    def test_missing_nodes_rejected(self) -> None:
        bad = {**{k: v for k, v in _MINIMAL_GRAPH.items() if k != "nodes"}}
        with pytest.raises(DAGCompileError, match="nodes"):
            validate_graph(bad)

    def test_empty_nodes_rejected(self) -> None:
        bad = {**_MINIMAL_GRAPH, "nodes": {}}
        with pytest.raises(DAGCompileError, match="nodes"):
            validate_graph(bad)

    def test_missing_outputs_rejected(self) -> None:
        bad = {**{k: v for k, v in _MINIMAL_GRAPH.items() if k != "outputs"}}
        with pytest.raises(DAGCompileError, match="outputs"):
            validate_graph(bad)

    def test_output_refs_unknown_node_rejected(self) -> None:
        bad = {**_MINIMAL_GRAPH, "outputs": {"bad": {"node": "nonexistent", "label": "x"}}}
        with pytest.raises(DAGCompileError, match="nonexistent"):
            validate_graph(bad)


class TestNodeTypes:
    """各类节点的解析与校验。"""

    def test_const_node(self) -> None:
        g = validate_graph({
            "schema_version": "dag-v1",
            "name": "const test",
            "nodes": {"c": {"type": "const", "value": 42}},
            "outputs": {"x": {"node": "c", "label": "x"}},
        })
        node = g.nodes["c"]
        assert isinstance(node, ConstNode)
        assert node.value == 42.0

    def test_var_node(self) -> None:
        g = validate_graph({
            "schema_version": "dag-v1",
            "name": "var test",
            "variables": {"角色.力量": {"type": "float", "source": "character"}},
            "nodes": {"v": {"type": "var", "path": "角色.力量"}},
            "outputs": {"x": {"node": "v", "label": "x"}},
        })
        node = g.nodes["v"]
        assert isinstance(node, VarNode)
        assert node.path == "角色.力量"

    def test_var_node_path_not_declared_rejected(self) -> None:
        with pytest.raises(DAGCompileError, match="未声明"):
            validate_graph({
                "schema_version": "dag-v1",
                "name": "bad var",
                "nodes": {"v": {"type": "var", "path": "角色.力量"}},
                "outputs": {"x": {"node": "v", "label": "x"}},
            })

    def test_unary_node(self) -> None:
        g = validate_graph({
            "schema_version": "dag-v1",
            "name": "unary test",
            "variables": {"a": {"type": "float", "source": "computed"}},
            "nodes": {
                "a_node": {"type": "var", "path": "a"},
                "u": {"type": "unary", "op": "floor", "input": "a_node"},
            },
            "outputs": {"x": {"node": "u", "label": "x"}},
        })
        node = g.nodes["u"]
        assert isinstance(node, UnaryNode)
        assert node.op == "floor"

    def test_unary_invalid_op_rejected(self) -> None:
        with pytest.raises(DAGCompileError, match="不支持"):
            validate_graph({
                "schema_version": "dag-v1",
                "name": "bad unary",
                "variables": {"a": {"type": "float", "source": "computed"}},
                "nodes": {
                    "a_node": {"type": "var", "path": "a"},
                    "u": {"type": "unary", "op": "sin", "input": "a_node"},
                },
                "outputs": {"x": {"node": "u", "label": "x"}},
            })

    def test_binary_node(self) -> None:
        g = validate_graph({
            "schema_version": "dag-v1",
            "name": "binary test",
            "variables": {"a": {"type": "float", "source": "computed"}},
            "nodes": {
                "a1": {"type": "var", "path": "a"},
                "a2": {"type": "var", "path": "a"},
                "b": {"type": "binary", "op": "+", "lhs": "a1", "rhs": "a2"},
            },
            "outputs": {"x": {"node": "b", "label": "x"}},
        })
        node = g.nodes["b"]
        assert isinstance(node, BinaryNode)
        assert node.op == "+"

    def test_binary_invalid_op_rejected(self) -> None:
        with pytest.raises(DAGCompileError, match="不支持"):
            validate_graph({
                "schema_version": "dag-v1",
                "name": "bad binary",
                "variables": {"a": {"type": "float", "source": "computed"}},
                "nodes": {
                    "a1": {"type": "var", "path": "a"},
                    "a2": {"type": "var", "path": "a"},
                    "b": {"type": "binary", "op": "%", "lhs": "a1", "rhs": "a2"},
                },
                "outputs": {"x": {"node": "b", "label": "x"}},
            })

    def test_binary_missing_lhs_rejected(self) -> None:
        with pytest.raises(DAGCompileError, match="lhs"):
            validate_graph({
                "schema_version": "dag-v1",
                "name": "bad binary",
                "variables": {"a": {"type": "float", "source": "computed"}},
                "nodes": {
                    "a1": {"type": "var", "path": "a"},
                    "b": {"type": "binary", "op": "+", "rhs": "a1"},
                },
                "outputs": {"x": {"node": "b", "label": "x"}},
            })

    def test_condition_node(self) -> None:
        g = validate_graph({
            "schema_version": "dag-v1",
            "name": "condition test",
            "variables": {"a": {"type": "float", "source": "computed"}},
            "nodes": {
                "cond": {"type": "var", "path": "a"},
                "true_val": {"type": "const", "value": 100},
                "false_val": {"type": "const", "value": 0},
                "branch": {"type": "condition", "cond": "cond", "true_val": "true_val", "false_val": "false_val"},
            },
            "outputs": {"x": {"node": "branch", "label": "x"}},
        })
        node = g.nodes["branch"]
        assert isinstance(node, ConditionNode)

    def test_expr_node(self) -> None:
        g = validate_graph({
            "schema_version": "dag-v1",
            "name": "expr test",
            "nodes": {
                "e": {"type": "expr", "expr": "1 + 2", "inputs": {}},
            },
            "outputs": {"x": {"node": "e", "label": "x"}},
        })
        node = g.nodes["e"]
        assert isinstance(node, ExprNode)
        assert node.expr == "1 + 2"

    def test_user_input_node(self) -> None:
        g = validate_graph({
            "schema_version": "dag-v1",
            "name": "user_input test",
            "nodes": {
                "ui": {"type": "user_input", "default": 0, "min": 0, "max": 100},
            },
            "outputs": {"x": {"node": "ui", "label": "x"}},
        })
        node = g.nodes["ui"]
        assert isinstance(node, UserInputNode)
        assert node.default == 0.0

    def test_call_node(self) -> None:
        g = validate_graph({
            "schema_version": "dag-v1",
            "name": "call test",
            "subgraphs": {
                "double": {
                    "parameters": {"val": {"type": "float"}},
                    "nodes": {
                        "two": {"type": "const", "value": 2},
                        "result": {"type": "binary", "op": "*", "lhs": "val", "rhs": "two"},
                    },
                    "outputs": {"doubled": {"node": "result", "label": "x2"}},
                },
            },
            "nodes": {
                "in_val": {"type": "const", "value": 5},
                "call_double": {
                    "type": "call",
                    "subgraph": "double",
                    "bindings": {"val": "in_val"},
                },
            },
            "outputs": {
                "main_out": {"node": "call_double.doubled", "label": "结果"},
            },
        })
        node = g.nodes["call_double"]
        assert isinstance(node, CallNode)
        assert node.subgraph == "double"


class TestVariables:
    """变量区校验。"""

    def test_variable_with_all_fields(self) -> None:
        g = validate_graph({
            "schema_version": "dag-v1",
            "name": "var fields",
            "variables": {
                "角色.攻击": {
                    "type": "float",
                    "source": "character",
                    "description": "角色基础攻击",
                    "default": 0,
                    "min": 0,
                    "max": 9999,
                },
            },
            "nodes": {"v": {"type": "var", "path": "角色.攻击"}},
            "outputs": {"x": {"node": "v", "label": "x"}},
        })
        var = g.variables["角色.攻击"]
        assert isinstance(var, DAGVariable)
        assert var.type == "float"
        assert var.source == "character"
        assert var.default == 0.0

    def test_variable_invalid_type_rejected(self) -> None:
        with pytest.raises(DAGCompileError, match="type"):
            validate_graph({
                "schema_version": "dag-v1",
                "name": "bad var type",
                "variables": {"x": {"type": "unknown", "source": "computed"}},
                "nodes": {"v": {"type": "var", "path": "x"}},
                "outputs": {"o": {"node": "v", "label": "o"}},
            })

    def test_variable_invalid_source_rejected(self) -> None:
        with pytest.raises(DAGCompileError, match="source"):
            validate_graph({
                "schema_version": "dag-v1",
                "name": "bad var source",
                "variables": {"x": {"type": "float", "source": "invalid_source"}},
                "nodes": {"v": {"type": "var", "path": "x"}},
                "outputs": {"o": {"node": "v", "label": "o"}},
            })


class TestSubgraphValidation:
    """子图校验。"""

    def test_subgraph_params_type_enforced(self) -> None:
        with pytest.raises(DAGCompileError, match="type"):
            validate_graph({
                "schema_version": "dag-v1",
                "name": "bad subgraph",
                "subgraphs": {
                    "sub": {
                        "parameters": {"p": {}},
                        "nodes": {},
                        "outputs": {},
                    },
                },
                "nodes": {},
                "outputs": {},
            })


class TestNodeReferenceValidation:
    """节点引用校验。"""

    def test_unary_input_missing(self) -> None:
        with pytest.raises(DAGCompileError, match="nonexistent"):
            validate_graph({
                "schema_version": "dag-v1",
                "name": "bad ref",
                "variables": {"a": {"type": "float", "source": "computed"}},
                "nodes": {
                    "a_node": {"type": "var", "path": "a"},
                    "u": {"type": "unary", "op": "floor", "input": "nonexistent"},
                },
                "outputs": {"x": {"node": "u", "label": "x"}},
            })

    def test_binary_lhs_missing(self) -> None:
        with pytest.raises(DAGCompileError, match="nonexistent"):
            validate_graph({
                "schema_version": "dag-v1",
                "name": "bad ref",
                "variables": {"a": {"type": "float", "source": "computed"}},
                "nodes": {
                    "a_node": {"type": "var", "path": "a"},
                    "b": {"type": "binary", "op": "+", "lhs": "nonexistent", "rhs": "a_node"},
                },
                "outputs": {"x": {"node": "b", "label": "x"}},
            })

    def test_condition_cond_missing(self) -> None:
        with pytest.raises(DAGCompileError, match="nonexistent"):
            validate_graph({
                "schema_version": "dag-v1",
                "name": "bad cond",
                "variables": {"a": {"type": "float", "source": "computed"}},
                "nodes": {
                    "t": {"type": "const", "value": 1},
                    "f": {"type": "const", "value": 0},
                    "c": {"type": "condition", "cond": "nonexistent", "true_val": "t", "false_val": "f"},
                },
                "outputs": {"x": {"node": "c", "label": "x"}},
            })

    def test_expr_inputs_missing(self) -> None:
        with pytest.raises(DAGCompileError, match="nonexistent"):
            validate_graph({
                "schema_version": "dag-v1",
                "name": "bad expr",
                "nodes": {
                    "e": {"type": "expr", "expr": "1 + x", "inputs": {"x": "nonexistent"}},
                },
                "outputs": {"o": {"node": "e", "label": "o"}},
            })

    def test_call_bindings_missing(self) -> None:
        with pytest.raises(DAGCompileError, match="nonexistent"):
            validate_graph({
                "schema_version": "dag-v1",
                "name": "bad call",
                "subgraphs": {
                    "sub": {
                        "parameters": {"p": {"type": "float"}},
                        "nodes": {"r": {"type": "const", "value": 1}},
                        "outputs": {"o": {"node": "r", "label": "o"}},
                    },
                },
                "nodes": {
                    "caller": {"type": "call", "subgraph": "sub", "bindings": {"p": "nonexistent"}},
                },
                "outputs": {"o": {"node": "caller.o", "label": "o"}},
            })

    def test_call_subgraph_not_defined(self) -> None:
        with pytest.raises(DAGCompileError, match="不存在"):
            validate_graph({
                "schema_version": "dag-v1",
                "name": "bad call sub",
                "nodes": {
                    "v": {"type": "const", "value": 1},
                    "caller": {"type": "call", "subgraph": "missing_sub", "bindings": {}},
                },
                "outputs": {"o": {"node": "v", "label": "o"}},
            })


class TestOutputs:
    """输出区校验。"""

    def test_output_is_primary_default(self) -> None:
        g = validate_graph({
            "schema_version": "dag-v1",
            "name": "output test",
            "nodes": {"c": {"type": "const", "value": 1}},
            "outputs": {"o": {"node": "c", "label": "输出"}},
        })
        out = g.outputs["o"]
        assert out.is_primary is False

    def test_output_is_primary_true(self) -> None:
        g = validate_graph({
            "schema_version": "dag-v1",
            "name": "output test",
            "nodes": {"c": {"type": "const", "value": 1}},
            "outputs": {"o": {"node": "c", "label": "主输出", "is_primary": True}},
        })
        out = g.outputs["o"]
        assert out.is_primary is True

    def test_output_missing_label_rejected(self) -> None:
        with pytest.raises(DAGCompileError, match="label"):
            validate_graph({
                "schema_version": "dag-v1",
                "name": "bad output",
                "nodes": {"c": {"type": "const", "value": 1}},
                "outputs": {"o": {"node": "c"}},
            })

    def test_output_node_missing_rejected(self) -> None:
        with pytest.raises(DAGCompileError, match="node"):
            validate_graph({
                "schema_version": "dag-v1",
                "name": "bad output",
                "nodes": {"c": {"type": "const", "value": 1}},
                "outputs": {"o": {"label": "x"}},
            })


class TestUnknownNodeType:
    """未知节点类型。"""

    def test_unknown_type_rejected(self) -> None:
        with pytest.raises(DAGCompileError, match="未知的节点类型"):
            validate_graph({
                "schema_version": "dag-v1",
                "name": "bad type",
                "nodes": {"x": {"type": "made_up_type"}},
                "outputs": {"o": {"node": "x", "label": "x"}},
            })
