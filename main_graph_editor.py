#!/usr/bin/env python3
"""
公式计算图编辑器 — 根入口

启动可视化公式图编辑器（含实时预览）。

使用方式：
    python main_graph_editor.py               # 启动编辑器
    python main_graph_editor.py path/to.json  # 打开已有文件
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


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
        open_graph_file,
        save_graph_file,
    )
    from calc_framework.graph_editor.graph_editor_widget import (
        GraphEditorWidget,
        NodeItem,
    )
    from calc_framework.graph_editor.node_panel import NodePanel
    from calc_framework.graph_editor.prop_panel import PropPanel

    from calc_framework.dag.engine import evaluate_graph
    from calc_framework.graph_editor.help_dialog import HelpDialog

    app = QApplication(sys.argv)

    window = QMainWindow()
    window.setWindowTitle("公式计算图编辑器")
    window.resize(1500, 950)

    editor = GraphEditorWidget()
    node_panel = NodePanel(editor)
    prop_panel = PropPanel(editor)

    editor.prop_panel = prop_panel

    splitter = QSplitter(Qt.Horizontal)
    splitter.addWidget(node_panel)
    splitter.addWidget(editor)
    splitter.addWidget(prop_panel)
    splitter.setSizes([220, 950, 330])

    central = QWidget()
    layout = QVBoxLayout(central)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(splitter)
    window.setCentralWidget(central)

    # ── 菜单栏 ──
    menu = window.menuBar()
    file_menu = menu.addMenu("文件(&F)")

    def open_file() -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            window, "打开图文件", "", "JSON (*.json);;所有文件 (*)"
        )
        if not path_str:
            return
        path = Path(path_str)
        doc = open_graph_file(path)
        if doc:
            editor.load_document(doc)

    open_action = QAction("打开(&O)...", window)
    open_action.setShortcut(QKeySequence("Ctrl+O"))
    open_action.triggered.connect(open_file)
    file_menu.addAction(open_action)

    def save_file() -> None:
        path_str, _ = QFileDialog.getSaveFileName(
            window, "保存图文件", "", "JSON (*.json);;所有文件 (*)"
        )
        if not path_str:
            return
        path = Path(path_str)
        doc = collect_document(editor)
        save_graph_file(doc, path)

    save_action = QAction("保存(&S)", window)
    save_action.setShortcut(QKeySequence("Ctrl+S"))
    save_action.triggered.connect(save_file)
    file_menu.addAction(save_action)

    def about() -> None:
        QMessageBox.about(window, "关于", "公式计算图编辑器\n\n基于 calc-framework DAG 引擎")

    about_action = QAction("关于(&A)", window)
    about_action.triggered.connect(about)
    file_menu.addAction(about_action)

    def show_help() -> None:
        dialog = HelpDialog(window)
        dialog.exec()

    help_action = QAction("帮助(&H)", window)
    help_action.setShortcut(QKeySequence("F1"))
    help_action.triggered.connect(show_help)
    file_menu.addAction(help_action)

    # ── 快捷键 ──
    def _eval_selected() -> None:
        """对选中的节点执行局部求值并显示结果。"""
        selected = [i for i in editor.scene().selectedItems() if isinstance(i, NodeItem)]
        if not selected:
            return
        node_item = selected[0]
        graph = editor.graph
        try:
            result = evaluate_graph(graph, {})
            if node_item.node_id in result.node_values:
                display = str(result.node_values[node_item.node_id])
            else:
                display = "（该节点无输出）"
            prop_panel.set_result(display)
        except Exception as e:
            prop_panel.set_result(f"求值错误: {e}")

    QShortcut(QKeySequence("Ctrl+Shift+E"), window).activated.connect(
        _eval_selected
    )

    # ── 命令行打开 ──
    if len(sys.argv) > 1:
        path_str = sys.argv[1]
        if path_str != "--debug":
            path = Path(path_str)
            if path.is_file():
                doc = open_graph_file(path)
                if doc:
                    editor.load_document(doc)

    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
