#!/usr/bin/env python3
"""GraphEditorWidget 画布组件测试。"""

import pytest
from calc_framework.graph_editor.schema import GraphNode, NodeConfig
from calc_framework.graph_editor.graph_editor_widget import (
    GraphScene,
    GraphEditorWidget,
    NodeItem,
)


def _node_items(scene: GraphScene) -> list[NodeItem]:
    return [it for it in scene.items() if isinstance(it, NodeItem)]


class TestGraphScene:
    def test_create_scene(self, qapp) -> None:
        scene = GraphScene()
        assert scene is not None

    def test_add_node_item(self, qapp) -> None:
        scene = GraphScene()
        node = GraphNode(id="n1", type="const", label="测试", config=NodeConfig(value=42))
        item = NodeItem(node)
        scene.addItem(item)
        assert len(_node_items(scene)) == 1

    def test_node_item_rect_size(self, qapp) -> None:
        node = GraphNode(id="n1", type="const", label="常量")
        item = NodeItem(node)
        rect = item.boundingRect()
        assert rect.width() > 0
        assert rect.height() > 0

    def test_node_item_label_in_rect(self, qapp) -> None:
        node = GraphNode(id="n1", type="const", label="42", config=NodeConfig(value=42))
        item = NodeItem(node)
        assert item.node_id == "n1"
        assert item.node_type == "const"

    def test_node_item_holds_position(self, qapp) -> None:
        node = GraphNode(id="n1", position={"x": 200, "y": 150})
        item = NodeItem(node)
        assert item.pos().x() == 200
        assert item.pos().y() == 150


class TestGraphEditorWidget:
    def test_create_widget(self, qapp) -> None:
        widget = GraphEditorWidget()
        assert widget is not None
        assert widget.scene() is not None

    def test_add_node_to_widget(self, qapp) -> None:
        widget = GraphEditorWidget()
        node = GraphNode(id="n1", type="const", label="测试节点")
        widget.add_graph_node(node)
        assert len(widget.graph_nodes()) == 1

    def test_add_multiple_nodes(self, qapp) -> None:
        widget = GraphEditorWidget()
        widget.add_graph_node(GraphNode(id="n1"))
        widget.add_graph_node(GraphNode(id="n2"))
        widget.add_graph_node(GraphNode(id="n3"))
        assert len(widget.graph_nodes()) == 3

    def test_clear_scene(self, qapp) -> None:
        widget = GraphEditorWidget()
        widget.add_graph_node(GraphNode(id="n1"))
        widget.clear_scene()
        assert len(widget.graph_nodes()) == 0

    def test_get_graph_nodes(self, qapp) -> None:
        widget = GraphEditorWidget()
        n1 = GraphNode(id="n1", type="const", label="A")
        n2 = GraphNode(id="n2", type="binary", op="+", label="B")
        widget.add_graph_node(n1)
        widget.add_graph_node(n2)
        nodes = sorted(widget.graph_nodes(), key=lambda n: n.id)
        assert nodes[0].id == "n1"
        assert nodes[1].id == "n2"
        assert nodes[1].op == "+"
