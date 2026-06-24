# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""画布上的节点图形项。"""

from __future__ import annotations

from PySide6.QtCore import QPointF
from PySide6.QtGui import QBrush, QColor, QFont, QPen
from PySide6.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsSimpleTextItem

from calc_framework.ui.i18n import tr

from .ports import PortDirection, PortItem
from .schema import GraphNode

_NODE_WIDTH = 160

_NODE_HEIGHT = 50

_NODE_BG = QColor("#2D2D2D")

_NODE_BORDER = QColor("#555555")

_NODE_TEXT = QColor("#D1D1D1")

_NODE_TYPE_COLORS: dict[str, QColor] = {
    "const": QColor("#4ECDC4"),
    "var": QColor("#45B7D1"),
    "user_input": QColor("#96CEB4"),
    "unary": QColor("#FFEAA7"),
    "binary": QColor("#FF6B6B"),
    "condition": QColor("#DDA0DD"),
    "output": QColor("#FF8C00"),
    "composite": QColor("#AB47BC"),
}

_FONT = QFont("Microsoft YaHei", 10)

_GRID_SIZE = 40

# 每种节点类型的端口定义：(输入数, 输出数, 输入标签列表, 输出标签列表)

_PORT_SPECS: dict[str, tuple[int, int, list[str], list[str]]] = {
    "const": (0, 1, [], ["value"]),
    "var": (0, 1, [], ["value"]),
    "user_input": (0, 1, [], ["value"]),
    "unary": (1, 1, ["value"], ["result"]),
    "binary": (2, 1, ["lhs", "rhs"], ["result"]),
    "condition": (3, 1, ["cond", "true", "false"], ["result"]),
    "output": (1, 0, ["value"], []),
}


class NodeItem(QGraphicsRectItem):
    """画布上的节点图形项。"""

    def __init__(self, node: GraphNode, parent: QGraphicsItem | None = None) -> None:
        super().__init__(0, 0, _NODE_WIDTH, _NODE_HEIGHT, parent)

        self._node_id = node.id

        self._node_type = node.type

        self._node_op = node.op

        self._node_label = node.label or node.id

        self._config = node.config

        self._ports: list[PortItem] = []

        self._on_double_click: callable | None = None  # type: ignore[valid-type]

        self.setPos(node.position.get("x", 0), node.position.get("y", 0))

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)

        self._setup_appearance()

        self._create_ports()

    def set_double_click_callback(self, cb: callable) -> None:  # type: ignore[valid-type]
        self._on_double_click = cb

    def mouseDoubleClickEvent(self, event) -> None:  # noqa: N802
        if self._node_type == "composite" and self._on_double_click:
            self._on_double_click(self._node_id, self._config.source_graph)

            event.accept()

            return

        super().mouseDoubleClickEvent(event)

    def itemChange(self, change, value):  # noqa: N802
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            # 吸附到网格

            snapped = QPointF(
                round(value.x() / _GRID_SIZE) * _GRID_SIZE,
                round(value.y() / _GRID_SIZE) * _GRID_SIZE,
            )

            return snapped

        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            scene = self.scene()

            if scene is not None:
                for wire in scene._wires:
                    src_parent = wire.source_port.parentItem()

                    tgt_parent = wire.target_port.parentItem()

                    if src_parent is self or tgt_parent is self:
                        wire.update_path()

        return super().itemChange(change, value)

    def _setup_appearance(self) -> None:
        """_setup_appearance。"""
        color = _NODE_TYPE_COLORS.get(self._node_type, _NODE_BORDER)

        self.setBrush(QBrush(_NODE_BG))

        self.setPen(QPen(color, 2))

        self.setCacheMode(QGraphicsItem.CacheMode.DeviceCoordinateCache)

        self._text = QGraphicsSimpleTextItem(self)

        display = self._node_label

        if self._node_op:
            display = f"{self._node_label} [{self._node_op}]"

        self._text.setText(display)

        self._text.setFont(_FONT)

        self._text.setBrush(QBrush(_NODE_TEXT))

        self._text.setPos(10, (_NODE_HEIGHT - self._text.boundingRect().height()) / 2)

        type_tag = QGraphicsSimpleTextItem(self)

        type_tag.setText(self._node_type)

        type_tag.setFont(QFont("Microsoft YaHei", 8))

        type_tag.setBrush(QBrush(QColor("#888888")))

        tr = type_tag.boundingRect()

        type_tag.setPos(_NODE_WIDTH - tr.width() - 8, _NODE_HEIGHT - tr.height() - 4)

    def _create_ports(self) -> None:
        """_create_ports。"""

        if self._node_type == "composite":
            in_labels, out_labels = _composite_port_labels(self._config.source_graph)

            in_count = len(in_labels)

            out_count = len(out_labels)

        else:
            spec = _PORT_SPECS.get(self._node_type, (0, 0, [], []))

            in_count, out_count, in_labels, out_labels = spec

        for i in range(in_count):
            lbl = in_labels[i] if i < len(in_labels) else f"in{i}"

            port = PortItem(PortDirection.INPUT, i, lbl, self)

            port.set_parent_node(self, in_count)

            self._ports.append(port)

        for i in range(out_count):
            lbl = out_labels[i] if i < len(out_labels) else f"out{i}"

            port = PortItem(PortDirection.OUTPUT, i, lbl, self)

            port.set_parent_node(self, out_count)

            self._ports.append(port)

    @property
    def node_id(self) -> str:
        """node_id。"""
        return self._node_id

    @property
    def node_type(self) -> str:
        """node_type。"""

        return self._node_type

    @property
    def ports(self) -> list[PortItem]:
        return self._ports

    def to_graph_node(self) -> GraphNode:
        return GraphNode(
            id=self._node_id,
            type=self._node_type,  # type: ignore[arg-type]
            op=self._node_op,
            label=self._node_label,
            config=self._config,
            position={"x": self.pos().x(), "y": self.pos().y()},
        )


def _composite_port_labels(source_graph: str) -> tuple[list[str], list[str]]:
    """解析子图 JSON，返回 (输入标签列表, 输出标签列表)。"""

    import json

    in_labels: list[str] = []

    out_labels: list[str] = []

    if not source_graph:
        return in_labels, out_labels

    try:
        data = json.loads(source_graph)

        nodes = data.get("nodes", [])

        for n in nodes:
            ntype = n.get("type", "")

            if ntype == "user_input":
                label = n.get("label", "") or n.get("id", tr("desktop.graphEditor.nodeTypeInput"))

                in_labels.append(label)

            elif ntype == "output":
                label = n.get("label", "") or n.get("id", tr("desktop.graphEditor.nodeTypeOutput"))

                out_labels.append(label)

    except Exception:
        pass

    return in_labels, out_labels


def _find_parent_node_id(port: PortItem) -> str | None:
    """_find_parent_node_id。"""

    p = port.parentItem()

    if isinstance(p, NodeItem):
        return p.node_id

    return None
