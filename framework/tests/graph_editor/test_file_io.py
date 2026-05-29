#!/usr/bin/env python3
"""编辑器状态收集/加载功能测试。"""

import tempfile
from pathlib import Path

import pytest

from calc_framework.graph_editor.file_actions import (
    collect_document,
    load_document,
    save_graph_file,
    open_graph_file,
)
from calc_framework.graph_editor.graph_editor_widget import GraphEditorWidget
from calc_framework.graph_editor.layout_panel import LayoutPanel
from calc_framework.graph_editor.registry import create_default_node
from calc_framework.graph_editor.schema import (
    GraphDocument,
    GraphEdge,
    GraphLayout,
    GraphNode,
    NodeConfig,
    SectionDef,
)


class TestCollectDocument:
    def test_collect_empty(self, qapp) -> None:
        widget = GraphEditorWidget()
        panel = LayoutPanel()
        doc = collect_document(widget, panel)
        assert doc.name == "未命名"
        assert doc.nodes == []
        assert doc.edges == []
        assert doc.layout.sections == []

    def test_collect_with_nodes(self, qapp) -> None:
        widget = GraphEditorWidget()
        panel = LayoutPanel()
        widget.add_graph_node(create_default_node("const", "n1"))
        widget.add_graph_node(create_default_node("binary", "n2"))
        doc = collect_document(widget, panel)
        assert len(doc.nodes) == 2
        ids = [n.id for n in doc.nodes]
        assert "n1" in ids
        assert "n2" in ids

    def test_collect_with_edges(self, qapp) -> None:
        widget = GraphEditorWidget()
        panel = LayoutPanel()
        widget.add_graph_node(create_default_node("const", "n1"))
        widget.add_graph_node(create_default_node("binary", "n2"))
        ports_n1 = widget.node_ports("n1")
        ports_n2 = widget.node_ports("n2")
        widget.add_wire(ports_n1[0], ports_n2[0])
        doc = collect_document(widget, panel)
        assert len(doc.edges) == 1
        assert doc.edges[0].from_node == "n1"

    def test_collect_with_layout(self, qapp) -> None:
        widget = GraphEditorWidget()
        panel = LayoutPanel()
        panel.add_section("结果", ["out1"])
        doc = collect_document(widget, panel)
        assert len(doc.layout.sections) == 1
        assert doc.layout.sections[0].title == "结果"

    def test_collect_node_positions(self, qapp) -> None:
        widget = GraphEditorWidget()
        panel = LayoutPanel()
        n1 = GraphNode(id="n1", type="const", position={"x": 150, "y": 300})
        widget.add_graph_node(n1)
        doc = collect_document(widget, panel)
        assert doc.nodes[0].position["x"] == 150
        assert doc.nodes[0].position["y"] == 300


class TestLoadDocument:
    def _make_doc(self, name: str = "test", nodes=None, edges=None, sections=None) -> GraphDocument:
        return GraphDocument(
            name=name,
            nodes=nodes or [],
            edges=edges or [],
            layout=GraphLayout(sections=sections or []),
        )

    def test_load_nodes(self, qapp) -> None:
        widget = GraphEditorWidget()
        panel = LayoutPanel()
        doc = self._make_doc(nodes=[
            GraphNode(id="n1", type="const", config=NodeConfig(value=42)),
            GraphNode(id="n2", type="binary", op="+"),
        ])
        load_document(doc, widget, panel)
        assert len(widget.graph_nodes()) == 2

    def test_load_with_edges(self, qapp) -> None:
        widget = GraphEditorWidget()
        panel = LayoutPanel()
        n1 = GraphNode(id="n1", type="const", config=NodeConfig(value=10))
        n2 = GraphNode(id="n2", type="binary", op="+")
        doc = self._make_doc(nodes=[n1, n2], edges=[
            GraphEdge(from_node="n1", from_port=0, to_node="n2", to_port=0),
        ])
        load_document(doc, widget, panel)
        assert len(widget.graph_wires()) == 1

    def test_load_with_layout(self, qapp) -> None:
        widget = GraphEditorWidget()
        panel = LayoutPanel()
        sec = SectionDef(id="s1", title="结果", output_nodes=["out1"])
        doc = self._make_doc(sections=[sec])
        load_document(doc, widget, panel)
        assert len(panel.sections()) == 1
        assert panel.sections()[0].title == "结果"

    def test_load_clears_before(self, qapp) -> None:
        widget = GraphEditorWidget()
        panel = LayoutPanel()
        widget.add_graph_node(create_default_node("const", "old"))
        panel.add_section("旧节")

        doc = self._make_doc(nodes=[GraphNode(id="new1", type="const")])
        load_document(doc, widget, panel)
        assert len(widget.graph_nodes()) == 1
        assert widget.graph_nodes()[0].id == "new1"
        assert len(panel.sections()) == 0


class TestSaveOpenFile:
    def test_save_and_open(self, qapp) -> None:
        widget = GraphEditorWidget()
        panel = LayoutPanel()
        widget.add_graph_node(GraphNode(id="out1", type="output"))
        panel.add_section("结果", ["out1"])

        doc1 = collect_document(widget, panel)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8",
        ) as f:
            fname = Path(f.name)
            save_graph_file(doc1, fname)

        try:
            widget2 = GraphEditorWidget()
            panel2 = LayoutPanel()
            doc2 = open_graph_file(fname)
            load_document(doc2, widget2, panel2)

            assert len(panel2.sections()) == 1
            assert panel2.sections()[0].title == "结果"
        finally:
            if fname.exists():
                fname.unlink()
