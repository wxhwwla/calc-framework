# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""DAGState 增量求值状态单元测试。"""

from __future__ import annotations

from calc_framework.dag.graph_types import DAGGraph
from calc_framework.dag.node_types import (
    ConstNode,
    VarNode,
)
from calc_framework.dag.state import (
    DAGState,
    compute_affected_nodes,
    compute_context_hash,
    find_changed_paths,
    flatten_context,
)


class TestFlattenContext:
    def test_empty(self) -> None:
        assert flatten_context({}) == {}

    def test_simple(self) -> None:
        assert flatten_context({"a": 1.0}) == {"a": 1.0}

    def test_nested(self) -> None:
        result = flatten_context({"character": {"atk": 100.0, "def": 50.0}})
        assert result == {"character.atk": 100.0, "character.def": 50.0}

    def test_int_conversion(self) -> None:
        result = flatten_context({"a": 1})
        assert result == {"a": 1.0}

    def test_skips_non_numeric(self) -> None:
        """非数值类型（字符串、列表）生成稳定哈希键而非丢弃。"""
        result = flatten_context({"a": 1.0, "b": "hello", "c": [1, 2]})
        # 数值键保持原值
        assert result["a"] == 1.0
        # 字符串键被哈希为稳定浮点值
        assert isinstance(result["b"], float)
        # 列表元素被递归展平
        assert result["c[0]"] == 1.0
        assert result["c[1]"] == 2.0


class TestComputeContextHash:
    def test_stable_hash(self) -> None:
        h1 = compute_context_hash({"a": 1.0, "b": 2.0})
        h2 = compute_context_hash({"b": 2.0, "a": 1.0})
        assert h1 == h2

    def test_differs_on_value(self) -> None:
        h1 = compute_context_hash({"a": 1.0})
        h2 = compute_context_hash({"a": 2.0})
        assert h1 != h2


class TestFindChangedPaths:
    def test_no_changes(self) -> None:
        assert find_changed_paths({"a": 1.0}, {"a": 1.0}) == set()

    def test_added_key(self) -> None:
        changed = find_changed_paths({"a": 1.0}, {"a": 1.0, "b": 2.0})
        assert "b" in changed

    def test_removed_key(self) -> None:
        changed = find_changed_paths({"a": 1.0, "b": 2.0}, {"a": 1.0})
        assert "b" in changed

    def test_modified_value(self) -> None:
        changed = find_changed_paths({"a": 1.0}, {"a": 2.0})
        assert "a" in changed


class TestComputeAffectedNodes:
    def test_finds_var_node_by_path(self) -> None:
        graph = DAGGraph(
            nodes={
                "v1": VarNode(path="character.atk"),
                "c1": ConstNode(value=5.0),
            }
        )
        affected = compute_affected_nodes(graph, {"character.atk"})
        assert "v1" in affected
        assert "c1" not in affected

    def test_no_match(self) -> None:
        graph = DAGGraph(
            nodes={
                "v1": VarNode(path="character.atk"),
            }
        )
        affected = compute_affected_nodes(graph, {"enemy.def"})
        assert len(affected) == 0


class TestDAGState:
    def test_initial_state(self) -> None:
        state = DAGState()
        assert state.node_values == {}
        assert state.context_hash == 0
        assert state.evaluation_count == 0

    def test_reset(self) -> None:
        state = DAGState()
        state.node_values["n1"] = 1.0
        state.context_hash = 12345
        state.evaluation_count = 5
        state.reset()
        assert state.node_values == {}
        assert state.context_hash == 0
        assert state.evaluation_count == 0
