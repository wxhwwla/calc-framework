# SPDX-License-Identifier: AGPL-3.0
"""块级缓存单元测试。"""

from __future__ import annotations

import pytest

from calc_framework.dag.block_cache import (
    BlockCache,
    _build_block_membership,
    _compute_block_inputs,
    _compute_input_hash,
    _get_primary_output_node,
    _resolve_block_outputs,
    _stable_hash_int,
)
from calc_framework.dag.graph_types import DAGGraph, DAGOutput, DAGSubgraph
from calc_framework.dag.node_types import CallNode, ConstNode, VarNode


class TestBlockCache:
    def test_get_missing(self) -> None:
        cache = BlockCache()
        result = cache.get("nonexistent", {"a": 1.0})
        assert result is None

    def test_put_and_get(self) -> None:
        cache = BlockCache()
        cache.put("b1", {"a": 1.0}, {"out": 42.0})
        result = cache.get("b1", {"a": 1.0})
        assert result is not None
        assert result["out"] == 42.0

    def test_different_input_returns_none(self) -> None:
        cache = BlockCache()
        cache.put("b1", {"a": 1.0}, {"out": 42.0})
        result = cache.get("b1", {"a": 2.0})
        assert result is None

    def test_invalidate(self) -> None:
        cache = BlockCache()
        cache.put("b1", {"a": 1.0}, {"out": 42.0})
        cache.invalidate("b1")
        assert cache.get("b1", {"a": 1.0}) is None

    def test_invalidate_all(self) -> None:
        cache = BlockCache()
        cache.put("b1", {"a": 1.0}, {"out": 10.0})
        cache.put("b2", {"a": 2.0}, {"out": 20.0})
        cache.invalidate_all()
        assert cache.get("b1", {"a": 1.0}) is None
        assert cache.get("b2", {"a": 2.0}) is None

    def test_put_overwrites(self) -> None:
        cache = BlockCache()
        cache.put("b1", {"a": 1.0}, {"out": 10.0})
        cache.put("b1", {"a": 1.0}, {"out": 99.0})
        result = cache.get("b1", {"a": 1.0})
        assert result is not None
        assert result["out"] == 99.0

    def test_multiple_blocks_independent(self) -> None:
        cache = BlockCache()
        cache.put("b1", {"a": 1.0}, {"out": 10.0})
        cache.put("b2", {"a": 2.0}, {"out": 20.0})
        r1 = cache.get("b1", {"a": 1.0})
        r2 = cache.get("b2", {"a": 2.0})
        assert r1 is not None and r1["out"] == 10.0
        assert r2 is not None and r2["out"] == 20.0

    def test_get_does_not_mutate_cache(self) -> None:
        cache = BlockCache()
        cache.put("b1", {"a": 1.0}, {"out": 42.0})
        r1 = cache.get("b1", {"a": 1.0})
        r2 = cache.get("b1", {"a": 1.0})
        assert r1 is not None and r2 is not None
        assert r1["out"] == r2["out"]

    def test_empty_inputs(self) -> None:
        cache = BlockCache()
        cache.put("b1", {}, {"out": 1.0})
        result = cache.get("b1", {})
        assert result is not None
        assert result["out"] == 1.0


class TestBlockCacheEviction:
    def test_lru_evicts_oldest_when_max_entries_exceeded(self) -> None:
        cache = BlockCache(max_entries=2)
        cache.put("b1", {"a": 1.0}, {"out": 1.0})
        cache.put("b2", {"a": 2.0}, {"out": 2.0})
        cache.put("b3", {"a": 3.0}, {"out": 3.0})
        assert len(cache) == 2
        assert cache.get("b1", {"a": 1.0}) is None
        assert cache.get("b2", {"a": 2.0}) is not None
        assert cache.get("b3", {"a": 3.0}) is not None

    def test_get_promotes_entry_for_lru(self) -> None:
        cache = BlockCache(max_entries=2)
        cache.put("b1", {"a": 1.0}, {"out": 1.0})
        cache.put("b2", {"a": 2.0}, {"out": 2.0})
        assert cache.get("b1", {"a": 1.0}) is not None
        cache.put("b3", {"a": 3.0}, {"out": 3.0})
        assert cache.get("b2", {"a": 2.0}) is None
        assert cache.get("b1", {"a": 1.0}) is not None

    def test_ttl_expires_entry(self, monkeypatch: pytest.MonkeyPatch) -> None:
        clock = {"now": 100.0}
        monkeypatch.setattr(
            "calc_framework.dag.block_cache.time.monotonic",
            lambda: clock["now"],
        )
        cache = BlockCache(ttl_seconds=30.0)
        cache.put("b1", {"a": 1.0}, {"out": 1.0})
        clock["now"] = 131.0
        assert cache.get("b1", {"a": 1.0}) is None
        assert len(cache) == 0

    def test_get_refreshes_ttl(self, monkeypatch: pytest.MonkeyPatch) -> None:
        clock = {"now": 0.0}
        monkeypatch.setattr(
            "calc_framework.dag.block_cache.time.monotonic",
            lambda: clock["now"],
        )
        cache = BlockCache(ttl_seconds=10.0)
        cache.put("b1", {"a": 1.0}, {"out": 1.0})
        clock["now"] = 8.0
        assert cache.get("b1", {"a": 1.0}) is not None
        clock["now"] = 15.0
        assert cache.get("b1", {"a": 1.0}) is not None


class TestStableInputHash:
    def test_compute_input_hash_order_independent(self) -> None:
        h1 = _compute_input_hash({"a": 1.0, "b": 2.0})
        h2 = _compute_input_hash({"b": 2.0, "a": 1.0})
        assert h1 == h2

    def test_compute_input_hash_differs_for_different_inputs(self) -> None:
        h1 = _compute_input_hash({"a": 1.0})
        h2 = _compute_input_hash({"a": 2.0})
        assert h1 != h2

    def test_stable_hash_int_is_deterministic(self) -> None:
        payload = b"call1"
        assert _stable_hash_int(payload) == _stable_hash_int(payload)

    def test_call_binding_uses_stable_hash(self) -> None:
        graph = DAGGraph(
            nodes={
                "call1": CallNode(subgraph="inner", bindings={"a": "n1"}),
                "call2": CallNode(subgraph="outer", bindings={"x": "call1"}),
            }
        )
        result = _compute_block_inputs(graph, {})
        expected = _stable_hash_int(b"call1")
        assert result["call2"]["x"] == expected


class TestComputeBlockInputs:
    def test_no_call_nodes(self) -> None:
        graph = DAGGraph(nodes={"a": ConstNode(value=1.0)})
        result = _compute_block_inputs(graph, {})
        assert result == {}

    def test_call_node_with_const_binding(self) -> None:
        graph = DAGGraph(
            nodes={
                "n1": ConstNode(value=5.0),
                "call1": CallNode(subgraph="s", bindings={"x": "n1"}),
            }
        )
        result = _compute_block_inputs(graph, {})
        assert result == {"call1": {"x": 5.0}}

    def test_call_node_with_var_binding(self) -> None:
        graph = DAGGraph(
            nodes={
                "v1": VarNode(path="character.atk"),
                "call1": CallNode(subgraph="s", bindings={"x": "v1"}),
            }
        )
        result = _compute_block_inputs(graph, {"character": {"atk": 100.0}})
        assert result == {"call1": {"x": 100.0}}

    def test_call_node_with_var_missing_from_context(self) -> None:
        """缺失变量不应出现在结果中。"""
        graph = DAGGraph(
            nodes={
                "v1": VarNode(path="missing"),
                "call1": CallNode(subgraph="s", bindings={"x": "v1"}),
            }
        )
        result = _compute_block_inputs(graph, {})
        assert result == {}

    def test_call_node_with_call_binding(self) -> None:
        """块到块依赖应使用哈希作为代理值。"""
        graph = DAGGraph(
            nodes={
                "call1": CallNode(subgraph="inner", bindings={"a": "n1"}),
                "call2": CallNode(subgraph="outer", bindings={"x": "call1"}),
            }
        )
        result = _compute_block_inputs(graph, {})
        assert "call2" in result
        assert isinstance(result["call2"]["x"], int)

    def test_mixed_call_and_const(self) -> None:
        graph = DAGGraph(
            nodes={
                "c1": ConstNode(value=3.0),
                "c2": ConstNode(value=4.0),
                "call1": CallNode(subgraph="add", bindings={"a": "c1", "b": "c2"}),
            }
        )
        result = _compute_block_inputs(graph, {})
        assert result == {"call1": {"a": 3.0, "b": 4.0}}


class TestBuildBlockMembership:
    def test_no_call_nodes(self) -> None:
        graph = DAGGraph(nodes={"n1": ConstNode(value=1.0)})
        expanded = DAGGraph(nodes={"n1": ConstNode(value=1.0)})
        result = _build_block_membership(expanded, graph)
        assert result == {}

    def test_call_node_expanded(self) -> None:
        graph = DAGGraph(
            nodes={
                "call1": CallNode(subgraph="s", bindings={"x": "n1"}),
            }
        )
        expanded = DAGGraph(
            nodes={
                "call1.sum": ConstNode(value=5.0),
                "call1.out": ConstNode(value=5.0),
            }
        )
        result = _build_block_membership(expanded, graph)
        assert "call1" in result
        assert "call1.sum" in result["call1"]
        assert "call1.out" in result["call1"]


class TestGetPrimaryOutputNode:
    def test_primary_output(self) -> None:
        graph = DAGGraph(
            nodes={"call1": CallNode(subgraph="s", bindings={})},
            subgraphs={
                "s": DAGSubgraph(
                    nodes={"sum": ConstNode(value=1.0)},
                    outputs={"out": DAGOutput(node="sum", is_primary=True)},
                ),
            },
        )
        call_node = graph.nodes["call1"]
        assert isinstance(call_node, CallNode)
        result = _get_primary_output_node(graph, call_node, "call1")
        assert result == "call1.sum"

    def test_fallback_first_output(self) -> None:
        graph = DAGGraph(
            nodes={"call1": CallNode(subgraph="s", bindings={})},
            subgraphs={
                "s": DAGSubgraph(
                    nodes={"sum": ConstNode(value=1.0)},
                    outputs={"out": DAGOutput(node="sum")},
                ),
            },
        )
        call_node = graph.nodes["call1"]
        assert isinstance(call_node, CallNode)
        result = _get_primary_output_node(graph, call_node, "call1")
        assert result == "call1.sum"

    def test_no_subgraph(self) -> None:
        result = _get_primary_output_node(
            DAGGraph(nodes={"call1": CallNode(subgraph="nonexistent", bindings={})}),
            CallNode(subgraph="nonexistent", bindings={}),
            "call1",
        )
        assert result is None

    def test_no_outputs(self) -> None:
        graph = DAGGraph(
            nodes={"call1": CallNode(subgraph="s", bindings={})},
            subgraphs={"s": DAGSubgraph(nodes={"n1": ConstNode(value=1.0)})},
        )
        call_node = graph.nodes["call1"]
        assert isinstance(call_node, CallNode)
        result = _get_primary_output_node(graph, call_node, "call1")
        assert result is None


class TestResolveBlockOutputs:
    def test_resolve_from_expanded(self) -> None:
        graph = DAGGraph(
            nodes={"call1": CallNode(subgraph="s", bindings={"x": "n1"})},
            subgraphs={
                "s": DAGSubgraph(
                    nodes={"sum": ConstNode(value=1.0)},
                    outputs={"out": DAGOutput(node="sum")},
                ),
            },
        )
        expanded = DAGGraph(nodes={"call1.sum": ConstNode(value=5.0)})
        values = {"call1.sum": 5.0}
        result = _resolve_block_outputs(graph, expanded, "call1", values)
        assert result.get("out") == 5.0

    def test_not_a_call_node(self) -> None:
        graph = DAGGraph(nodes={"n1": ConstNode(value=1.0)})
        result = _resolve_block_outputs(graph, DAGGraph(), "n1", {"n1": 1.0})
        assert result == {}

    def test_no_subgraph(self) -> None:
        graph = DAGGraph(nodes={"call1": CallNode(subgraph="missing", bindings={})})
        result = _resolve_block_outputs(graph, DAGGraph(), "call1", {})
        assert result == {}

    def test_fallback_primary(self) -> None:
        """当输出名不匹配时，应回退到主输出。"""
        graph = DAGGraph(
            nodes={"call1": CallNode(subgraph="s", bindings={})},
            subgraphs={
                "s": DAGSubgraph(
                    nodes={"out": ConstNode(value=42.0)},
                    outputs={"result": DAGOutput(node="out", is_primary=True)},
                ),
            },
        )
        expanded = DAGGraph(nodes={"call1.out": ConstNode(value=42.0)})
        values = {"call1.out": 42.0}
        result = _resolve_block_outputs(graph, expanded, "call1", values)
        assert result.get("result") == 42.0
