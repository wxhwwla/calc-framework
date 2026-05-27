#!/usr/bin/env python3
"""子图展开单元测试。"""

from calc_framework.dag.serializer import dag_from_dict
from calc_framework.dag.subgraph import expand_subgraphs


_SIMPLE_SUBGRAPH: dict = {
    "schema_version": "dag-v1",
    "name": "子图展开测试",
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
    "outputs": {
        "main_out": {"node": "call_double.doubled", "label": "结果"},
    },
}


class TestSubgraphExpansion:
    """子图内联展开。"""

    def test_call_node_expanded_into_binary(self) -> None:
        g = dag_from_dict(_SIMPLE_SUBGRAPH)
        expanded = expand_subgraphs(g)
        assert "call_double.two" in expanded.nodes
        assert "call_double.result" in expanded.nodes
        assert "call_double" not in expanded.nodes

    def test_output_references_rewritten(self) -> None:
        g = dag_from_dict(_SIMPLE_SUBGRAPH)
        expanded = expand_subgraphs(g)
        main_out = expanded.outputs["main_out"]
        assert main_out.node == "call_double.result"

    def test_no_subgraphs_no_change(self) -> None:
        g = dag_from_dict({
            "schema_version": "dag-v1",
            "name": "no subs",
            "nodes": {"c": {"type": "const", "value": 1}},
            "outputs": {"o": {"node": "c", "label": "o"}},
        })
        expanded = expand_subgraphs(g)
        assert len(expanded.nodes) == 1
        assert expanded.nodes["c"] == g.nodes["c"]

    def test_nested_subgraph_expansion(self) -> None:
        """子图内 call 另一个子图也被展开。"""
        g = dag_from_dict({
            "schema_version": "dag-v1",
            "name": "嵌套子图",
            "subgraphs": {
                "inner": {
                    "parameters": {"x": {"type": "float"}},
                    "nodes": {"one": {"type": "const", "value": 1}, "sum": {"type": "binary", "op": "+", "lhs": "x", "rhs": "one"}},
                    "outputs": {"out": {"node": "sum", "label": "+1"}},
                },
                "outer": {
                    "parameters": {"y": {"type": "float"}},
                    "nodes": {
                        "two": {"type": "const", "value": 2},
                        "inner_call": {"type": "call", "subgraph": "inner", "bindings": {"x": "y"}},
                        "mul": {"type": "binary", "op": "*", "lhs": "inner_call.out", "rhs": "two"},
                    },
                    "outputs": {"result": {"node": "mul", "label": "(y+1)*2"}},
                },
            },
            "nodes": {
                "inp": {"type": "const", "value": 3},
                "outer_call": {"type": "call", "subgraph": "outer", "bindings": {"y": "inp"}},
            },
            "outputs": {"final": {"node": "outer_call.result", "label": "最终"}},
        })
        expanded = expand_subgraphs(g)
        assert "outer_call.two" in expanded.nodes
        assert "outer_call.inner_call.one" in expanded.nodes
        assert "outer_call.inner_call.sum" in expanded.nodes
        assert "outer_call.mul" in expanded.nodes
        assert expanded.outputs["final"].node == "outer_call.mul"
