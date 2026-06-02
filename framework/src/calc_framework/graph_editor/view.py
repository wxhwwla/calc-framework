# SPDX-License-Identifier: AGPL-3.0
"""自定义视图 — 中键平移、滚轮缩放、接收节点面板拖放。"""



from __future__ import annotations

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView, QWidget


class GraphView(QGraphicsView):

    """自定义视图：鼠标中键平移、滚轮缩放、接收节点面板拖放。"""



    node_drop_requested = Signal(str, float, float)



    def __init__(self, scene: QGraphicsScene, parent: QWidget | None = None) -> None:

        super().__init__(scene, parent)

        self._panning = False

        self._pan_start = QPoint()

        self._pan_start_h = 0

        self._pan_start_v = 0

        self.setRenderHint(QPainter.RenderHint.Antialiasing)

        self.setDragMode(QGraphicsView.DragMode.NoDrag)

        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)

        self.setAcceptDrops(True)

        self.setMouseTracking(False)



    def wheelEvent(self, event) -> None:  # noqa: N802

        if self._panning:

            event.ignore()

            return

        factor = 1.15

        if event.angleDelta().y() > 0:

            self.scale(factor, factor)

        else:

            self.scale(1 / factor, 1 / factor)



    def mousePressEvent(self, event) -> None:  # noqa: N802

        if event.button() == Qt.MouseButton.MiddleButton:

            self._panning = True

            self._pan_start = event.pos()

            self._pan_start_h = self.horizontalScrollBar().value()

            self._pan_start_v = self.verticalScrollBar().value()

            self.setCursor(Qt.CursorShape.ClosedHandCursor)

            event.accept()

            return

        super().mousePressEvent(event)



    def mouseMoveEvent(self, event) -> None:  # noqa: N802

        if self._panning:

            delta = event.pos() - self._pan_start

            self.horizontalScrollBar().setValue(self._pan_start_h - delta.x())

            self.verticalScrollBar().setValue(self._pan_start_v - delta.y())

            event.accept()

            return

        super().mouseMoveEvent(event)



    def mouseReleaseEvent(self, event) -> None:  # noqa: N802

        if event.button() == Qt.MouseButton.MiddleButton:

            self._panning = False

            self.setCursor(Qt.CursorShape.ArrowCursor)

            event.accept()

            return

        super().mouseReleaseEvent(event)



    def dragEnterEvent(self, event) -> None:  # noqa: N802

        if event.mimeData().hasText():

            event.acceptProposedAction()



    def dragMoveEvent(self, event) -> None:  # noqa: N802

        event.acceptProposedAction()



    def dropEvent(self, event) -> None:  # noqa: N802

        type_id = event.mimeData().text()

        if not type_id:

            return

        viewport_pos = event.position().toPoint()

        scene_pos = self.mapToScene(viewport_pos)

        self.node_drop_requested.emit(type_id, scene_pos.x(), scene_pos.y())

        event.acceptProposedAction()
