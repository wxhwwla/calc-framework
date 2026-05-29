"""可视化公式编辑画布 — PySide6 QGraphicsView 实现。"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
    QGraphicsView,
    QVBoxLayout,
    QWidget,
)

from calc_framework.graph_editor.ports import PortDirection, PortItem
from calc_framework.graph_editor.schema import GraphEdge, GraphNode, NodeConfig
from calc_framework.graph_editor.wire import WireItem

_NODE_WIDTH = 160
_NODE_HEIGHT = 50
_BG_COLOR = QColor("#1E1E1E")
_GRID_COLOR = QColor("#2A2A2A")
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

        self.setPos(node.position.get("x", 0), node.position.get("y", 0))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)

        self._setup_appearance()
        self._create_ports()

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
    """公式编辑器的场景，管理所有节点项。"""

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self.setBackgroundBrush(_BRUSH_BG)
        self.setSceneRect(-2000, -2000, 4000, 4000)
        self._wires: list[WireItem] = []
        self._wire_start_port: PortItem | None = None
        self._ghost_wire: WireItem | None = None

    def drawBackground(self, painter: QPainter, rect: Any) -> None:
        super().drawBackground(painter, rect)
        painter.setPen(_PEN_GRID)
        grid_size = 40
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


def _node_item_from_id(scene: GraphScene, node_id: str) -> NodeItem | None:
    for item in scene.items():
        if isinstance(item, NodeItem) and item.node_id == node_id:
            return item
    return None


class GraphEditorWidget(QWidget):
    """公式编辑器主组件。

    包含 GraphScene + QGraphicsView，支持：
    - 添加/删除节点
    - 中键平移
    - 滚轮缩放
    - 网格背景
    - 连线创建（从输出端口拖到输入端口）
    """

    node_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._scene = GraphScene(self)
        self._view = QGraphicsView(self._scene)
        self._view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self._view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self._view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self._view.setAcceptDrops(True)
        self._view.installEventFilter(self)
        self._view.wheelEvent = self._zoom_event

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._view)

    def _zoom_event(self, event: Any) -> None:
        factor = 1.15
        if event.angleDelta().y() > 0:
            self._view.scale(factor, factor)
        else:
            self._view.scale(1 / factor, 1 / factor)

    def scene(self) -> GraphScene:
        return self._scene

    def add_graph_node(self, node: GraphNode) -> NodeItem:
        item = NodeItem(node)
        self._scene.addItem(item)
        self.node_changed.emit()
        return item

    def node_ports(self, node_id: str) -> list[PortItem]:
        item = _node_item_from_id(self._scene, node_id)
        if item is None:
            return []
        return item.ports

    def find_node_item(self, node_id: str) -> NodeItem | None:
        return _node_item_from_id(self._scene, node_id)

    def remove_node(self, node_id: str) -> None:
        item = _node_item_from_id(self._scene, node_id)
        if item is None:
            return
        # Remove connected wires from scene and list
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

    # ── 拖放支持（从左侧节点面板拖入） ──

    def eventFilter(self, obj, event) -> bool:
        if obj is self._view and event.type() in (
            QEvent.Type.DragEnter, QEvent.Type.DragMove, QEvent.Type.Drop,
        ):
            et = event.type()
            if et == QEvent.Type.DragEnter:
                self.dragEnterEvent(event)
            elif et == QEvent.Type.DragMove:
                self.dragMoveEvent(event)
            elif et == QEvent.Type.Drop:
                self.dropEvent(event)
            return True
        return super().eventFilter(obj, event)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event) -> None:
        event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        type_id = event.mimeData().text()
        if not type_id:
            return
        scene_pos = self._view.mapToScene(event.position().toPoint())
        from calc_framework.graph_editor.registry import create_default_node
        node = create_default_node(type_id)
        node.position = {"x": scene_pos.x() - _NODE_WIDTH / 2, "y": scene_pos.y() - _NODE_HEIGHT / 2}
        self.add_graph_node(node)
        event.acceptProposedAction()


def _find_parent_node_id(port: PortItem) -> str | None:
    p = port.parentItem()
    if isinstance(p, NodeItem):
        return p.node_id
    return None
