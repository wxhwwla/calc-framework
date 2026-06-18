#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""拖拽连线交互测试。"""

from PySide6.QtCore import QPointF, Qt

from calc_framework.graph_editor.graph_editor_widget import (
    GraphEditorWidget,
)
from calc_framework.graph_editor.ports import PortDirection, PortItem
from calc_framework.graph_editor.schema import GraphNode


def _find_port(port_list: list[PortItem], direction: PortDirection, index: int = 0) -> PortItem:
    for p in port_list:
        if p.direction == direction and p.port_index == index:
            return p

    raise AssertionError(f"未找到端口 direction={direction} index={index}")


def _scene_pos_of_port(w: GraphEditorWidget, node_id: str, direction: PortDirection, index: int = 0) -> QPointF:
    """获取端口的场景坐标。"""

    ports = w.node_ports(node_id)

    port = _find_port(ports, direction, index)

    return port.scene_center()


class TestWireCreation:
    def test_widget_starts_with_no_wires(self, qapp) -> None:
        w = GraphEditorWidget()

        assert len(w.graph_wires()) == 0

    def test_wire_follows_node_when_moved(self, qapp) -> None:
        """移动节点时连线路径跟随更新。"""

        w = GraphEditorWidget()
        w.add_graph_node(GraphNode(id="src", type="const", position={"x": 0, "y": 0}))
        w.add_graph_node(GraphNode(id="dst", type="unary", position={"x": 300, "y": 0}))
        w.show()
        try:
            scene = w.scene()
            src_item = w.find_node_item("src")
            dst_item = w.find_node_item("dst")
            assert src_item is not None
            assert dst_item is not None

            ports_a = w.node_ports("src")
            ports_b = w.node_ports("dst")
            out_a = _find_port(ports_a, PortDirection.OUTPUT)
            in_b = _find_port(ports_b, PortDirection.INPUT, 0)
            w.add_wire(out_a, in_b)

            assert len(w.graph_wires()) == 1
            wire = scene._wires[0]
            path_before = wire.path()

            # 移动源节点
            src_item.setPos(100, 50)
            scene.update()
            path_after = wire.path()

            # 路径应该改变了
            assert path_before != path_after, "连线路径应该在节点移动后更新"
        finally:
            w.close()

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

    def test_wire_creation_via_mouse_events(self, qapp) -> None:
        """通过鼠标事件模拟拖拽连线。"""
        w = GraphEditorWidget()
        # 给节点不同位置防止重叠
        w.add_graph_node(GraphNode(id="src", type="const", position={"x": 0, "y": 0}))
        w.add_graph_node(GraphNode(id="dst", type="unary", position={"x": 300, "y": 0}))
        w.show()
        try:
            scene = w.scene()
            src_pos = _scene_pos_of_port(w, "src", PortDirection.OUTPUT)
            dst_pos = _scene_pos_of_port(w, "dst", PortDirection.INPUT, 0)

            from PySide6.QtWidgets import QGraphicsSceneMouseEvent

            # 按下输出端口
            press = QGraphicsSceneMouseEvent()
            press.setButton(Qt.MouseButton.LeftButton)
            press.setButtons(Qt.MouseButton.LeftButton)
            press.setScenePos(src_pos)
            press.setButtonDownScenePos(Qt.MouseButton.LeftButton, src_pos)
            scene.mousePressEvent(press)

            # 鬼线应已创建
            assert scene._ghost_wire is not None

            # 移动到输入端口附近
            move = QGraphicsSceneMouseEvent()
            move.setScenePos(dst_pos)
            scene.mouseMoveEvent(move)

            # 松开在输入端口
            release = QGraphicsSceneMouseEvent()
            release.setButton(Qt.MouseButton.LeftButton)
            release.setButtons(Qt.MouseButton.LeftButton)
            release.setScenePos(dst_pos)
            scene.mouseReleaseEvent(release)

            # 验证连线已创建
            assert len(w.graph_wires()) == 1
            assert w.graph_wires()[0].from_node == "src"
            assert w.graph_wires()[0].to_node == "dst"
        finally:
            w.close()

    def test_wire_not_created_on_empty_area(self, qapp) -> None:
        """在空白区域松开不创建连线。"""
        w = GraphEditorWidget()
        w.add_graph_node(GraphNode(id="src", type="const"))
        w.show()
        try:
            scene = w.scene()
            src_pos = _scene_pos_of_port(w, "src", PortDirection.OUTPUT)

            from PySide6.QtWidgets import QGraphicsSceneMouseEvent

            press = QGraphicsSceneMouseEvent()
            press.setButton(Qt.MouseButton.LeftButton)
            press.setButtons(Qt.MouseButton.LeftButton)
            press.setScenePos(src_pos)
            press.setButtonDownScenePos(Qt.MouseButton.LeftButton, src_pos)
            scene.mousePressEvent(press)
            assert scene._ghost_wire is not None

            # 在空白位置（远端）松开
            release = QGraphicsSceneMouseEvent()
            release.setButton(Qt.MouseButton.LeftButton)
            release.setButtons(Qt.MouseButton.LeftButton)
            release.setScenePos(QPointF(-999, -999))
            scene.mouseReleaseEvent(release)

            assert len(w.graph_wires()) == 0
            assert scene._ghost_wire is None
            assert scene._wire_start_port is None
        finally:
            w.close()

    def test_wire_not_created_on_same_node(self, qapp) -> None:
        """输出端口不能连接到同一个节点的输入端口。"""
        w = GraphEditorWidget()
        w.add_graph_node(GraphNode(id="n", type="unary"))
        w.show()
        try:
            scene = w.scene()
            out_pos = _scene_pos_of_port(w, "n", PortDirection.OUTPUT)
            in_pos = _scene_pos_of_port(w, "n", PortDirection.INPUT, 0)

            from PySide6.QtWidgets import QGraphicsSceneMouseEvent

            press = QGraphicsSceneMouseEvent()
            press.setButton(Qt.MouseButton.LeftButton)
            press.setButtons(Qt.MouseButton.LeftButton)
            press.setScenePos(out_pos)
            press.setButtonDownScenePos(Qt.MouseButton.LeftButton, out_pos)
            scene.mousePressEvent(press)

            release = QGraphicsSceneMouseEvent()
            release.setButton(Qt.MouseButton.LeftButton)
            release.setButtons(Qt.MouseButton.LeftButton)
            release.setScenePos(in_pos)
            scene.mouseReleaseEvent(release)

            assert len(w.graph_wires()) == 0
        finally:
            w.close()
