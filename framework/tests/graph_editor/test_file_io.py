#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""编辑器状态收集/加载功能测试。"""

import tempfilefrom pathlib import Pathfrom calc_framework.graph_editor.file_actions import (    collect_document,    load_document,    open_graph_file,    save_graph_file,)from calc_framework.graph_editor.graph_editor_widget import GraphEditorWidgetfrom calc_framework.graph_editor.registry import create_default_nodefrom calc_framework.graph_editor.schema import (    GraphDocument,    GraphEdge,    GraphLayout,    GraphNode,    NodeConfig,)class TestCollectDocument:
    def test_collect_empty(self, qapp) -> None:
        widget = GraphEditorWidget()
        doc = collect_document(widget)
        assert doc.name == "未命名"
        assert doc.nodes == []
        assert doc.edges == []

    def test_collect_with_nodes(self, qapp) -> None:
        widget = GraphEditorWidget()
        widget.add_graph_node(create_default_node("const", "n1"))
        widget.add_graph_node(create_default_node("binary", "n2"))
        doc = collect_document(widget)
        assert len(doc.nodes) == 2
        ids = [n.id for n in doc.nodes]
        assert "n1" in ids
        assert "n2" in ids

    def test_collect_with_edges(self, qapp) -> None:
        widget = GraphEditorWidget()
        widget.add_graph_node(create_default_node("const", "n1"))
        widget.add_graph_node(create_default_node("binary", "n2"))
        ports_n1 = widget.node_ports("n1")
        ports_n2 = widget.node_ports("n2")
        widget.add_wire(ports_n1[0], ports_n2[0])
        doc = collect_document(widget)
        assert len(doc.edges) == 1
        assert doc.edges[0].from_node == "n1"

    def test_collect_auto_output_sections(self, qapp) -> None:
        widget = GraphEditorWidget()
        widget.add_graph_node(create_default_node("const", "n1"))
        output_node = GraphNode(id="out1", type="output", label="最终结果")
        widget.add_graph_node(output_node)
        doc = collect_document(widget)
        sections = doc.layout.sections
        assert len(sections) == 1
        assert sections[0].title == "输出"
        assert "out1" in sections[0].output_nodes

    def test_collect_no_output_nodes_no_sections(self, qapp) -> None:
        widget = GraphEditorWidget()
        widget.add_graph_node(create_default_node("const", "n1"))
        widget.add_graph_node(create_default_node("binary", "n2"))
        doc = collect_document(widget)
        assert doc.layout.sections == []

    def test_collect_node_positions(self, qapp) -> None:
        widget = GraphEditorWidget()
        n1 = GraphNode(id="n1", type="const", position={"x": 150, "y": 300})
        widget.add_graph_node(n1)
        doc = collect_document(widget)
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

    def test_load_empty(self, qapp) -> None:
        widget = GraphEditorWidget()
        doc = self._make_doc()
        load_document(doc, widget)
        assert widget.graph_nodes() == []

    def test_load_single_node(self, qapp) -> None:
        widget = GraphEditorWidget()
        n1 = GraphNode(id="c1", type="const", position={"x": 100, "y": 200})
        doc = self._make_doc(nodes=[n1])
        load_document(doc, widget)
        nodes = widget.graph_nodes()
        assert len(nodes) == 1
        assert nodes[0].position["x"] == 100

    def test_load_with_edge(self, qapp) -> None:
        widget = GraphEditorWidget()
        n1 = GraphNode(id="c1", type="const", position={"x": 0, "y": 0})
        n2 = GraphNode(id="b1", type="binary", position={"x": 200, "y": 0})
        doc = self._make_doc(
            nodes=[n1, n2],
            edges=[GraphEdge(from_node="c1", from_port=0, to_node="b1", to_port=0)],
        )
        load_document(doc, widget)
        assert len(widget.graph_nodes()) == 2
        assert len(widget.graph_wires()) == 1

    def test_save_and_reload(self, qapp) -> None:
        widget = GraphEditorWidget()
        n1 = GraphNode(id="c1", type="const", config=NodeConfig(value=42), position={"x": 10, "y": 20})
        n2 = GraphNode(id="o1", type="output", position={"x": 300, "y": 20})
        widget.add_graph_node(n1)
        widget.add_graph_node(n2)
        ports = widget.node_ports("c1")
        ports2 = widget.node_ports("o1")
        widget.add_wire(ports[0], ports2[0])

        doc = collect_document(widget)

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.json"
            save_graph_file(doc, path)
            assert path.exists()
            loaded_doc = open_graph_file(path)
            assert len(loaded_doc.nodes) == 2
            const_node = [n for n in loaded_doc.nodes if n.id == "c1"][0]
            assert const_node.config.value == 42
            assert len(loaded_doc.edges) == 1

    def test_save_and_reload_with_auto_sections(self, qapp) -> None:
        widget = GraphEditorWidget()
        widget.add_graph_node(create_default_node("const", "c1"))
        widget.add_graph_node(GraphNode(id="o1", type="output", label="结果"))

        doc = collect_document(widget)
        assert len(doc.layout.sections) == 1

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.json"
            save_graph_file(doc, path)
            loaded_doc = open_graph_file(path)
            assert len(loaded_doc.layout.sections) == 1
