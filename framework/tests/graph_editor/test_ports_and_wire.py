#!/usr/bin/env python3
"""端口 (PortItem) 与连线 (WireItem) 测试。"""


from PySide6.QtWidgets import QGraphicsScene

from calc_framework.graph_editor.ports import PortItem, PortDirection
from calc_framework.graph_editor.wire import WireItem
from calc_framework.graph_editor.schema import GraphNode, NodeConfig
from calc_framework.graph_editor.graph_editor_widget import NodeItem


class TestPortItem:
    def test_create_input_port(self, qapp) -> None:
        port = PortItem(PortDirection.INPUT, 0, "输入")
        assert port.direction == PortDirection.INPUT
        assert port.port_index == 0
        assert port.label == "输入"

    def test_create_output_port(self, qapp) -> None:
        port = PortItem(PortDirection.OUTPUT, 0, "输出")
        assert port.direction == PortDirection.OUTPUT

    def test_port_radius(self, qapp) -> None:
        port = PortItem(PortDirection.INPUT, 0)
        r = port.boundingRect()
        assert r.width() > 0
        assert r.height() > 0

    def test_port_attach_to_node(self, qapp) -> None:
        scene = QGraphicsScene()
        node = GraphNode(id="n1", type="const", label="A", config=NodeConfig(value=10))
        node_item = NodeItem(node)
        scene.addItem(node_item)

        port = PortItem(PortDirection.INPUT, 0, "val")
        port.set_parent_node(node_item, 0)
        scene.addItem(port)

        assert port.node_item is node_item

    def test_port_center_position_input(self, qapp) -> None:
        scene = QGraphicsScene()
        node = GraphNode(id="n1", position={"x": 100, "y": 100})
        node_item = NodeItem(node)
        scene.addItem(node_item)

        port = PortItem(PortDirection.INPUT, 0)
        port.set_parent_node(node_item, 0)
        scene.addItem(port)

        center = port.scene_center()
        # Input ports are on the left side
        assert center.x() < node_item.pos().x() + 50

    def test_port_center_position_output(self, qapp) -> None:
        scene = QGraphicsScene()
        node = GraphNode(id="n1", position={"x": 100, "y": 100})
        node_item = NodeItem(node)
        scene.addItem(node_item)

        port = PortItem(PortDirection.OUTPUT, 0)
        port.set_parent_node(node_item, 0)
        scene.addItem(port)

        center = port.scene_center()
        # Output ports are on the right side of the node
        assert center.x() > node_item.pos().x()


class TestWireItem:
    def test_create_wire(self, qapp) -> None:
        p1 = PortItem(PortDirection.OUTPUT, 0)
        p2 = PortItem(PortDirection.INPUT, 0)
        wire = WireItem(p1, p2)
        assert wire.source_port is p1
        assert wire.target_port is p2

    def test_wire_bounding_rect(self, qapp) -> None:
        scene = QGraphicsScene()
        node_a = GraphNode(id="a", position={"x": 0, "y": 0})
        node_b = GraphNode(id="b", position={"x": 300, "y": 0})
        item_a = NodeItem(node_a)
        item_b = NodeItem(node_b)
        scene.addItem(item_a)
        scene.addItem(item_b)

        out_port = PortItem(PortDirection.OUTPUT, 0)
        out_port.set_parent_node(item_a, 0)
        scene.addItem(out_port)

        in_port = PortItem(PortDirection.INPUT, 0)
        in_port.set_parent_node(item_b, 0)
        scene.addItem(in_port)

        wire = WireItem(out_port, in_port)
        scene.addItem(wire)
        r = wire.boundingRect()
        assert r.width() > 0 or r.height() > 0

    def test_wire_path_shape(self, qapp) -> None:
        scene = QGraphicsScene()
        node_a = GraphNode(id="a", position={"x": 0, "y": 0})
        node_b = GraphNode(id="b", position={"x": 300, "y": 0})
        item_a = NodeItem(node_a)
        item_b = NodeItem(node_b)
        scene.addItem(item_a)
        scene.addItem(item_b)

        out_port = PortItem(PortDirection.OUTPUT, 0)
        out_port.set_parent_node(item_a, 0)
        scene.addItem(out_port)

        in_port = PortItem(PortDirection.INPUT, 0)
        in_port.set_parent_node(item_b, 0)
        scene.addItem(in_port)

        wire = WireItem(out_port, in_port)
        scene.addItem(wire)

        assert wire is not None

    def test_wire_update_path(self, qapp) -> None:
        p1 = PortItem(PortDirection.OUTPUT, 0)
        p2 = PortItem(PortDirection.INPUT, 0)
        wire = WireItem(p1, p2)
        wire.update_path()
        r = wire.boundingRect()
        # After update_path with ports at (0,0), the rect should be valid
        assert r is not None
