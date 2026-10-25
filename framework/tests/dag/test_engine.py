# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""DAG 求值引擎单元测试。"""

from __future__ import annotations

import pytest

from calc_framework.dag.engine import _eval_single_node, evaluate_graph
from calc_framework.dag.errors import DAGRuntimeError
from calc_framework.dag.graph_types import DAGGraph, DAGOutput
from calc_framework.dag.node_types import (
    BinaryNode,
    ConditionNode,
    ConstNode,
    ExprNode,
    UnaryNode,
    UserInputNode,
    VarNode,
)
from calc_framework.dag.state import DAGState


class TestEvalSingleNode:
    def test_const(self) -> None:
        assert _eval_single_node(ConstNode(value=5.0), {}, {}) == 5.0

    def test_const_float_coerce(self) -> None:
        assert _eval_single_node(ConstNode(value=3), {}, {}) == 3.0

    def test_var_found(self) -> None:
        assert _eval_single_node(VarNode(path="x"), {}, {"x": 42.0}) == 42.0

    def test_var_nested(self) -> None:
        ctx = {"character": {"atk": 100.0}}
        assert _eval_single_node(VarNode(path="character.atk"), {}, ctx) == 100.0

    def test_var_not_found(self) -> None:
        with pytest.raises(DAGRuntimeError):
            _eval_single_node(VarNode(path="missing"), {}, {})

    def test_user_input(self) -> None:
        assert _eval_single_node(UserInputNode(default=3.0), {}, {}) == 3.0

    def test_unary_neg(self) -> None:
        assert _eval_single_node(UnaryNode(op="neg", input="n1"), {"n1": 5.0}, {}) == -5.0

    def test_unary_abs(self) -> None:
        assert _eval_single_node(UnaryNode(op="abs", input="n1"), {"n1": -3.0}, {}) == 3.0

    def test_unary_unknown_op(self) -> None:
        with pytest.raises(DAGRuntimeError):
            _eval_single_node(UnaryNode(op="bogus", input="n1"), {"n1": 1.0}, {})

    def test_binary_add(self) -> None:
        node = BinaryNode(op="+", lhs="a", rhs="b")
        assert _eval_single_node(node, {"a": 1.0, "b": 2.0}, {}) == 3.0

    def test_binary_mul(self) -> None:
        node = BinaryNode(op="*", lhs="a", rhs="b")
        assert _eval_single_node(node, {"a": 3.0, "b": 4.0}, {}) == 12.0

    def test_binary_div(self) -> None:
        node = BinaryNode(op="/", lhs="a", rhs="b")
        assert _eval_single_node(node, {"a": 10.0, "b": 2.0}, {}) == 5.0

    def test_binary_div_by_zero(self) -> None:
        node = BinaryNode(op="/", lhs="a", rhs="b")
        with pytest.raises(DAGRuntimeError):
            _eval_single_node(node, {"a": 1.0, "b": 0.0}, {})

    def test_binary_mod(self) -> None:
        node = BinaryNode(op="mod", lhs="a", rhs="b")
        assert _eval_single_node(node, {"a": 7.0, "b": 3.0}, {}) == 1.0

    def test_binary_unknown_op(self) -> None:
        node = BinaryNode(op="bogus", lhs="a", rhs="b")
        with pytest.raises(DAGRuntimeError):
            _eval_single_node(node, {"a": 1.0, "b": 2.0}, {})

    def test_condition_true(self) -> None:
        node = ConditionNode(cond="c", true_val="t", false_val="f")
        assert _eval_single_node(node, {"c": 1.0, "t": 10.0, "f": 20.0}, {}) == 10.0

    def test_condition_false(self) -> None:
        node = ConditionNode(cond="c", true_val="t", false_val="f")
        assert _eval_single_node(node, {"c": 0.0, "t": 10.0, "f": 20.0}, {}) == 20.0

    def test_expr_node(self) -> None:
        node = ExprNode(expr="a + b", inputs={"a": "n1", "b": "n2"})
        assert _eval_single_node(node, {"n1": 3.0, "n2": 4.0}, {}) == 7.0

    def test_unsupported_type(self) -> None:
        with pytest.raises(DAGRuntimeError):
            _eval_single_node("string_node", {}, {})  # type: ignore[arg-type]


class TestEvaluateGraph:
    def test_single_const(self) -> None:
        graph = DAGGraph(nodes={"n1": ConstNode(value=42.0)})
        result = evaluate_graph(graph, {})
        assert result.node_values["n1"] == 42.0

    def test_linear_chain(self) -> None:
        graph = DAGGraph(
            nodes={
                "a": ConstNode(value=10.0),
                "b": UnaryNode(op="neg", input="a"),
            }
        )
        result = evaluate_graph(graph, {})
        assert result.node_values["a"] == 10.0
        assert result.node_values["b"] == -10.0

    def test_binary_chain(self) -> None:
        graph = DAGGraph(
            nodes={
                "a": ConstNode(value=2.0),
                "b": ConstNode(value=3.0),
                "c": BinaryNode(op="+", lhs="a", rhs="b"),
                "d": BinaryNode(op="*", lhs="c", rhs="b"),
            }
        )
        result = evaluate_graph(graph, {})
        assert result.node_values["c"] == 5.0
        assert result.node_values["d"] == 15.0

    def test_var_input(self) -> None:
        graph = DAGGraph(
            nodes={
                "v": VarNode(path="x"),
                "o": UnaryNode(op="neg", input="v"),
            }
        )
        result = evaluate_graph(graph, {"x": 7.0})
        assert result.node_values["v"] == 7.0
        assert result.node_values["o"] == -7.0

    def test_incremental_unchanged(self) -> None:
        """相同上下文两次求值应返回缓存结果。"""
        graph = DAGGraph(
            nodes={
                "a": ConstNode(value=1.0),
                "v": VarNode(path="x"),
            }
        )
        state = DAGState()
        evaluate_graph(graph, {"x": 5.0}, dag_state=state)  # first eval populates state
        r2 = evaluate_graph(graph, {"x": 5.0}, dag_state=state)
        assert r2.node_values["v"] == 5.0
        assert r2.node_values["a"] == 1.0
        assert state.evaluation_count == 2

    def test_incremental_changed(self) -> None:
        """上下文变化后应重算。"""
        graph = DAGGraph(
            nodes={
                "v": VarNode(path="x"),
                "o": UnaryNode(op="neg", input="v"),
            }
        )
        state = DAGState()
        r1 = evaluate_graph(graph, {"x": 5.0}, dag_state=state)
        assert r1.node_values["o"] == -5.0
        r2 = evaluate_graph(graph, {"x": 10.0}, dag_state=state)
        assert r2.node_values["o"] == -10.0

    def test_cycle_detection(self) -> None:
        """循环依赖应立即报错。"""
        graph = DAGGraph(
            nodes={
                "a": UnaryNode(op="neg", input="b"),
                "b": UnaryNode(op="neg", input="a"),
            }
        )
        with pytest.raises(Exception):
            evaluate_graph(graph, {})

    def test_div_by_zero_handling(self) -> None:
        graph = DAGGraph(
            nodes={
                "a": ConstNode(value=1.0),
                "b": ConstNode(value=0.0),
                "c": BinaryNode(op="div", lhs="a", rhs="b"),
            }
        )
        with pytest.raises(Exception):
            evaluate_graph(graph, {})

    def test_outputs_in_result(self) -> None:
        graph = DAGGraph(
            nodes={
                "a": ConstNode(value=5.0),
                "b": ConstNode(value=3.0),
                "sum": BinaryNode(op="+", lhs="a", rhs="b"),
            },
            outputs={"result": DAGOutput(node="sum", label="sum", format=".1f", is_primary=True)},
        )
        result = evaluate_graph(graph, {})
        assert result.outputs.get("result") == 8.0

    def test_execution_order_topo(self) -> None:
        graph = DAGGraph(
            nodes={
                "a": ConstNode(value=1.0),
                "b": UnaryNode(op="neg", input="a"),
            }
        )
        result = evaluate_graph(graph, {})
        assert result.execution_order.index("a") < result.execution_order.index("b")

    def test_condition_node(self) -> None:
        graph = DAGGraph(
            nodes={
                "cond": ConstNode(value=1.0),
                "t": ConstNode(value=100.0),
                "f": ConstNode(value=200.0),
                "c": ConditionNode(cond="cond", true_val="t", false_val="f"),
            }
        )
        result = evaluate_graph(graph, {})
        assert result.node_values["c"] == 100.0

    def test_expr_node(self) -> None:
        graph = DAGGraph(
            nodes={
                "a": ConstNode(value=7.0),
                "b": ConstNode(value=3.0),
                "e": ExprNode(expr="a * b + 1", inputs={"a": "a", "b": "b"}),
            }
        )
        result = evaluate_graph(graph, {})
        assert result.node_values["e"] == 22.0

    def test_user_input_default(self) -> None:
        graph = DAGGraph(
            nodes={
                "u": UserInputNode(default=99.0),
                "o": UnaryNode(op="neg", input="u"),
            }
        )
        result = evaluate_graph(graph, {})
        assert result.node_values["u"] == 99.0
        assert result.node_values["o"] == -99.0
