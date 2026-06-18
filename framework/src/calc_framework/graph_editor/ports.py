# SPDX-License-Identifier: AGPL-3.0
"""端口定义 — 节点的输入/输出连接点。"""

from __future__ import annotations

from enum import Enum, auto

from PySide6.QtCore import QPointF
from PySide6.QtGui import QBrush, QColor, QPen
from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsItem, QGraphicsSceneMouseEvent

_PORT_RADIUS = 6

_PORT_COLOR_INPUT = QColor("#4ECDC4")

_PORT_COLOR_OUTPUT = QColor("#FF6B6B")

_PORT_BORDER = QColor("#333333")


class PortDirection(Enum):
    """PortDirection。"""

    INPUT = auto()

    OUTPUT = auto()


class PortItem(QGraphicsEllipseItem):
    """节点的输入/输出端口。"""

    def __init__(
        self,
        direction: PortDirection,
        port_index: int = 0,
        label: str = "",
        parent: QGraphicsItem | None = None,
    ) -> None:
        r = _PORT_RADIUS

        super().__init__(-r, -r, r * 2, r * 2, parent)

        self._direction = direction

        self._port_index = port_index

        self._label = label

        self._node_item: QGraphicsItem | None = None

        color = _PORT_COLOR_INPUT if direction == PortDirection.INPUT else _PORT_COLOR_OUTPUT

        self.setBrush(QBrush(color))

        self.setPen(QPen(_PORT_BORDER, 1.5))

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)

        self.setZValue(10)

    @property
    def direction(self) -> PortDirection:
        """direction。"""
        return self._direction

    @property
    def port_index(self) -> int:
        """port_index。"""

        return self._port_index

    @property
    def label(self) -> str:
        return self._label

    @property
    def node_item(self) -> QGraphicsItem | None:
        return self._node_item

    def set_parent_node(self, node_item: QGraphicsItem, port_count: int) -> None:
        """将端口附着到节点上，根据方向计算偏移位置。"""

        self._node_item = node_item

        node_rect = node_item.boundingRect()

        spacing = node_rect.height() / max(port_count + 1, 2)

        x = -_PORT_RADIUS if self._direction == PortDirection.INPUT else node_rect.width() + _PORT_RADIUS

        y = spacing * (self._port_index + 1)

        self.setPos(x, y)

    def scene_center(self) -> QPointF:
        return self.mapToScene(self.boundingRect().center())

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent | None) -> None:  # noqa: N802
        if event is not None:
            event.ignore()

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent | None) -> None:  # noqa: N802
        if event is not None:
            event.ignore()
