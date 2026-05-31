#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""文件导入/导出功能测试。"""

import json
import tempfile
from pathlib import Path

import pytest

from calc_framework.graph_editor.schema import (
    GraphDocument,
    GraphEdge,
    GraphNode,
    GraphLayout,
    NodeConfig,
    SectionDef,
    ValidationError,
    validate,
)
from calc_framework.graph_editor.registry import create_default_node
from calc_framework.graph_editor.serializer import document_to_dict, document_from_json, document_to_json


class TestExportGraph:
    def test_export_minimal_graph(self) -> None:
        doc = GraphDocument(
            name="测试图",
            description="用于测试",
            nodes=[
                GraphNode(id="n1", type="const", label="常量1", config=NodeConfig(value=10)),
                GraphNode(id="n2", type="const", label="常量2", config=NodeConfig(value=20)),
                GraphNode(id="n3", type="binary", op="+", label="加法"),
            ],
            edges=[GraphEdge(from_node="n1", to_node="n3"), GraphEdge(from_node="n2", to_node="n3")],
            layout=GraphLayout(sections=[
                SectionDef(id="s1", title="结果", output_nodes=["n3"]),
            ]),
        )
        data = document_to_dict(doc)
        assert data["name"] == "测试图"
        assert len(data["nodes"]) == 3
        assert len(data["edges"]) == 2
        assert len(data["layout"]["sections"]) == 1

    def test_export_with_positions(self) -> None:
        doc = GraphDocument(
            name="位置测试",
            nodes=[
                GraphNode(id="a", position={"x": 100, "y": 200}),
            ],
        )
        data = document_to_dict(doc)
        assert data["nodes"][0]["position"]["x"] == 100

    def test_export_roundtrip_file(self) -> None:
        original = GraphDocument(
            name="往返测试",
            nodes=[create_default_node("const", "c1"), create_default_node("binary", "b1")],
            edges=[GraphEdge(from_node="c1", to_node="b1")],
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            f.write(document_to_json(original))
            f.flush()
            tmppath = f.name

        try:
            with open(tmppath, encoding="utf-8") as f:
                restored = document_from_json(json.load(f))
            assert restored.name == original.name
            assert len(restored.nodes) == 2
            assert len(restored.edges) == 1
        finally:
            Path(tmppath).unlink(missing_ok=True)

    def test_export_with_layout(self) -> None:
        doc = GraphDocument(
            name="排版导出",
            nodes=[GraphNode(id="out1", type="output"), GraphNode(id="out2", type="output")],
            layout=GraphLayout(sections=[
                SectionDef(id="s1", title="伤害区", output_nodes=["out1"], columns=2),
                SectionDef(id="s2", title="增益区", output_nodes=["out2"]),
            ]),
        )
        data = document_to_dict(doc)
        assert data["layout"]["sections"][0]["columns"] == 2
        assert data["layout"]["sections"][1]["output_nodes"] == ["out2"]


class TestImportGraph:
    def test_import_minimal_valid(self) -> None:
        raw = {
            "schema_version": "calc-graph-v1",
            "name": "导入测试",
            "description": "",
            "external_variables": {},
            "nodes": [
                {"id": "n1", "type": "const", "label": "常量", "position": {"x": 0, "y": 0},
                 "config": {"value": 5.0}},
            ],
            "edges": [],
            "layout": {"sections": []},
        }
        doc = document_from_json(raw)
        validate(doc)
        assert doc.name == "导入测试"
        assert doc.nodes[0].config.value == 5.0

    def test_import_invalid_file_raises(self) -> None:
        raw = {
            "schema_version": "calc-graph-v1",
            "name": "非法",
            "nodes": [
                {"id": "dup", "type": "const", "label": "A"},
                {"id": "dup", "type": "const", "label": "B"},
            ],
            "edges": [],
            "layout": {"sections": []},
        }
        doc = document_from_json(raw)
        with pytest.raises(ValidationError):
            validate(doc)

    def test_import_file_with_edges(self) -> None:
        raw = {
            "schema_version": "calc-graph-v1",
            "name": "连线图",
            "nodes": [
                {"id": "a", "type": "const", "label": "A", "config": {"value": 42}},
                {"id": "b", "type": "binary", "op": "*", "label": "乘法"},
            ],
            "edges": [
                {"from_node": "a", "from_port": 0, "to_node": "b", "to_port": 0},
            ],
            "layout": {"sections": []},
        }
        doc = document_from_json(raw)
        assert len(doc.edges) == 1
        assert doc.edges[0].from_node == "a"
        assert doc.edges[0].to_node == "b"

    def test_import_and_validate_passes(self) -> None:
        raw = {
            "schema_version": "calc-graph-v1",
            "name": "好图",
            "nodes": [
                {"id": "n1", "type": "const", "label": "C1", "config": {"value": 10}},
                {"id": "n2", "type": "const", "label": "C2", "config": {"value": 20}},
                {"id": "n3", "type": "binary", "op": "+", "label": "求和"},
            ],
            "edges": [
                {"from_node": "n1", "to_node": "n3"},
                {"from_node": "n2", "to_node": "n3"},
            ],
            "layout": {"sections": [{"id": "s1", "title": "结果", "output_nodes": ["n3"]}]},
        }
        doc = document_from_json(raw)
        validate(doc)
