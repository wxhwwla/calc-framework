# SPDX-License-Identifier: AGPL-3.0
"""连线绘制 — 端口之间的贝塞尔曲线。"""

from __future__ import annotations

from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QGraphicsItem, QGraphicsPathItem

from .ports import PortItem

_WIRE_COLOR = QColor("#888888")

_WIRE_WIDTH = 2.0

_WIRE_HIGHLIGHT = QColor("#4ECDC4")


class WireItem(QGraphicsPathItem):
    """连接两个端口的贝塞尔曲线。"""

    def __init__(self, source: PortItem, target: PortItem, parent: QGraphicsItem | None = None) -> None:
        super().__init__(parent)

        self._source = source

        self._target = target

        self.setPen(QPen(_WIRE_COLOR, _WIRE_WIDTH))

        self.setZValue(5)

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)

        self.update_path()

    @property
    def source_port(self) -> PortItem:
        """source_port。"""
        return self._source

    @property
    def target_port(self) -> PortItem:
        """target_port。"""

        return self._target

    def update_path(self) -> None:
        """重算贝塞尔曲线路径。"""

        p1 = self._source.scene_center()

        p2 = self._target.scene_center()

        path = QPainterPath()

        path.moveTo(p1)

        dx = abs(p2.x() - p1.x()) * 0.5

        cp1 = QPointF(p1.x() + dx, p1.y())

        cp2 = QPointF(p2.x() - dx, p2.y())

        path.cubicTo(cp1, cp2, p2)

        self.setPath(path)

    def paint(self, painter: QPainter | None, option: object, widget: object | None = None) -> None:
        if painter is None:
            return

        if self.isSelected():
            painter.setPen(QPen(_WIRE_HIGHLIGHT, _WIRE_WIDTH + 1))

        else:
            painter.setPen(QPen(_WIRE_COLOR, _WIRE_WIDTH))

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.drawPath(self.path())
