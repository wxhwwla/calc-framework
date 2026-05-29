"""块级缓存单元测试。"""

from __future__ import annotations

import pytest

from calc_framework.dag.engine import BlockCache, evaluate_graph
from calc_framework.dag.serializer import dag_from_dict

_BLOCK_DAG = {
    "schema_version": "dag-v1",
    "name": "块测试图",
    "variables": {
        "character.a": {"type": "float", "source": "character"},
        "character.b": {"type": "float", "source": "character"},
    },
    "subgraphs": {
        "add_block": {
            "description": "加法块",
            "parameters": {
                "x": {"type": "float", "source": "computed"},
                "y": {"type": "float", "source": "computed"},
            },
            "nodes": {
                "sum": {"type": "binary", "op": "+", "lhs": "x", "rhs": "y", "label": "x+y"},
            },
            "outputs": {
                "result": {"node": "sum", "label": "结果", "is_primary": True},
            },
        },
        "mul_block": {
            "description": "乘法块",
            "parameters": {
                "v": {"type": "float", "source": "computed"},
            },
            "nodes": {
                "double": {"type": "binary", "op": "*", "lhs": "v", "rhs": "v", "label": "v*v"},
            },
            "outputs": {
                "result": {"node": "double", "label": "平方", "is_primary": True},
            },
        },
    },
    "nodes": {
        "var_a": {"type": "var", "path": "character.a", "label": "a"},
        "var_b": {"type": "var", "path": "character.b", "label": "b"},
        "block_add": {
            "type": "call",
            "subgraph": "add_block",
            "bindings": {"x": "var_a", "y": "var_b"},
            "label": "加法块",
        },
        "block_mul": {
            "type": "call",
            "subgraph": "mul_block",
            "bindings": {"v": "block_add"},
            "label": "乘法块",
        },
    },
    "outputs": {
        "add_result": {"node": "block_add", "label": "a+b"},
        "mul_result": {"node": "block_mul", "label": "(a+b)²"},
    },
}


class TestBlockCache:
    def test_cache_miss_returns_none(self) -> None:
        cache = BlockCache()
        result = cache.get("block_add", {"x": 1.0, "y": 2.0})
        assert result is None

    def test_cache_hit_returns_cached_values(self) -> None:
        cache = BlockCache()
        cache.put("block_add", {"x": 1.0, "y": 2.0}, {"result": 3.0})
        result = cache.get("block_add", {"x": 1.0, "y": 2.0})
        assert result == {"result": 3.0}

    def test_cache_miss_after_input_change(self) -> None:
        cache = BlockCache()
        cache.put("block_add", {"x": 1.0, "y": 2.0}, {"result": 3.0})
        result = cache.get("block_add", {"x": 5.0, "y": 2.0})
        assert result is None

    def test_invalidate_removes_entry(self) -> None:
        cache = BlockCache()
        cache.put("block_add", {"x": 1.0, "y": 2.0}, {"result": 3.0})
        cache.invalidate("block_add")
        result = cache.get("block_add", {"x": 1.0, "y": 2.0})
        assert result is None

    def test_invalidate_all(self) -> None:
        cache = BlockCache()
        cache.put("block_add", {"x": 1.0, "y": 2.0}, {"result": 3.0})
        cache.put("block_mul", {"v": 3.0}, {"result": 9.0})
        cache.invalidate_all()
        assert cache.get("block_add", {"x": 1.0, "y": 2.0}) is None
        assert cache.get("block_mul", {"v": 3.0}) is None

    def test_multiple_blocks_independent(self) -> None:
        cache = BlockCache()
        cache.put("block_add", {"x": 1.0, "y": 2.0}, {"result": 3.0})
        cache.put("block_mul", {"v": 3.0}, {"result": 9.0})
        # Change block_add inputs
        cache.put("block_add", {"x": 10.0, "y": 20.0}, {"result": 30.0})
        # block_mul unchanged
        assert cache.get("block_add", {"x": 1.0, "y": 2.0}) is None
        assert cache.get("block_mul", {"v": 3.0}) == {"result": 9.0}

    def test_cache_preserves_output_across_evaluations(self) -> None:
        """BlockCache survives across evaluate_graph calls (passed as arg)."""
        g = dag_from_dict(_BLOCK_DAG)
        cache = BlockCache()

        # First eval — uncached
        r1 = evaluate_graph(g, {"character": {"a": 3.0, "b": 4.0}}, block_cache=cache)
        assert r1.outputs["add_result"] == 7.0
        assert r1.outputs["mul_result"] == 49.0  # (3+4)²

        # Second eval — same inputs, blocks should hit cache
        r2 = evaluate_graph(g, {"character": {"a": 3.0, "b": 4.0}}, block_cache=cache)
        assert r2.outputs["add_result"] == 7.0
        assert r2.outputs["mul_result"] == 49.0

    def test_different_inputs_force_re_evaluation(self) -> None:
        g = dag_from_dict(_BLOCK_DAG)
        cache = BlockCache()

        r1 = evaluate_graph(g, {"character": {"a": 3.0, "b": 4.0}}, block_cache=cache)
        assert r1.outputs["add_result"] == 7.0

        # Change input b
        r2 = evaluate_graph(g, {"character": {"a": 3.0, "b": 10.0}}, block_cache=cache)
        assert r2.outputs["add_result"] == 13.0
