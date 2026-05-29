#!/usr/bin/env python3
"""graph_editor 包入口 — 启动可视化公式图编辑器。"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def main() -> None:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QAction, QKeySequence, QShortcut
    from PySide6.QtWidgets import (
        QApplication,
        QFileDialog,
        QHBoxLayout,
        QMainWindow,
        QMenuBar,
        QMessageBox,
        QSplitter,
        QVBoxLayout,
        QWidget,
    )

    from calc_framework.graph_editor.file_actions import (
        collect_document,
        load_document,
        save_graph_file,
        open_graph_file,
    )
    from calc_framework.graph_editor.graph_editor_widget import (
        GraphEditorWidget,
        NodeItem,
    )
    from calc_framework.graph_editor.layout_panel import LayoutPanel
    from calc_framework.graph_editor.node_panel import NodePanel
    from calc_framework.graph_editor.prop_panel import PropPanel
    from calc_framework.graph_editor.registry import create_default_node
    from calc_framework.graph_editor.schema import GraphDocument

    app = QApplication(sys.argv)

    window = QMainWindow()
    window.setWindowTitle("公式计算图编辑器")
    window.resize(1500, 950)

    # ── 中央控件 ──
    container = QWidget()
    window.setCentralWidget(container)
    root_layout = QVBoxLayout(container)
    root_layout.setContentsMargins(0, 0, 0, 0)
    root_layout.setSpacing(0)

    # ── 主内容区（左侧面板 + 画布 + 右侧排版）──
    mid_splitter = QSplitter(Qt.Horizontal)

    node_panel = NodePanel()
    canvas = GraphEditorWidget()

    # 右侧排版面板
    right_panel = QSplitter(Qt.Vertical)
    layout_panel = LayoutPanel()
    prop_panel = PropPanel()
    prop_panel.setMaximumHeight(300)

    right_panel.addWidget(layout_panel)
    right_panel.addWidget(prop_panel)
    right_panel.setStretchFactor(0, 1)
    right_panel.setStretchFactor(1, 0)

    mid_splitter.addWidget(node_panel)
    mid_splitter.addWidget(canvas)
    mid_splitter.addWidget(right_panel)
    mid_splitter.setStretchFactor(0, 0)
    mid_splitter.setStretchFactor(1, 1)
    mid_splitter.setStretchFactor(2, 0)
    mid_splitter.setSizes([180, 800, 280])

    root_layout.addWidget(mid_splitter)

    # ── 文件状态 ──
    current_file: Path | None = None

    # ── 信号连接 ──
    node_panel.node_created.connect(
        lambda type_id: canvas.add_graph_node(create_default_node(type_id))
    )

    canvas.scene().selectionChanged.connect(lambda: _on_selection_changed())

    def _on_selection_changed() -> None:
        selected = canvas.scene().selectedItems()
        nodes = [it for it in selected if isinstance(it, NodeItem)]
        if nodes:
            prop_panel.show_node(nodes[0].to_graph_node())
        else:
            prop_panel.show_node(None)

    prop_panel.node_changed.connect(_on_node_config_changed)

    def _on_node_config_changed(node_id: str) -> None:
        item = canvas.find_node_item(node_id)
        if item:
            item.update()
        selected = canvas.scene().selectedItems()
        if any(isinstance(it, NodeItem) and it.node_id == node_id for it in selected):
            ni = canvas.find_node_item(node_id)
            if ni:
                prop_panel.show_node(ni.to_graph_node())

    # Delete 快捷键
    delete_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Delete), canvas)
    delete_shortcut.activated.connect(_delete_selected)

    def _delete_selected() -> None:
        for item in canvas.scene().selectedItems():
            if isinstance(item, NodeItem):
                canvas.remove_node(item.node_id)

    # ── 菜单栏 ──
    menubar = window.menuBar()

    file_menu = menubar.addMenu("文件")

    def _new_file() -> None:
        canvas.clear_scene()
        layout_panel.clear_all()
        prop_panel.show_node(None)
        nonlocal current_file
        current_file = None
        window.setWindowTitle("公式计算图编辑器 — 未命名")

    def _open_file() -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            window, "打开计算图", "", "计算图文件 (*.json);;所有文件 (*)"
        )
        if not path_str:
            return
        path = Path(path_str)
        try:
            doc = open_graph_file(path)
            load_document(doc, canvas, layout_panel)
            nonlocal current_file
            current_file = path
            window.setWindowTitle(f"公式计算图编辑器 — {path.name}")
        except Exception as e:
            QMessageBox.critical(window, "打开失败", f"无法打开文件:\n{e}")

    def _save_file() -> None:
        nonlocal current_file
        if current_file is None:
            _save_as_file()
            return
        doc = collect_document(canvas, layout_panel)
        try:
            save_graph_file(doc, current_file)
            window.setWindowTitle(f"公式计算图编辑器 — {current_file.name}")
        except Exception as e:
            QMessageBox.critical(window, "保存失败", f"无法保存文件:\n{e}")

    def _save_as_file() -> None:
        path_str, _ = QFileDialog.getSaveFileName(
            window, "另存计算图", "", "计算图文件 (*.json);;所有文件 (*)"
        )
        if not path_str:
            return
        path = Path(path_str)
        if path.suffix not in (".json",):
            path = path.with_suffix(".json")
        doc = collect_document(canvas, layout_panel)
        try:
            save_graph_file(doc, path)
            nonlocal current_file
            current_file = path
            window.setWindowTitle(f"公式计算图编辑器 — {path.name}")
        except Exception as e:
            QMessageBox.critical(window, "保存失败", f"无法保存文件:\n{e}")

    new_action = QAction("新建", window)
    new_action.setShortcut(QKeySequence.StandardKey.New)
    new_action.triggered.connect(lambda: _new_file())
    file_menu.addAction(new_action)

    open_action = QAction("打开...", window)
    open_action.setShortcut(QKeySequence.StandardKey.Open)
    open_action.triggered.connect(lambda: _open_file())
    file_menu.addAction(open_action)

    save_action = QAction("保存", window)
    save_action.setShortcut(QKeySequence.StandardKey.Save)
    save_action.triggered.connect(lambda: _save_file())
    file_menu.addAction(save_action)

    save_as_action = QAction("另存为...", window)
    save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
    save_as_action.triggered.connect(lambda: _save_as_file())
    file_menu.addAction(save_as_action)

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
