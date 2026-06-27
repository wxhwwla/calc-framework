#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""graph_editor 包入口 — 启动可视化公式图编辑器。"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from calc_framework.ui.i18n import tr


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

    from ..dag.engine import evaluate_graph
    from .compiler import compile_graph
    from .file_actions import (
        collect_document,
        load_document,
        open_graph_file,
        save_graph_file,
    )
    from .graph_editor_widget import (
        GraphEditorWidget,
        NodeItem,
    )
    from .help_dialog import HelpDialog
    from .node_panel import NodePanel
    from .package_manager import PackageManager
    from .prop_panel import PropPanel
    from .registry import create_default_node, register_composite_type

    # 初始化 PackageManager 并自动发现子图包
    pm = PackageManager(auto_discover=True)
    for tdefs in pm.loaded_packages().values():
        for tdef in tdefs:
            register_composite_type(tdef)

    app = QApplication(sys.argv)

    window = QMainWindow()
    window.setWindowTitle(tr("desktop.graphEditor.windowTitle"))
    window.resize(1500, 950)

    # ── 中央控件 ──
    container = QWidget()
    window.setCentralWidget(container)
    root_layout = QVBoxLayout(container)
    root_layout.setContentsMargins(0, 0, 0, 0)
    root_layout.setSpacing(0)

    # ── 主内容区（左侧面板 + 画布 + 右侧属性）──
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

    # ── 文件状态 ──
    current_file: Path | None = None

    # ── 信号连接 ──
    node_panel.node_created.connect(lambda type_id: canvas.add_graph_node(create_default_node(type_id)))

    canvas.scene().selectionChanged.connect(lambda: _on_selection_changed())

    def _on_selection_changed() -> None:
        selected = canvas.scene().selectedItems()
        nodes = [it for it in selected if isinstance(it, NodeItem)]
        if nodes:
            prop_panel.show_node(nodes[0].to_graph_node())
        else:
            prop_panel.show_node(None)
        _update_preview()

    def _update_preview() -> None:
        selected = canvas.scene().selectedItems()
        node_items = [it for it in selected if isinstance(it, NodeItem)]
        if not node_items:
            prop_panel.set_preview_value("—")
            return
        node_id = node_items[0].node_id
        graph_node = node_items[0].to_graph_node()

        # 对于变量引用节点，显示引用路径
        if graph_node.type == "var":
            path = graph_node.config.path
            if path:
                prop_panel.set_preview_value(f"引用: {path}")
            else:
                prop_panel.set_preview_value("(未设置路径)")
            return

        # 对于用户输入节点，显示默认值
        if graph_node.type == "user_input":
            default = graph_node.config.default
            prop_panel.set_preview_value(f"默认值: {default}")
            return

        # 对于常量节点，显示值
        if graph_node.type == "const":
            value = graph_node.config.value
            prop_panel.set_preview_value(f"{value}")
            return

        # 对于计算节点，尝试求值
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
            # 同步 label、op、config 修改到画布节点
            if prop_panel._current_node and prop_panel._current_node.id == node_id:
                item.update_label(prop_panel._current_node.label)
                item.update_op(prop_panel._current_node.op)
                item.update_config(prop_panel._current_node.config)
            item.update()
        # 注意：不要在这里调用 show_node()，否则会导致输入框重建并丢失焦点
        _update_preview()

    prop_panel.node_changed.connect(_on_node_config_changed)

    canvas.node_changed.connect(lambda: _update_preview())

    def _delete_selected() -> None:
        for item in canvas.scene().selectedItems():
            if isinstance(item, NodeItem):
                canvas.remove_node(item.node_id)

    delete_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Delete), canvas)
    delete_shortcut.activated.connect(_delete_selected)

    # ── 菜单栏 ──
    menubar = window.menuBar()

    file_menu = menubar.addMenu(tr("common.file"))

    def _new_file() -> None:
        canvas.clear_scene()
        prop_panel.show_node(None)
        nonlocal current_file
        current_file = None
        window.setWindowTitle(tr("desktop.graphEditor.windowTitleUntitled"))

    def _open_file() -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            window, tr("desktop.graphEditor.openGraph"), "", tr("desktop.graphEditor.graphFileFilter")
        )
        if not path_str:
            return
        path = Path(path_str)
        try:
            doc = open_graph_file(path)
            load_document(doc, canvas)
            nonlocal current_file
            current_file = path
            window.setWindowTitle(tr("desktop.graphEditor.windowTitleFile", name=path.name))
        except Exception as e:
            QMessageBox.critical(
                window, tr("desktop.graphEditor.openFailed"), tr("desktop.graphEditor.openFailedDetail", error=e)
            )

    def _save_file() -> None:
        nonlocal current_file
        if current_file is None:
            _save_as_file()
            return
        doc = collect_document(canvas)
        try:
            save_graph_file(doc, current_file)
            window.setWindowTitle(tr("desktop.graphEditor.windowTitleFile", name=current_file.name))
        except Exception as e:
            QMessageBox.critical(
                window, tr("desktop.graphEditor.saveFailed"), tr("desktop.graphEditor.saveFailedDetail", error=e)
            )

    def _save_as_file() -> None:
        path_str, _ = QFileDialog.getSaveFileName(
            window, tr("desktop.graphEditor.saveAsGraph"), "", tr("desktop.graphEditor.graphFileFilter")
        )
        if not path_str:
            return
        path = Path(path_str)
        if path.suffix not in (".json",):
            path = path.with_suffix(".json")
        doc = collect_document(canvas)
        try:
            save_graph_file(doc, path)
            nonlocal current_file
            current_file = path
            window.setWindowTitle(tr("desktop.graphEditor.windowTitleFile", name=path.name))
        except Exception as e:
            QMessageBox.critical(
                window, tr("desktop.graphEditor.saveFailed"), tr("desktop.graphEditor.saveFailedDetail", error=e)
            )

    new_action = QAction(tr("desktop.graphEditor.new"), window)
    new_action.setShortcut(QKeySequence.StandardKey.New)
    new_action.triggered.connect(lambda: _new_file())
    file_menu.addAction(new_action)

    open_action = QAction(tr("desktop.graphEditor.open"), window)
    open_action.setShortcut(QKeySequence.StandardKey.Open)
    open_action.triggered.connect(lambda: _open_file())
    file_menu.addAction(open_action)

    save_action = QAction(tr("desktop.graphEditor.save"), window)
    save_action.setShortcut(QKeySequence.StandardKey.Save)
    save_action.triggered.connect(lambda: _save_file())
    file_menu.addAction(save_action)

    save_as_action = QAction(tr("desktop.graphEditor.saveAs"), window)
    save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
    save_as_action.triggered.connect(lambda: _save_as_file())
    file_menu.addAction(save_as_action)

    # ── 帮助菜单 ──
    help_menu = menubar.addMenu(tr("common.help"))

    def _show_help() -> None:
        dialog = HelpDialog(window)
        dialog.exec()

    help_action = QAction(tr("desktop.graphEditor.usageGuide"), window)
    help_action.setShortcut(QKeySequence(Qt.Key.Key_F1))
    help_action.triggered.connect(lambda: _show_help())
    help_menu.addAction(help_action)

    # 捐赠菜单（可选，依赖项目特定的 utils 模块）
    try:
        from utils.gui.donation import append_donation_help_menu_action

        append_donation_help_menu_action(help_menu, window)
    except ImportError:
        pass  # 捐赠功能不可用，跳过

    # ── 工具栏 ──
    toolbar = window.addToolBar(tr("desktop.graphEditor.commonOperations"))
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

    from collections.abc import Callable

    from PySide6.QtWidgets import QToolButton

    def _tb(text: str, tip: str, cb: Callable[[], None]) -> None:
        btn = QToolButton()
        btn.setText(text)
        btn.setToolTip(tip)
        btn.clicked.connect(cb)
        toolbar.addWidget(btn)

    def _run_evaluate() -> None:
        try:
            doc = collect_document(canvas)
            dag = compile_graph(doc)
            res = evaluate_graph(dag, {})
            output_lines = [f"{k}: {v}" for k, v in res.outputs.items()]
            node_lines = [f"{k}: {v}" for k, v in res.node_values.items()]
            msg = (
                tr("desktop.graphEditor.evalOutputResult") + "\n" + "\n".join(output_lines)
                if output_lines
                else tr("desktop.graphEditor.evalNoOutput")
            )
            msg += "\n\n" + tr("desktop.graphEditor.evalNodeValues") + "\n" + "\n".join(node_lines) if node_lines else ""
            QMessageBox.information(window, tr("desktop.graphEditor.evalResult"), msg)
        except Exception as e:
            QMessageBox.critical(window, tr("desktop.graphEditor.evalFailed"), str(e))

    _tb(tr("desktop.graphEditor.newBtn"), tr("desktop.graphEditor.newTip"), _new_file)
    _tb(tr("desktop.graphEditor.openBtn"), tr("desktop.graphEditor.openTip"), _open_file)
    _tb(tr("desktop.graphEditor.saveBtn"), tr("desktop.graphEditor.saveTip"), _save_file)
    toolbar.addSeparator()
    _tb(
        tr("desktop.graphEditor.importPackageBtn"),
        tr("desktop.graphEditor.importPackageTip"),
        lambda: node_panel._on_import_package(),
    )
    toolbar.addSeparator()
    _tb(tr("common.delete"), tr("desktop.graphEditor.deleteTip"), _delete_selected)
    toolbar.addSeparator()
    _tb(tr("desktop.graphEditor.fitViewBtn"), tr("desktop.graphEditor.fitViewTip"), canvas.fit_all)
    _tb(tr("desktop.graphEditor.resetViewBtn"), tr("desktop.graphEditor.resetViewTip"), canvas.reset_zoom)
    toolbar.addSeparator()
    _tb(tr("desktop.graphEditor.evaluateBtn"), tr("desktop.graphEditor.evaluateTip"), _run_evaluate)
    toolbar.addSeparator()
    _tb(tr("desktop.graphEditor.clearBtn"), tr("desktop.graphEditor.clearTip"), _new_file)

    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
