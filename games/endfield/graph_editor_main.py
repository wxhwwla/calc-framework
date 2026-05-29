#!/usr/bin/env python3
"""
公式计算图编辑器 — 根入口文件

启动可视化公式图编辑器（含实时预览）。

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
    from calc_framework.graph_editor.node_panel import NodePanel
    from calc_framework.graph_editor.prop_panel import PropPanel
    from calc_framework.graph_editor.registry import create_default_node

    from calc_framework.dag.engine import evaluate_graph
    from calc_framework.graph_editor.compiler import compile_graph
    from calc_framework.graph_editor.help_dialog import HelpDialog

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
    prop_panel = PropPanel()

    mid_splitter.addWidget(node_panel)
    mid_splitter.addWidget(canvas)
    mid_splitter.addWidget(prop_panel)
    mid_splitter.setStretchFactor(0, 0)
    mid_splitter.setStretchFactor(1, 1)
    mid_splitter.setStretchFactor(2, 0)
    mid_splitter.setSizes([180, 900, 280])
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
        selected = canvas.scene().selectedItems()
        node_items = [it for it in selected if isinstance(it, NodeItem)]
        if not node_items:
            prop_panel.set_preview_value("—")
            return
        node_id = node_items[0].node_id
        try:
            doc = collect_document(canvas)
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

    prop_panel.node_changed.connect(_on_node_config_changed)
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
            load_document(doc, canvas)
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
        doc = collect_document(canvas)
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
        doc = collect_document(canvas)
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

    help_menu = window.menuBar().addMenu("帮助")

    def _show_help() -> None:
        dialog = HelpDialog(window)
        dialog.exec()

    help_action = QAction("使用说明", window)
    help_action.setShortcut(QKeySequence(Qt.Key.Key_F1))
    help_action.triggered.connect(lambda: _show_help())
    help_menu.addAction(help_action)

    # ── 工具栏 ──
    toolbar = window.addToolBar("常用操作")
    toolbar.setMovable(False)
    toolbar.setStyleSheet("""
        QToolBar {
            background: #252526; border-bottom: 1px solid #3c3c3c;
            padding: 2px; spacing: 4px;
        }
        QToolButton {
            color: #cccccc; background: transparent;
            border: 1px solid transparent; border-radius: 4px;
            padding: 6px 12px; font-family: "Microsoft YaHei"; font-size: 13px;
        }
        QToolButton:hover { background: #2a2d2e; border-color: #094771; color: white; }
        QToolButton:pressed { background: #094771; color: white; }
    """)

    from PySide6.QtWidgets import QToolButton, QMessageBox

    def _tb(text: str, tip: str, cb: callable) -> None:
        btn = QToolButton()
        btn.setText(text)
        btn.setToolTip(tip)
        btn.clicked.connect(cb)
        toolbar.addWidget(btn)

    def _delete_selected() -> None:
        for item in canvas.scene().selectedItems():
            if isinstance(item, NodeItem):
                canvas.remove_node(item.node_id)

    def _run_evaluate() -> None:
        try:
            doc = collect_document(canvas)
            dag = compile_graph(doc)
            res = evaluate_graph(dag, {})
            output_lines = [f"{k}: {v}" for k, v in res.outputs.items()]
            node_lines = [f"{k}: {v}" for k, v in res.node_values.items()]
            msg = "【输出结果】\n" + "\n".join(output_lines) if output_lines else "(无输出)"
            msg += "\n\n【节点值】\n" + "\n".join(node_lines) if node_lines else ""
            QMessageBox.information(window, "运算结果", msg)
        except Exception as e:
            QMessageBox.critical(window, "运算失败", str(e))

    _tb("[新建]", "新建空白计算图 (Ctrl+N)", _new_file)
    _tb("[打开]", "打开计算图文件 (Ctrl+O)", _open_file)
    _tb("[保存]", "保存当前计算图 (Ctrl+S)", _save_file)
    toolbar.addSeparator()
    _tb("[导入包]", "导入计算包 (ZIP/JSON)", lambda: node_panel._on_import_package())
    toolbar.addSeparator()
    _tb("[删除]", "删除选中节点 (Delete)", _delete_selected)
    toolbar.addSeparator()
    _tb("[适配]", "缩放画布以适配所有节点", canvas.fit_all)
    _tb("[重置]", "重置缩放为 100%", canvas.reset_zoom)
    toolbar.addSeparator()
    _tb("[运算]", "编译并求值整个计算图", _run_evaluate)
    toolbar.addSeparator()
    _tb("[清除]", "清除画布上所有节点和连线", _new_file)

    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if args:
        p = Path(args[0])
        if p.exists():
            try:
                doc = open_graph_file(p)
                load_document(doc, canvas)
                current_file = p
                window.setWindowTitle(f"公式计算图编辑器 — {p.name}")
            except Exception as e:
                print(f"加载失败: {e}")

    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
