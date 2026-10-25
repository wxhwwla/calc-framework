# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""DAG 序列化单元测试。"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from calc_framework.dag.graph_types import DAGGraph, DAGOutput, DAGSubgraph, DAGVariable
from calc_framework.dag.node_types import (
    BinaryNode,
    CallNode,
    ConditionNode,
    ConstNode,
    ExprNode,
    UnaryNode,
    UserInputNode,
    VarNode,
)
from calc_framework.dag.serializer import (
    _node_to_dict,
    _variable_to_dict,
    dag_from_dict,
    dag_to_dict,
    load_dag,
    save_dag,
)


class TestVariableToDict:
    def test_minimal(self) -> None:
        d = _variable_to_dict(DAGVariable(type="float", source="user"))
        assert d == {"type": "float", "source": "user"}

    def test_with_all_fields(self) -> None:
        var = DAGVariable(type="float", source="user", description="test var", default=5.0, min=0.0, max=10.0)
        d = _variable_to_dict(var)
        assert d["description"] == "test var"
        assert d["default"] == 5.0
        assert d["min"] == 0.0
        assert d["max"] == 10.0

    def test_with_only_min(self) -> None:
        var = DAGVariable(type="int", source="user", min=1)
        d = _variable_to_dict(var)
        assert d["min"] == 1
        assert "max" not in d
        assert "default" not in d
        assert "description" not in d


class TestNodeToDict:
    def test_const(self) -> None:
        d = _node_to_dict(ConstNode(value=5.0))
        assert d["type"] == "const"
        assert d["value"] == 5.0

    def test_const_with_label(self) -> None:
        d = _node_to_dict(ConstNode(value=5.0, label="five"))
        assert d["label"] == "five"

    def test_var(self) -> None:
        d = _node_to_dict(VarNode(path="x.y"))
        assert d["type"] == "var"
        assert d["path"] == "x.y"

    def test_var_with_desc(self) -> None:
        d = _node_to_dict(VarNode(path="x", description="desc"))
        assert d["description"] == "desc"

    def test_unary(self) -> None:
        d = _node_to_dict(UnaryNode(op="neg", input="n1"))
        assert d["type"] == "unary"
        assert d["input"] == "n1"

    def test_binary(self) -> None:
        d = _node_to_dict(BinaryNode(op="+", lhs="a", rhs="b"))
        assert d["lhs"] == "a"
        assert d["rhs"] == "b"

    def test_condition(self) -> None:
        d = _node_to_dict(ConditionNode(cond="c", true_val="t", false_val="f"))
        assert d["cond"] == "c"
        assert d["true_val"] == "t"
        assert d["false_val"] == "f"

    def test_expr_with_inputs(self) -> None:
        d = _node_to_dict(ExprNode(expr="a + b", inputs={"a": "n1", "b": "n2"}))
        assert d["inputs"]["a"] == "n1"

    def test_expr_without_inputs(self) -> None:
        d = _node_to_dict(ExprNode(expr="5"))
        assert "inputs" not in d

    def test_user_input_full(self) -> None:
        d = _node_to_dict(UserInputNode(default=3.0, min=0.0, max=10.0, step=0.5))
        assert d["type"] == "user_input"
        assert d["step"] == 0.5

    def test_call_with_bindings(self) -> None:
        d = _node_to_dict(CallNode(subgraph="add", bindings={"a": "n1", "b": "n2"}))
        assert d["bindings"]["a"] == "n1"

    def test_call_without_bindings(self) -> None:
        d = _node_to_dict(CallNode(subgraph="add"))
        assert "bindings" not in d


class TestDagToDict:
    def test_minimal(self) -> None:
        g = DAGGraph(name="test", nodes={"n1": ConstNode(value=1.0)})
        d = dag_to_dict(g)
        assert d["schema_version"] == "dag-v1"
        assert d["nodes"]["n1"]["type"] == "const"
        assert "description" not in d
        assert "variables" not in d
        assert "subgraphs" not in d

    def test_with_all_fields(self) -> None:
        g = DAGGraph(
            schema_version="dag-v2",
            name="test",
            description="a test graph",
            variables={"x": DAGVariable(type="float", source="user")},
            subgraphs={
                "add": DAGSubgraph(
                    nodes={"sum": BinaryNode(op="+", lhs="a", rhs="b")},
                    outputs={"out": DAGOutput(node="sum")},
                ),
            },
            nodes={"n1": ConstNode(value=1.0)},
            outputs={"o1": DAGOutput(node="n1", label="out")},
        )
        d = dag_to_dict(g)
        assert d["description"] == "a test graph"
        assert "x" in d["variables"]
        assert "add" in d["subgraphs"]
        assert "o1" in d["outputs"]

    def test_round_trip(self) -> None:
        original = DAGGraph(
            name="test",
            nodes={
                "a": ConstNode(value=2.0),
                "b": ConstNode(value=3.0),
                "sum": BinaryNode(op="+", lhs="a", rhs="b"),
            },
            outputs={"result": DAGOutput(node="sum", label="sum", format=".1f")},
        )
        d = dag_to_dict(original)
        restored = dag_from_dict(d)
        assert isinstance(restored, DAGGraph)
        assert "a" in restored.nodes


class TestSaveLoad:
    def test_save_and_load(self) -> None:
        g = DAGGraph(name="test", nodes={"n1": ConstNode(value=42.0)})
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            p = Path(f.name)
        try:
            save_dag(g, p)
            loaded = load_dag(p)
            assert "n1" in loaded.nodes
        finally:
            p.unlink(missing_ok=True)

    def test_json_content(self) -> None:
        g = DAGGraph(name="test", nodes={"n1": ConstNode(value=42.0)})
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            p = Path(f.name)
        try:
            save_dag(g, p)
            raw = json.loads(p.read_text(encoding="utf-8"))
            assert raw["name"] == "test"
        finally:
            p.unlink(missing_ok=True)
