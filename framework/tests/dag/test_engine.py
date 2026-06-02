#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""DAG 求值引擎单元测试。"""

import pytestfrom calc_framework.dag.engine import evaluate_graph, topological_sortfrom calc_framework.dag.errors import DAGCycleError, DAGRuntimeErrorfrom calc_framework.dag.serializer import dag_from_dict_SIMPLE_LINEAR: dict = {
    "schema_version": "dag-v1",
    "name": "线性图",
    "variables": {"a": {"type": "float", "source": "computed"}},
    "nodes": {
        "a_node": {"type": "var", "path": "a"},
        "two": {"type": "const", "value": 2},
        "result": {"type": "binary", "op": "*", "lhs": "a_node", "rhs": "two"},
    },
    "outputs": {"prod": {"node": "result", "label": "乘积"}},
}


_SUBGRAPH_GRAPH: dict = {
    "schema_version": "dag-v1",
    "name": "子图求值",
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
        "call_double": {"type": "call", "subgraph": "double", "bindings": {"val": "in_val"}},
    },
    "outputs": {"main_out": {"node": "call_double.doubled", "label": "结果"}},
}


_CONDITION_GRAPH: dict = {
    "schema_version": "dag-v1",
    "name": "条件图",
    "variables": {"flag": {"type": "float", "source": "computed"}},
    "nodes": {
        "flag_node": {"type": "var", "path": "flag"},
        "true_val": {"type": "const", "value": 100},
        "false_val": {"type": "const", "value": 0},
        "branch": {"type": "condition", "cond": "flag_node", "true_val": "true_val", "false_val": "false_val"},
    },
    "outputs": {"result": {"node": "branch", "label": "分支结果"}},
}


_EXPR_GRAPH: dict = {
    "schema_version": "dag-v1",
    "name": "表达式图",
    "nodes": {
        "e": {"type": "expr", "expr": "1 + floor(3.7)", "inputs": {}},
    },
    "outputs": {"out": {"node": "e", "label": "expr"}},
}


_CYCLE_GRAPH: dict = {
    "schema_version": "dag-v1",
    "name": "循环图",
    "nodes": {
        "a": {"type": "binary", "op": "+", "lhs": "b", "rhs": "b"},
        "b": {"type": "binary", "op": "+", "lhs": "a", "rhs": "a"},
    },
    "outputs": {"x": {"node": "a", "label": "x"}},
}


_RESOLVE_PATH_DICT: dict = {
    "schema_version": "dag-v1",
    "name": "嵌套路径 dict",
    "variables": {"character.attack": {"type": "float", "source": "character"}},
    "nodes": {
        "atk_node": {"type": "var", "path": "character.attack"},
    },
    "outputs": {"atk": {"node": "atk_node", "label": "攻击"}},
}


_MISSING_OUTPUT_DAG: dict = {
    "schema_version": "dag-v1",
    "name": "缺失输出引用",
    "subgraphs": {
        "add_one": {
            "parameters": {"val": {"type": "float"}},
            "nodes": {
                "one": {"type": "const", "value": 1},
                "result": {"type": "binary", "op": "+", "lhs": "val", "rhs": "one"},
            },
            "outputs": {"out": {"node": "result", "label": "val+1", "is_primary": True}},
        },
    },
    "nodes": {
        "in_val": {"type": "const", "value": 5},
        "call_add": {"type": "call", "subgraph": "add_one", "bindings": {"val": "in_val"}},
    },
    "outputs": {
        "valid": {"node": "call_add", "label": "有效输出"},
        "invalid": {"node": "call_add.nonexistent", "label": "无效输出"},
    },
}


class TestTopologicalSort:
    """拓扑排序。"""

    def test_linear_graph_order(self) -> None:
        g = dag_from_dict(_SIMPLE_LINEAR)
        order = topological_sort(g)
        assert len(order) == 3
        const_idx = order.index("two")
        var_idx = order.index("a_node")
        result_idx = order.index("result")
        assert const_idx < result_idx
        assert var_idx < result_idx

    def test_cycle_detected(self) -> None:
        g = dag_from_dict(_CYCLE_GRAPH)
        with pytest.raises(DAGCycleError):
            topological_sort(g)


class TestEvaluateGraph:
    """完整图求值。"""

    def test_simple_linear(self) -> None:
        g = dag_from_dict(_SIMPLE_LINEAR)
        result = evaluate_graph(g, {"a": 3.0})
        assert result.outputs["prod"] == pytest.approx(6.0)

    def test_subgraph_evaluation(self) -> None:
        g = dag_from_dict(_SUBGRAPH_GRAPH)
        result = evaluate_graph(g, {})
        assert result.outputs["main_out"] == pytest.approx(10.0)

    def test_condition_true_branch(self) -> None:
        g = dag_from_dict(_CONDITION_GRAPH)
        result = evaluate_graph(g, {"flag": 1.0})
        assert result.outputs["result"] == pytest.approx(100.0)

    def test_condition_false_branch(self) -> None:
        g = dag_from_dict(_CONDITION_GRAPH)
        result = evaluate_graph(g, {"flag": 0.0})
        assert result.outputs["result"] == pytest.approx(0.0)

    def test_expr_node(self) -> None:
        g = dag_from_dict(_EXPR_GRAPH)
        result = evaluate_graph(g, {})
        assert result.outputs["out"] == pytest.approx(4.0)

    def test_node_values_contain_intermediates(self) -> None:
        g = dag_from_dict(_SIMPLE_LINEAR)
        result = evaluate_graph(g, {"a": 4.0})
        assert result.node_values["two"] == pytest.approx(2.0)
        assert result.node_values["result"] == pytest.approx(8.0)

    def test_user_input_default(self) -> None:
        g = dag_from_dict({
            "schema_version": "dag-v1",
            "name": "ui",
            "nodes": {"ui": {"type": "user_input", "default": 42}},
            "outputs": {"o": {"node": "ui", "label": "o"}},
        })
        result = evaluate_graph(g, {})
        assert result.outputs["o"] == pytest.approx(42.0)

    def test_unary_node(self) -> None:
        g = dag_from_dict({
            "schema_version": "dag-v1",
            "name": "unary",
            "variables": {"x": {"type": "float", "source": "computed"}},
            "nodes": {
                "x_node": {"type": "var", "path": "x"},
                "neg": {"type": "unary", "op": "neg", "input": "x_node"},
            },
            "outputs": {"o": {"node": "neg", "label": "o"}},
        })
        result = evaluate_graph(g, {"x": 3.0})
        assert result.outputs["o"] == pytest.approx(-3.0)

    def test_unknown_unary_op(self) -> None:
        from calc_framework.dag.schema import DAGGraph, DAGOutput, DAGVariable, UnaryNode, VarNode
        g = DAGGraph(
            name="unknown_unary",
            variables={"x": DAGVariable(type="float", source="computed")},
            nodes={
                "x_node": VarNode(path="x"),
                "bad": UnaryNode(op="foo", input="x_node"),
            },
            outputs={"o": DAGOutput(node="bad", label="o")},
        )
        with pytest.raises(DAGRuntimeError, match="未知一元运算"):
            evaluate_graph(g, {"x": 1.0})

    def test_unknown_binary_op(self) -> None:
        from calc_framework.dag.schema import BinaryNode, ConstNode, DAGGraph, DAGOutput, DAGVariable, VarNode
        g = DAGGraph(
            name="unknown_binary",
            variables={"x": DAGVariable(type="float", source="computed")},
            nodes={
                "x_node": VarNode(path="x"),
                "two": ConstNode(value=2),
                "bad": BinaryNode(op="^^^", lhs="x_node", rhs="two"),
            },
            outputs={"o": DAGOutput(node="bad", label="o")},
        )
        with pytest.raises(DAGRuntimeError, match="未知二元运算"):
            evaluate_graph(g, {"x": 1.0})

    def test_unsupported_node_type(self) -> None:
        from dataclasses import dataclass
        from calc_framework.dag.engine import _eval_single_node

        @dataclass
        class MockNode:
            type: str = "mock"

        with pytest.raises(DAGRuntimeError, match="不支持的节点类型"):
            _eval_single_node(MockNode(), {}, {})

    def test_resolve_path_with_dict(self) -> None:
        g = dag_from_dict(_RESOLVE_PATH_DICT)
        result = evaluate_graph(g, {"character": {"attack": 100.0}})
        assert result.outputs["atk"] == pytest.approx(100.0)

    def test_resolve_path_non_dict_intermediate(self) -> None:
        g = dag_from_dict(_RESOLVE_PATH_DICT)
        with pytest.raises(DAGRuntimeError):
            evaluate_graph(g, {"character": 10.0})

    def test_missing_output_reference(self) -> None:
        g = dag_from_dict(_MISSING_OUTPUT_DAG)
        result = evaluate_graph(g, {})
        assert result.outputs["valid"] == pytest.approx(6.0)
        assert "invalid" not in result.outputs
