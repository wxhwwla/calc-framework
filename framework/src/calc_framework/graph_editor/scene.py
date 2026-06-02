# SPDX-License-Identifier: AGPL-3.0
"""画布场景 — 管理所有节点项和连线创建。"""



from __future__ import annotations

from typing import Any

from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QGraphicsPathItem, QGraphicsScene

from .items import NodeItem, _find_parent_node_id, _GRID_SIZE
from .ports import PortDirection, PortItem
from .wire import WireItem

_BG_COLOR = QColor("#1E1E1E")

_GRID_COLOR = QColor("#2A2A2A")

_BRUSH_BG = QBrush(_BG_COLOR)

_PEN_GRID = QPen(_GRID_COLOR, 1)



class GraphScene(QGraphicsScene):

    """公式编辑器的场景，管理所有节点项和连线创建。"""



    wire_created = Signal(str, str, int, int)  # src_node_id, tgt_node_id, src_port, tgt_port



    def __init__(self, parent: Any = None) -> None:

        super().__init__(parent)

        self.setBackgroundBrush(_BRUSH_BG)

        self.setSceneRect(-2000, -2000, 4000, 4000)

        self._wires: list[WireItem] = []

        self._wire_start_port: PortItem | None = None

        self._ghost_wire: QGraphicsPathItem | None = None



    def drawBackground(self, painter: QPainter, rect: Any) -> None:

        super().drawBackground(painter, rect)

        painter.setPen(_PEN_GRID)

        grid_size = _GRID_SIZE

        left = int(rect.left()) - int(rect.left()) % grid_size

        top = int(rect.top()) - int(rect.top()) % grid_size

        x = left

        while x < int(rect.right()):

            painter.drawLine(x, int(rect.top()), x, int(rect.bottom()))

            x += grid_size

        y = top

        while y < int(rect.bottom()):

            painter.drawLine(int(rect.left()), y, int(rect.right()), y)

            y += grid_size



    def _port_at(self, scene_pos: QPointF) -> PortItem | None:

        """返回场景坐标位置处的端口（跨过非端口项查找）。"""

        for item in self.items(scene_pos):

            if isinstance(item, PortItem):

                return item

        return None



    def mousePressEvent(self, event) -> None:

        if event.button() != Qt.MouseButton.LeftButton:

            super().mousePressEvent(event)

            return

        port = self._port_at(event.scenePos())

        if port is not None and port.direction == PortDirection.OUTPUT:

            self._wire_start_port = port

            self._ghost_wire = QGraphicsPathItem()

            pen = QPen(QColor("#4ECDC4"), 2, Qt.PenStyle.DashLine)

            self._ghost_wire.setPen(pen)

            self._ghost_wire.setZValue(100)

            self.addItem(self._ghost_wire)

            self._update_ghost(event.scenePos())

            event.accept()

            return

        super().mousePressEvent(event)



    def mouseMoveEvent(self, event) -> None:

        if self._wire_start_port and self._ghost_wire:

            self._update_ghost(event.scenePos())

            event.accept()

            return

        super().mouseMoveEvent(event)



    def mouseReleaseEvent(self, event) -> None:

        if self._wire_start_port and self._ghost_wire:

            source_port = self._wire_start_port

            self.removeItem(self._ghost_wire)

            self._ghost_wire = None

            target_port: PortItem | None = None

            port = self._port_at(event.scenePos())

            if port is not None and port.direction == PortDirection.INPUT:

                if port.parentItem() is not source_port.parentItem():

                    target_port = port

            if target_port:

                wire = WireItem(source_port, target_port)

                self.addItem(wire)

                self._wires.append(wire)

                src_node = _find_parent_node_id(source_port)

                tgt_node = _find_parent_node_id(target_port)

                if src_node and tgt_node:

                    self.wire_created.emit(src_node, tgt_node, source_port.port_index, target_port.port_index)

            self._wire_start_port = None

            event.accept()

            return

        super().mouseReleaseEvent(event)



        """_update_ghost。"""
    def _update_ghost(self, scene_pos: QPointF) -> None:

        if not self._wire_start_port or not self._ghost_wire:

            return

        p1 = self._wire_start_port.scene_center()

        p2 = scene_pos

        path = QPainterPath()

        path.moveTo(p1)

        dx = abs(p2.x() - p1.x()) * 0.5

        cp1 = QPointF(p1.x() + dx, p1.y())

        cp2 = QPointF(p2.x() - dx, p2.y())

        path.cubicTo(cp1, cp2, p2)

        self._ghost_wire.setPath(path)




def _node_item_from_id(scene: GraphScene, node_id: str) -> NodeItem | None:

    """_node_item_from_id。"""
    for item in scene.items():

        if isinstance(item, NodeItem) and item.node_id == node_id:

            return item

    return None
