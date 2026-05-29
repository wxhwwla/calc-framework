#!/usr/bin/env python3
"""graph.json 序列化/反序列化测试。"""

import json

import pytest
from calc_framework.graph_editor.schema import (
    GraphDocument,
    GraphEdge,
    GraphNode,
    NodeConfig,
    SectionDef,
)
from calc_framework.graph_editor.serializer import (
    document_from_json,
    document_to_dict,
    document_to_json,
)


class TestSerializeMinimal:
    def test_empty_document_roundtrip(self) -> None:
        doc = GraphDocument(name="空图")
        data = document_to_dict(doc)
        assert data["schema_version"] == "calc-graph-v1"
        assert data["name"] == "空图"
        assert data["nodes"] == []
        assert data["edges"] == []

    def test_json_string_roundtrip(self) -> None:
        doc = GraphDocument(name="空图")
        json_str = document_to_json(doc)
        parsed = json.loads(json_str)
        assert parsed["name"] == "空图"

    def test_roundtrip_from_json(self) -> None:
        original = GraphDocument(
            name="往返测试",
            description="描述",
            nodes=[
                GraphNode(id="n1", type="const", label="c1", config=NodeConfig(value=42.0)),
                GraphNode(id="n2", type="binary", op="+", label="加法"),
            ],
            edges=[GraphEdge(from_node="n1", from_port=0, to_node="n2", to_port=0)],
            external_variables={"x": {"type": "float", "source": "computed"}},
        )
        data = document_to_dict(original)
        restored = document_from_json(data)
        assert restored.name == original.name
        assert restored.description == original.description
        assert len(restored.nodes) == 2
        assert len(restored.edges) == 1
        n1 = restored.nodes[0]
        assert n1.id == "n1"
        assert n1.type == "const"
        assert n1.config.value == 42.0
        n2 = restored.nodes[1]
        assert n2.type == "binary"
        assert n2.op == "+"
        assert "x" in restored.external_variables


class TestSerializePositions:
    def test_node_positions_preserved(self) -> None:
        original = GraphDocument(
            name="位置测试",
            nodes=[
                GraphNode(id="n1", position={"x": 150.0, "y": 300.0}),
            ],
        )
        data = document_to_dict(original)
        restored = document_from_json(data)
        assert restored.nodes[0].position["x"] == 150.0
        assert restored.nodes[0].position["y"] == 300.0


class TestSerializeLayout:
    def test_layout_sections_roundtrip(self) -> None:
        sec = SectionDef(id="s1", title="结果区", output_nodes=["o1"], columns=2)
        doc = GraphDocument(
            name="排版测试",
            layout=type("Layout", (), {"sections": [sec]})(),
        )
        data = document_to_dict(doc)
        assert "layout" in data
        assert data["layout"]["sections"][0]["id"] == "s1"
        assert data["layout"]["sections"][0]["title"] == "结果区"
        assert data["layout"]["sections"][0]["columns"] == 2


class TestDeserializeFromRaw:
    def test_load_from_dict(self) -> None:
        raw = {
            "schema_version": "calc-graph-v1",
            "name": "从字典加载",
            "nodes": [
                {"id": "a", "type": "const", "label": "", "position": {"x": 0, "y": 0},
                 "config": {"value": 10}},
            ],
            "edges": [],
            "external_variables": {},
            "layout": {"sections": []},
        }
        doc = document_from_json(raw)
        assert doc.name == "从字典加载"
        assert doc.nodes[0].config.value == 10

    def test_load_node_without_position(self) -> None:
        raw = {
            "schema_version": "calc-graph-v1",
            "name": "无位置",
            "nodes": [
                {"id": "a", "type": "const", "label": "fallback"},
            ],
            "edges": [],
            "layout": {"sections": []},
        }
        doc = document_from_json(raw)
        assert doc.nodes[0].position == {"x": 0.0, "y": 0.0}

    def test_load_node_with_op(self) -> None:
        raw = {
            "schema_version": "calc-graph-v1",
            "name": "运算",
            "nodes": [
                {"id": "a", "type": "binary", "op": "*", "label": "乘法"},
            ],
            "edges": [],
            "layout": {"sections": []},
        }
        doc = document_from_json(raw)
        assert doc.nodes[0].op == "*"
