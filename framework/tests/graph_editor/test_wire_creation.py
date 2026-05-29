#!/usr/bin/env python3
"""拖拽连线交互测试。"""

import pytest
from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QGraphicsScene

from calc_framework.graph_editor.schema import GraphNode
from calc_framework.graph_editor.graph_editor_widget import (
    GraphEditorWidget,
    GraphScene,
    NodeItem,
)
from calc_framework.graph_editor.ports import PortDirection, PortItem
from calc_framework.graph_editor.wire import WireItem


def _find_port(port_list: list[PortItem], direction: PortDirection, index: int = 0) -> PortItem:
    for p in port_list:
        if p.direction == direction and p.port_index == index:
            return p
    raise AssertionError(f"未找到端口 direction={direction} index={index}")


class TestWireCreation:
    def test_widget_starts_with_no_wires(self, qapp) -> None:
        w = GraphEditorWidget()
        assert len(w.graph_wires()) == 0

    def test_add_wire_via_method(self, qapp) -> None:
        w = GraphEditorWidget()
        n1 = GraphNode(id="a", type="const", label="A")
        n2 = GraphNode(id="b", type="binary", op="+", label="B")
        w.add_graph_node(n1)
        w.add_graph_node(n2)

        ports_a = w.node_ports("a")
        ports_b = w.node_ports("b")
        out_a = _find_port(ports_a, PortDirection.OUTPUT)
        in_b = _find_port(ports_b, PortDirection.INPUT)
        w.add_wire(out_a, in_b)

        assert len(w.graph_wires()) == 1

    def test_add_multiple_wires(self, qapp) -> None:
        w = GraphEditorWidget()
        n1 = GraphNode(id="a", type="const")
        n2 = GraphNode(id="b", type="const")
        n3 = GraphNode(id="c", type="binary", op="+")
        w.add_graph_node(n1)
        w.add_graph_node(n2)
        w.add_graph_node(n3)

        w.add_wire(
            _find_port(w.node_ports("a"), PortDirection.OUTPUT),
            _find_port(w.node_ports("c"), PortDirection.INPUT, 0),
        )
        w.add_wire(
            _find_port(w.node_ports("b"), PortDirection.OUTPUT),
            _find_port(w.node_ports("c"), PortDirection.INPUT, 1),
        )
        assert len(w.graph_wires()) == 2

    def test_graph_wires_returns_edges(self, qapp) -> None:
        w = GraphEditorWidget()
        w.add_graph_node(GraphNode(id="a", type="const"))
        w.add_graph_node(GraphNode(id="b", type="binary", op="+"))
        ports_a = w.node_ports("a")
        ports_b = w.node_ports("b")
        w.add_wire(
            _find_port(ports_a, PortDirection.OUTPUT),
            _find_port(ports_b, PortDirection.INPUT, 0),
        )

        edges = w.graph_wires()
        assert len(edges) == 1
        assert edges[0].from_node == "a"
        assert edges[0].to_node == "b"
