"""可视化公式编辑画布 — PySide6 QGraphicsView 实现。"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QPoint, QPointF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
    QGraphicsView,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from calc_framework.graph_editor.ports import PortDirection, PortItem
from calc_framework.graph_editor.schema import GraphEdge, GraphNode
from calc_framework.graph_editor.wire import WireItem

_NODE_WIDTH = 160
_NODE_HEIGHT = 50
_BG_COLOR = QColor("#1E1E1E")
_GRID_COLOR = QColor("#2A2A2A")
_GRID_SIZE = 40
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

_BRUSH_BG = QBrush(_BG_COLOR)
_PEN_GRID = QPen(_GRID_COLOR, 1)
_FONT = QFont("Microsoft YaHei", 10)

# 每种节点类型的端口定义：(输入数, 输出数, 输入标签列表, 输出标签列表)
_PORT_SPECS: dict[str, tuple[int, int, list[str], list[str]]] = {
    "const":       (0, 1, [],          ["value"]),
    "var":         (0, 1, [],          ["value"]),
    "user_input":  (0, 1, [],          ["value"]),
    "unary":       (1, 1, ["value"],   ["result"]),
    "binary":      (2, 1, ["lhs", "rhs"], ["result"]),
    "condition":   (3, 1, ["cond", "true", "false"], ["result"]),
    "output":      (1, 0, ["value"],   []),
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
        self._on_double_click: callable | None = None

        self.setPos(node.position.get("x", 0), node.position.get("y", 0))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)

        self._setup_appearance()
        self._create_ports()

    def set_double_click_callback(self, cb: callable) -> None:
        self._on_double_click = cb

    def mouseDoubleClickEvent(self, event) -> None:
        if self._node_type == "composite" and self._on_double_click:
            self._on_double_click(self._node_id, self._config.source_graph)
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def itemChange(self, change, value):
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
        return self._node_id

    @property
    def node_type(self) -> str:
        return self._node_type

    @property
    def ports(self) -> list[PortItem]:
        return self._ports

    def to_graph_node(self) -> GraphNode:
        return GraphNode(
            id=self._node_id,
            type=self._node_type,
            op=self._node_op,
            label=self._node_label,
            config=self._config,
            position={"x": self.pos().x(), "y": self.pos().y()},
        )


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
    for item in scene.items():
        if isinstance(item, NodeItem) and item.node_id == node_id:
            return item
    return None


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

    def wheelEvent(self, event) -> None:
        if self._panning:
            event.ignore()
            return
        factor = 1.15
        if event.angleDelta().y() > 0:
            self.scale(factor, factor)
        else:
            self.scale(1 / factor, 1 / factor)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._pan_start = event.pos()
            self._pan_start_h = self.horizontalScrollBar().value()
            self._pan_start_v = self.verticalScrollBar().value()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._panning:
            delta = event.pos() - self._pan_start
            self.horizontalScrollBar().setValue(self._pan_start_h - delta.x())
            self.verticalScrollBar().setValue(self._pan_start_v - delta.y())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event) -> None:
        event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        type_id = event.mimeData().text()
        if not type_id:
            return
        viewport_pos = event.position().toPoint()
        scene_pos = self.mapToScene(viewport_pos)
        self.node_drop_requested.emit(type_id, scene_pos.x(), scene_pos.y())
        event.acceptProposedAction()


class GraphEditorWidget(QWidget):
    """公式编辑器主组件。

    包含 GraphScene + GraphView，支持：
    - 添加/删除节点
    - 中键平移
    - 滚轮缩放
    - 网格背景
    - 连线创建（从输出端口拖到输入端口）
    - 拖放创建节点（从节点面板拖入）
    """

    node_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._scene = GraphScene(self)
        self._view = GraphView(self._scene)
        self._view.node_drop_requested.connect(self._on_drop_node)
        self._scene.wire_created.connect(self._on_wire_created)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._view)

    def _on_drop_node(self, type_id: str, scene_x: float, scene_y: float) -> None:
        from calc_framework.graph_editor.registry import create_default_node
        node = create_default_node(type_id)
        snap_x = round((scene_x - _NODE_WIDTH / 2) / _GRID_SIZE) * _GRID_SIZE
        snap_y = round((scene_y - _NODE_HEIGHT / 2) / _GRID_SIZE) * _GRID_SIZE
        node.position = {"x": snap_x, "y": snap_y}
        self.add_graph_node(node)

    def _on_wire_created(self, src_id: str, tgt_id: str, src_port: int, tgt_port: int) -> None:
        self.node_changed.emit()

    def scene(self) -> GraphScene:
        return self._scene

    def add_graph_node(self, node: GraphNode) -> NodeItem:
        item = NodeItem(node)
        if node.type == "composite":
            item.set_double_click_callback(self._open_subgraph_editor)
        self._scene.addItem(item)
        self.node_changed.emit()
        return item

    def node_ports(self, node_id: str) -> list[PortItem]:
        item = _node_item_from_id(self._scene, node_id)
        if item is None:
            return []
        return item.ports

    def view(self) -> GraphView:
        return self._view

    def fit_all(self) -> None:
        """缩放画布以适配所有节点。"""
        items = [it for it in self._scene.items() if isinstance(it, NodeItem)]
        if not items:
            return
        from PySide6.QtCore import QRectF
        bounds = QRectF()
        for it in items:
            bounds = bounds.united(it.sceneBoundingRect())
        margin = 80
        bounds.adjust(-margin, -margin, margin, margin)
        self._view.fitInView(bounds, Qt.AspectRatioMode.KeepAspectRatio)

    def reset_zoom(self) -> None:
        """重置缩放为 100%。"""
        self._view.resetTransform()

    def find_node_item(self, node_id: str) -> NodeItem | None:
        return _node_item_from_id(self._scene, node_id)

    def remove_node(self, node_id: str) -> None:
        item = _node_item_from_id(self._scene, node_id)
        if item is None:
            return
        remaining_wires: list[WireItem] = []
        for w in self._scene._wires:
            src_id = _find_parent_node_id(w.source_port)
            tgt_id = _find_parent_node_id(w.target_port)
            if src_id == node_id or tgt_id == node_id:
                self._scene.removeItem(w)
            else:
                remaining_wires.append(w)
        self._scene._wires = remaining_wires
        self._scene.removeItem(item)
        self.node_changed.emit()

    def add_wire(self, source: PortItem, target: PortItem) -> WireItem:
        wire = WireItem(source, target)
        self._scene.addItem(wire)
        self._scene._wires.append(wire)
        self.node_changed.emit()
        return wire

    def graph_wires(self) -> list[GraphEdge]:
        edges: list[GraphEdge] = []
        for wire in self._scene._wires:
            src_node = _find_parent_node_id(wire.source_port)
            tgt_node = _find_parent_node_id(wire.target_port)
            if src_node and tgt_node:
                edges.append(GraphEdge(
                    from_node=src_node,
                    from_port=wire.source_port.port_index,
                    to_node=tgt_node,
                    to_port=wire.target_port.port_index,
                ))
        return edges

    def graph_nodes(self) -> list[GraphNode]:
        nodes: list[GraphNode] = []
        for item in self._scene.items():
            if isinstance(item, NodeItem):
                nodes.append(item.to_graph_node())
        return nodes

    def clear_scene(self) -> None:
        self._scene.clear()
        self._scene._wires.clear()
        self._scene._wire_start_port = None
        self._scene._ghost_wire = None
        self.node_changed.emit()

    # ── 子图编辑器（复合节点双击） ──

    def _open_subgraph_editor(self, node_id: str, source_graph: str) -> None:
        if not source_graph:
            QMessageBox.information(self, "子图编辑器", "该复合节点没有嵌入的子图数据。")
            return
        dialog = SubGraphDialog(source_graph, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_json = dialog.get_graph_json()
            if new_json and new_json != source_graph:
                # 更新节点配置
                item = self.find_node_item(node_id)
                if item is not None:
                    item._config.source_graph = new_json
                    # 重建端口
                    for port in item._ports[:]:
                        item.scene().removeItem(port)
                    item._ports.clear()
                    item._create_ports()
                    self.node_changed.emit()


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
                label = n.get("label", "") or n.get("id", "输入")
                in_labels.append(label)
            elif ntype == "output":
                label = n.get("label", "") or n.get("id", "输出")
                out_labels.append(label)
    except Exception:
        pass
    return in_labels, out_labels


class SubGraphDialog(QDialog):
    """子图编辑器对话框 — 双击复合节点时打开。"""

    def __init__(self, source_graph: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("子图编辑器")
        self.resize(800, 600)

        from calc_framework.graph_editor.serializer import document_from_json
        from calc_framework.graph_editor.file_actions import load_document
        from calc_framework.graph_editor.prop_panel import PropPanel

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 子图的 GraphEditorWidget
        from calc_framework.graph_editor.graph_editor_widget import GraphEditorWidget
        self._editor = GraphEditorWidget()
        self._prop_panel = PropPanel(self._editor)

        # 加载子图
        self._source_graph = source_graph
        try:
            data = json.loads(source_graph)
            doc = document_from_json(data)
            load_document(doc, self._editor)
        except Exception:
            pass

        # 把编辑器放到对话框里
        from PySide6.QtWidgets import QSplitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self._editor)
        right_panel = QWidget()
        rl = QVBoxLayout(right_panel)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.addWidget(self._prop_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([550, 250])

        layout.addWidget(splitter, 1)

        # 底部按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # 选节点时更新属性面板
        self._editor.scene().selectionChanged.connect(self._on_selection_changed)

    def _on_selection_changed(self) -> None:
        selected = self._editor.scene().selectedItems()
        node_item = None
        for item in selected:
            if isinstance(item, NodeItem):
                node_item = item
                break
        if node_item is not None:
            self._prop_panel.show_node(node_item)
        else:
            self._prop_panel.show_node(None)

    def get_graph_json(self) -> str:
        """获取编辑后的子图 JSON。"""
        from calc_framework.graph_editor.file_actions import collect_document
        from calc_framework.graph_editor.serializer import document_to_json
        doc = collect_document(self._editor)
        return document_to_json(doc)


def _find_parent_node_id(port: PortItem) -> str | None:
    p = port.parentItem()
    if isinstance(p, NodeItem):
        return p.node_id
    return None
