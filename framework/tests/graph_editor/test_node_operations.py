#!/usr/bin/env python3
"""节点拖拽、删除、左侧面板测试。"""

import pytest
from PySide6.QtWidgets import QGraphicsScene

from calc_framework.graph_editor.schema import GraphNode
from calc_framework.graph_editor.graph_editor_widget import (
    GraphEditorWidget,
    NodeItem,
)
from calc_framework.graph_editor.ports import PortDirection, PortItem


def _find_port(port_list: list[PortItem], direction: PortDirection, index: int = 0) -> PortItem:
    for p in port_list:
        if p.direction == direction and p.port_index == index:
            return p
    raise AssertionError(f"端口未找到 direction={direction} index={index}")


class TestNodeMoveUpdatesWires:
    def test_wire_updates_on_node_position_change(self, qapp) -> None:
        w = GraphEditorWidget()
        n1 = GraphNode(id="a", type="const", position={"x": 0, "y": 0})
        n2 = GraphNode(id="b", type="binary", op="+", position={"x": 300, "y": 0})
        w.add_graph_node(n1)
        w.add_graph_node(n2)

        pa = _find_port(w.node_ports("a"), PortDirection.OUTPUT)
        pb = _find_port(w.node_ports("b"), PortDirection.INPUT, 0)
        wire = w.add_wire(pa, pb)

        path_before = wire.path()
        # Move node 'a' by 100px
        item_a = w.find_node_item("a")
        item_a.setPos(100, 50)
        wire.update_path()
        path_after = wire.path()
        assert path_before != path_after

    def test_wire_tracks_node_item_change(self, qapp) -> None:
        w = GraphEditorWidget()
        w.add_graph_node(GraphNode(id="a", type="const"))
        w.add_graph_node(GraphNode(id="b", type="binary", op="+"))
        pa = _find_port(w.node_ports("a"), PortDirection.OUTPUT)
        pb = _find_port(w.node_ports("b"), PortDirection.INPUT, 0)
        wire = w.add_wire(pa, pb)
        initial = wire.path()
        item_a = w.find_node_item("a")
        item_a.setPos(200, 200)
        wire.update_path()
        assert wire.path() != initial


class TestDeleteNode:
    def test_remove_node_by_id(self, qapp) -> None:
        w = GraphEditorWidget()
        w.add_graph_node(GraphNode(id="n1", type="const"))
        w.add_graph_node(GraphNode(id="n2", type="const"))
        assert len(w.graph_nodes()) == 2
        w.remove_node("n1")
        nodes = w.graph_nodes()
        assert len(nodes) == 1
        assert nodes[0].id == "n2"

    def test_remove_node_removes_connected_wires(self, qapp) -> None:
        w = GraphEditorWidget()
        w.add_graph_node(GraphNode(id="a", type="const"))
        w.add_graph_node(GraphNode(id="b", type="binary", op="+"))
        pa = _find_port(w.node_ports("a"), PortDirection.OUTPUT)
        pb = _find_port(w.node_ports("b"), PortDirection.INPUT, 0)
        w.add_wire(pa, pb)
        assert len(w.graph_wires()) == 1
        w.remove_node("a")
        assert len(w.graph_wires()) == 0
