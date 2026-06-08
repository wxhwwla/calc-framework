# SPDX-License-Identifier: AGPL-3.0
"""DAG 求值服务单元测试。"""

from __future__ import annotations

from calc_framework.dag.graph_types import DAGGraph
from calc_framework.dag.node_types import ConstNode, UnaryNode
from calc_framework.dag.service import DAGService
from calc_framework.dag.state import DAGState


class TestDAGService:
    def test_construct_from_graph(self) -> None:
        graph = DAGGraph(nodes={"n1": ConstNode(value=1.0)})
        svc = DAGService(graph)
        result = svc.evaluate({})
        assert result.node_values["n1"] == 1.0

    def test_evaluate_outputs(self) -> None:
        graph = DAGGraph(
            nodes={
                "a": ConstNode(value=2.0),
                "b": ConstNode(value=3.0),
            },
        )
        svc = DAGService(graph)
        result = svc.evaluate({})
        assert result.node_values["a"] == 2.0

    def test_evaluate_returns_node_values(self) -> None:
        graph = DAGGraph(
            nodes={
                "a": ConstNode(value=10.0),
                "b": UnaryNode(op="neg", input="a"),
            }
        )
        svc = DAGService(graph)
        result = svc.evaluate({})
        assert result.node_values == {"a": 10.0, "b": -10.0}

    def test_multiple_evaluations(self) -> None:
        graph = DAGGraph(nodes={"a": ConstNode(value=1.0)})
        svc = DAGService(graph)
        r1 = svc.evaluate({})
        r2 = svc.evaluate({})
        assert r1.node_values == r2.node_values

    def test_has_state_by_default(self) -> None:
        graph = DAGGraph(nodes={"n1": ConstNode(value=1.0)})
        svc = DAGService(graph)
        assert isinstance(svc._dag_state, DAGState)

    def test_has_cache_by_default(self) -> None:
        graph = DAGGraph(nodes={"n1": ConstNode(value=1.0)})
        svc = DAGService(graph)
        assert svc._block_cache is not None

    def test_register_function(self) -> None:
        graph = DAGGraph(nodes={"n1": ConstNode(value=1.0)})
        svc = DAGService(graph)
        svc.register_function("double", lambda x: x * 2)
        # No error means success
