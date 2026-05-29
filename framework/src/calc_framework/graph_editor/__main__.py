#!/usr/bin/env python3
"""graph_editor 包入口 — 启动可视化公式图编辑器。"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def main() -> None:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QShortcut, QKeySequence
    from PySide6.QtWidgets import (
        QApplication,
        QHBoxLayout,
        QSplitter,
        QVBoxLayout,
        QWidget,
    )

    from calc_framework.graph_editor.graph_editor_widget import GraphEditorWidget, NodeItem
    from calc_framework.graph_editor.node_panel import NodePanel
    from calc_framework.graph_editor.prop_panel import PropPanel
    from calc_framework.graph_editor.registry import create_default_node

    app = QApplication(sys.argv)

    container = QWidget()
    container.setWindowTitle("公式计算图编辑器")
    container.resize(1400, 900)

    root_layout = QVBoxLayout(container)
    root_layout.setContentsMargins(0, 0, 0, 0)
    root_layout.setSpacing(0)

    # ── 主内容区（左侧面板 + 画布）──
    mid_splitter = QSplitter(Qt.Horizontal)

    node_panel = NodePanel()
    canvas = GraphEditorWidget()

    # ── 属性面板（底部）──
    prop_panel = PropPanel()
    prop_panel.setMaximumHeight(250)

    # 连接面板拖拽 → 画布创建节点
    def _on_node_created(type_id: str) -> None:
        node = create_default_node(type_id)
        canvas.add_graph_node(node)

    node_panel.node_created.connect(_on_node_created)

    # 连接画布选中 → 属性面板
    def _on_selection_changed() -> None:
        selected_items = canvas.scene().selectedItems()
        node_items = [it for it in selected_items if isinstance(it, NodeItem)]
        if node_items:
            prop_panel.show_node(node_items[0].to_graph_node())
        else:
            prop_panel.show_node(None)

    canvas.scene().selectionChanged.connect(_on_selection_changed)

    # 连接属性面板修改 → 重绘节点
    def _on_node_config_changed(node_id: str) -> None:
        item = canvas.find_node_item(node_id)
        if item:
            item.update()
        # 如果该节点仍选中，刷新属性面板显示
        selected = canvas.scene().selectedItems()
        if any(isinstance(it, NodeItem) and it.node_id == node_id for it in selected):
            node = canvas.find_node_item(node_id)
            if node:
                prop_panel.show_node(node.to_graph_node())

    prop_panel.node_changed.connect(_on_node_config_changed)

    # Delete 快捷键删除选中节点
    def _delete_selected() -> None:
        for item in canvas.scene().selectedItems():
            if isinstance(item, NodeItem):
                canvas.remove_node(item.node_id)

    delete_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Delete), canvas)
    delete_shortcut.activated.connect(_delete_selected)

    mid_splitter.addWidget(node_panel)
    mid_splitter.addWidget(canvas)
    mid_splitter.setStretchFactor(0, 0)
    mid_splitter.setStretchFactor(1, 1)
    mid_splitter.setSizes([200, 1200])

    root_layout.addWidget(mid_splitter, 1)
    root_layout.addWidget(prop_panel, 0)

    container.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
