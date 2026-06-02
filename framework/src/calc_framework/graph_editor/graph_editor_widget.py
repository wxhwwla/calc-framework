# SPDX-License-Identifier: AGPL-3.0
"""可视化公式编辑画布 — 主容器组件。"""



from __future__ import annotations

import json

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from .items import _GRID_SIZE, _NODE_HEIGHT, _NODE_WIDTH, NodeItem, _find_parent_node_id
from .scene import GraphScene, _node_item_from_id
from .schema import GraphEdge, GraphNode
from .view import GraphView
from .wire import WireItem


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

        """_on_drop_node。"""



    def _on_drop_node(self, type_id: str, scene_x: float, scene_y: float) -> None:

        from .registry import create_default_node

        node = create_default_node(type_id)

        snap_x = round((scene_x - _NODE_WIDTH / 2) / _GRID_SIZE) * _GRID_SIZE

        snap_y = round((scene_y - _NODE_HEIGHT / 2) / _GRID_SIZE) * _GRID_SIZE

        node.position = {"x": snap_x, "y": snap_y}

        self.add_graph_node(node)

        """_on_wire_created。"""



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



    def node_ports(self, node_id: str) -> list:

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



    def add_wire(self, source, target) -> WireItem:

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



        """_open_subgraph_editor。"""
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




class SubGraphDialog(QDialog):

    """子图编辑器对话框 — 双击复合节点时打开。"""



    def __init__(self, source_graph: str, parent: QWidget | None = None) -> None:

        super().__init__(parent)

        self.setWindowTitle("子图编辑器")

        self.resize(800, 600)



        from .file_actions import load_document
        from .prop_panel import PropPanel
        from .serializer import document_from_json



        layout = QVBoxLayout(self)

        layout.setContentsMargins(0, 0, 0, 0)



        # 子图的 GraphEditorWidget

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
        """_on_selection_changed。"""

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

        from .file_actions import collect_document
        from .serializer import document_to_json

        doc = collect_document(self._editor)

        return document_to_json(doc)
