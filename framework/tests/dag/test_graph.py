# SPDX-License-Identifier: AGPL-3.0
"""DAG 图算法单元测试：拓扑排序、节点依赖、节点显示。"""

from __future__ import annotations

import pytest

from calc_framework.dag.errors import DAGCycleError
from calc_framework.dag.graph import (
    _node_dependencies,
    _node_display,
    topological_sort,
)
from calc_framework.dag.graph_types import DAGGraph
from calc_framework.dag.node_types import (
    BinaryNode,
    ConditionNode,
    ConstNode,
    ExprNode,
    UnaryNode,
    UserInputNode,
    VarNode,
)


class TestTopologicalSort:
    def test_single_node(self) -> None:
        graph = DAGGraph(nodes={"n1": ConstNode(value=1.0)})
        order = topological_sort(graph)
        assert order == ["n1"]

    def test_linear_chain(self) -> None:
        graph = DAGGraph(
            nodes={
                "n1": ConstNode(value=1.0),
                "n2": UnaryNode(op="neg", input="n1"),
                "n3": UnaryNode(op="abs", input="n2"),
            }
        )
        order = topological_sort(graph)
        assert order.index("n1") < order.index("n2")
        assert order.index("n2") < order.index("n3")

    def test_binary_diamond(self) -> None:
        graph = DAGGraph(
            nodes={
                "a": ConstNode(value=1.0),
                "b": ConstNode(value=2.0),
                "c": BinaryNode(op="add", lhs="a", rhs="b"),
            }
        )
        order = topological_sort(graph)
        assert order.index("a") < order.index("c")
        assert order.index("b") < order.index("c")

    def test_cycle_detected(self) -> None:
        graph = DAGGraph(
            nodes={
                "n1": UnaryNode(op="neg", input="n2"),
                "n2": UnaryNode(op="neg", input="n1"),
            }
        )
        with pytest.raises(DAGCycleError):
            topological_sort(graph)

    def test_disconnected_graph(self) -> None:
        graph = DAGGraph(
            nodes={
                "a": ConstNode(value=1.0),
                "b": ConstNode(value=2.0),
                "c": ConstNode(value=3.0),
            }
        )
        order = topological_sort(graph)
        assert len(order) == 3


class TestNodeDependencies:
    def test_const_var(self) -> None:
        assert _node_dependencies(ConstNode(value=1.0)) == []
        assert _node_dependencies(VarNode(path="x")) == []

    def test_unary(self) -> None:
        assert _node_dependencies(UnaryNode(input="n1")) == ["n1"]

    def test_binary(self) -> None:
        node = BinaryNode(lhs="a", rhs="b")
        assert _node_dependencies(node) == ["a", "b"]

    def test_condition(self) -> None:
        node = ConditionNode(cond="c", true_val="t", false_val="f")
        assert set(_node_dependencies(node)) == {"c", "t", "f"}

    def test_expr(self) -> None:
        node = ExprNode(inputs={"x": "n1", "y": "n2"})
        assert _node_dependencies(node) == ["n1", "n2"]


class TestNodeDisplay:
    def test_const(self) -> None:
        assert "Const(5.0)" in _node_display(ConstNode(value=5.0))

    def test_var(self) -> None:
        assert "Var(x.y)" in _node_display(VarNode(path="x.y"))

    def test_user_input(self) -> None:
        assert "UserInput" in _node_display(UserInputNode(default=0.0))

    def test_unary(self) -> None:
        assert "Unary" in _node_display(UnaryNode(op="neg", input="n1"))

    def test_binary(self) -> None:
        assert "Binary" in _node_display(BinaryNode(op="add", lhs="a", rhs="b"))

    def test_condition(self) -> None:
        assert "Condition" in _node_display(ConditionNode())

    def test_expr(self) -> None:
        assert "Expr" in _node_display(ExprNode(expr="x+y"))

    def test_unknown_type(self) -> None:
        assert _node_display("unknown") == "str"  # type: ignore[arg-type]
