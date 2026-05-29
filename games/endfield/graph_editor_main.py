#!/usr/bin/env python3
"""
公式计算图编辑器 — 根入口文件

启动可视化公式图编辑器。

使用方式：
    python graph_editor_main.py               # 启动编辑器
    python graph_editor_main.py path/to.json  # 打开已有文件
    python -m calc_framework.graph_editor      # 等价
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_PKG_DIR = Path(__file__).resolve().parent
if str(_PKG_DIR) not in sys.path:
    sys.path.insert(0, str(_PKG_DIR))


def main() -> None:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QAction, QKeySequence, QShortcut
    from PySide6.QtWidgets import (
        QApplication,
        QFileDialog,
        QMainWindow,
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

    from calc_framework.dag.engine import evaluate_graph
    from calc_framework.graph_editor.compiler import compile_graph

    app = QApplication(sys.argv)

    window = QMainWindow()
    window.setWindowTitle("公式计算图编辑器")
    window.resize(1500, 950)

    container = QWidget()
    window.setCentralWidget(container)
    root_layout = QVBoxLayout(container)
    root_layout.setContentsMargins(0, 0, 0, 0)
    root_layout.setSpacing(0)

    mid_splitter = QSplitter(Qt.Horizontal)
    node_panel = NodePanel()
    canvas = GraphEditorWidget()

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

    current_file: Path | None = None

    node_panel.node_created.connect(
        lambda type_id: canvas.add_graph_node(create_default_node(type_id))
    )

    canvas.scene().selectionChanged.connect(lambda: _on_selection_changed())

    def _on_selection_changed() -> None:
        selected = canvas.scene().selectedItems()
        nodes = [it for it in selected if isinstance(it, NodeItem)]
        prop_panel.show_node(nodes[0].to_graph_node() if nodes else None)
        _update_preview()

    def _update_preview() -> None:
        """编译当前图并求值，在属性面板显示选中节点的计算结果。"""
        selected = canvas.scene().selectedItems()
        node_items = [it for it in selected if isinstance(it, NodeItem)]
        if not node_items:
            prop_panel.set_preview_value("—")
            return
        node_id = node_items[0].node_id
        try:
            doc = collect_document(canvas, layout_panel)
            dag = compile_graph(doc)
            if not dag.nodes:
                prop_panel.set_preview_value("—")
                return
            res = evaluate_graph(dag, {})
            val = res.node_values.get(node_id)
            if val is not None:
                formatted = f"{val:.6f}" if isinstance(val, float) else str(val)
                prop_panel.set_preview_value(formatted)
            else:
                val = res.outputs.get(node_id)
                if val is not None:
                    prop_panel.set_preview_value(f"{val:.6f}")
                else:
                    prop_panel.set_preview_value("(无法计算)")
        except Exception as e:
            err_msg = str(e)
            if len(err_msg) > 60:
                err_msg = err_msg[:57] + "..."
            prop_panel.set_preview_value(f"错误: {err_msg}")

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
        _update_preview()

    canvas.node_changed.connect(lambda: _update_preview())

    delete_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Delete), canvas)
    delete_shortcut.activated.connect(lambda: [
        canvas.remove_node(it.node_id)
        for it in canvas.scene().selectedItems()
        if isinstance(it, NodeItem)
    ])

    file_menu = window.menuBar().addMenu("文件")

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
        p = Path(path_str)
        try:
            doc = open_graph_file(p)
            load_document(doc, canvas, layout_panel)
            nonlocal current_file
            current_file = p
            window.setWindowTitle(f"公式计算图编辑器 — {p.name}")
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
        p = Path(path_str)
        if p.suffix not in (".json",):
            p = p.with_suffix(".json")
        doc = collect_document(canvas, layout_panel)
        try:
            save_graph_file(doc, p)
            nonlocal current_file
            current_file = p
            window.setWindowTitle(f"公式计算图编辑器 — {p.name}")
        except Exception as e:
            QMessageBox.critical(window, "保存失败", f"无法保存文件:\n{e}")

    for label, shortcut_key, callback in [
        ("新建", QKeySequence.StandardKey.New, _new_file),
        ("打开...", QKeySequence.StandardKey.Open, _open_file),
        ("保存", QKeySequence.StandardKey.Save, _save_file),
        ("另存为...", QKeySequence.StandardKey.SaveAs, _save_as_file),
    ]:
        action = QAction(label, window)
        action.setShortcut(shortcut_key)
        action.triggered.connect(callback)
        file_menu.addAction(action)

    # 如果命令行提供了文件路径，打开它
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if args:
        p = Path(args[0])
        if p.exists():
            try:
                doc = open_graph_file(p)
                load_document(doc, canvas, layout_panel)
                current_file = p
                window.setWindowTitle(f"公式计算图编辑器 — {p.name}")
            except Exception as e:
                print(f"加载失败: {e}")

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
