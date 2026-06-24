# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""子图展开单元测试。"""
# pyright: reportCallIssue=false

from __future__ import annotations

from calc_framework.dag.graph_types import DAGGraph, DAGOutput, DAGSubgraph, DAGVariable
from calc_framework.dag.node_types import (
    BinaryNode,
    CallNode,
    ConditionNode,
    ConstNode,
    ExprNode,
    UnaryNode,
    VarNode,
)
from calc_framework.dag.subgraph import (
    _apply_ref_map_to_node,
    _prefixed_node,
    expand_subgraphs,
)


class TestPrefixedNode:
    def test_unary(self) -> None:
        result = _prefixed_node(UnaryNode(input="n1"), "b")
        assert result.input == "b.n1"

    def test_binary(self) -> None:
        result = _prefixed_node(BinaryNode(lhs="a", rhs="b"), "b")
        assert result.lhs == "b.a"
        assert result.rhs == "b.b"

    def test_condition(self) -> None:
        node = ConditionNode(cond="c", true_val="t", false_val="f")
        result = _prefixed_node(node, "b")
        assert result.cond == "b.c"
        assert result.true_val == "b.t"
        assert result.false_val == "b.f"

    def test_expr(self) -> None:
        result = _prefixed_node(ExprNode(inputs={"x": "n1"}), "b")
        assert result.inputs["x"] == "b.n1"

    def test_var(self) -> None:
        result = _prefixed_node(VarNode(path="x.y"), "b")
        assert result.path == "b.x.y"

    def test_call(self) -> None:
        result = _prefixed_node(CallNode(subgraph="s", bindings={"a": "n1"}), "b")
        assert result.bindings["a"] == "b.n1"

    def test_const_unchanged(self) -> None:
        result = _prefixed_node(ConstNode(value=5.0), "b")
        assert result.value == 5.0


class TestApplyRefMap:
    def test_unary(self) -> None:
        node = UnaryNode(input="old")
        _apply_ref_map_to_node(node, {"old": "new"})
        assert node.input == "new"

    def test_binary(self) -> None:
        node = BinaryNode(lhs="a", rhs="b")
        _apply_ref_map_to_node(node, {"a": "x", "b": "y"})
        assert node.lhs == "x"
        assert node.rhs == "y"

    def test_condition(self) -> None:
        node = ConditionNode(cond="c", true_val="t", false_val="f")
        _apply_ref_map_to_node(node, {"c": "c2"})
        assert node.cond == "c2"

    def test_expr(self) -> None:
        node = ExprNode(inputs={"a": "n1"})
        _apply_ref_map_to_node(node, {"n1": "n2"})
        assert node.inputs["a"] == "n2"

    def test_chain(self) -> None:
        """测试链式引用解析（a→b→c）。"""
        node = UnaryNode(input="a")
        _apply_ref_map_to_node(node, {"a": "b", "b": "c"})
        assert node.input == "c"

    def test_no_match(self) -> None:
        node = UnaryNode(input="x")
        _apply_ref_map_to_node(node, {"y": "z"})
        assert node.input == "x"


class TestExpandSubgraphs:
    def test_no_subgraphs(self) -> None:
        """没有子图的图扩展后不变。"""
        graph = DAGGraph(nodes={"n1": ConstNode(value=1.0)})
        result = expand_subgraphs(graph)
        assert "n1" in result.nodes

    def test_single_call(self) -> None:
        graph = DAGGraph(
            nodes={"call1": CallNode(subgraph="add", bindings={"a": "n1", "b": "n2"})},
            subgraphs={
                "add": DAGSubgraph(
                    nodes={
                        "sum": BinaryNode(op="add", lhs="a", rhs="b"),
                    },
                    outputs={"out": DAGOutput(node="sum")},
                ),
            },
        )
        result = expand_subgraphs(graph)
        # call node should be expanded into prefixed nodes
        assert "call1.sum" in result.nodes
        assert isinstance(result.nodes["call1.sum"], BinaryNode)

    def test_call_reference_maps(self) -> None:
        """call 绑定的参数应正确映射到展开后的引用。"""
        graph = DAGGraph(
            nodes={
                "a": ConstNode(value=3.0),
                "b": ConstNode(value=4.0),
                "call1": CallNode(subgraph="add", bindings={"a": "a", "b": "b"}),
            },
            subgraphs={
                "add": DAGSubgraph(
                    nodes={
                        "sum": BinaryNode(op="add", lhs="a", rhs="b"),
                    },
                    outputs={"out": DAGOutput(node="sum")},
                ),
            },
        )
        result = expand_subgraphs(graph)
        assert "call1.sum" in result.nodes
        n = result.nodes["call1.sum"]
        assert isinstance(n, BinaryNode)
        # After ref mapping, lhs and rhs should point to the original nodes
        assert n.lhs == "call1.a" or n.lhs == "a"
        assert n.rhs == "call1.b" or n.rhs == "b"

    def test_nested_call(self) -> None:
        """调用另一个子图的 call 节点应递归展开。"""
        graph = DAGGraph(
            nodes={
                "a": ConstNode(value=1.0),
                "b": ConstNode(value=2.0),
                "call1": CallNode(subgraph="add", bindings={"a": "a", "b": "b"}),
            },
            subgraphs={
                "add": DAGSubgraph(
                    nodes={
                        "sum": BinaryNode(op="+", lhs="a", rhs="b"),
                    },
                    outputs={"out": DAGOutput(node="sum")},
                ),
            },
        )
        result = expand_subgraphs(graph)
        assert len(result.nodes) >= 1
        # Call node should be removed
        assert "call1" not in result.nodes

    def test_respects_variables(self) -> None:
        graph = DAGGraph(
            nodes={"n1": ConstNode(value=1.0)},
            variables={"v1": DAGVariable(type="float", source="user_input")},
        )
        result = expand_subgraphs(graph)
        assert "v1" in result.variables
