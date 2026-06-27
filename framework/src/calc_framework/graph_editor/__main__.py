#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""graph_editor 包入口 — 启动可视化公式图编辑器。"""

import json
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
    from .file_actions import collect_document
    from .graph_editor_widget import (
        GraphEditorWidget,
        NodeItem,
    )
    from .help_dialog import HelpDialog
    from .node_panel import NodePanel
    from .package_manager import PackageManager
    from .prop_panel import PropPanel
    from .registry import create_default_node, register_composite_type, set_package_manager
    from .tab_manager import TabManager

    # 初始化 PackageManager 并自动发现子图包
    pm = PackageManager(auto_discover=True)
    set_package_manager(pm)
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

    # ── 主内容区（左侧面板 + 标签页 + 右侧属性）──
    mid_splitter = QSplitter(Qt.Horizontal)

    node_panel = NodePanel()
    tab_manager = TabManager()
    prop_panel = PropPanel()

    mid_splitter.addWidget(node_panel)
    mid_splitter.addWidget(tab_manager)
    mid_splitter.addWidget(prop_panel)
    mid_splitter.setStretchFactor(0, 0)
    mid_splitter.setStretchFactor(1, 1)
    mid_splitter.setStretchFactor(2, 0)
    mid_splitter.setSizes([180, 900, 280])

    root_layout.addWidget(mid_splitter)

    # 创建初始标签页
    tab_manager.new_tab()

    # ── 辅助函数 ──
    def _get_current_canvas() -> GraphEditorWidget | None:
        """获取当前标签页的画布。"""
        try:
            return tab_manager.current_canvas
        except RuntimeError:
            return None

    def _get_current_prop_panel() -> PropPanel | None:
        """获取当前标签页的属性面板。"""
        return prop_panel

    # ── 信号连接 ──
    def _on_node_created(type_id: str) -> None:
        canvas = _get_current_canvas()
        if canvas:
            canvas.add_graph_node(create_default_node(type_id))

    node_panel.node_created.connect(_on_node_created)

    # 子图标签页追踪：node_id → tab_index（用于跳转到已打开的标签页）
    _subgraph_tab_by_node: dict[str, int] = {}
    # 反向追踪：tab_index → (parent_canvas, composite_node_id)
    _subgraph_tabs: dict[int, tuple[GraphEditorWidget, str]] = {}

    def _on_subgraph_tab_closed(index: int) -> None:
        """关闭标签页时清理子图追踪记录。"""
        if index in _subgraph_tabs:
            _, node_id = _subgraph_tabs.pop(index)
            _subgraph_tab_by_node.pop(node_id, None)

    tab_manager.tabCloseRequested.connect(_on_subgraph_tab_closed)

    def _open_subgraph_in_tab(node_id: str, source_graph: str) -> None:
        """在新标签页中打开子图进行编辑。已打开则跳转。"""
        canvas = _get_current_canvas()
        if not canvas:
            return

        # 如果这个子图已经在某个标签页中打开，直接跳转
        if node_id in _subgraph_tab_by_node:
            existing_idx = _subgraph_tab_by_node[node_id]
            if existing_idx < tab_manager.count():
                tab_manager.setCurrentIndex(existing_idx)
                return
            # 标签页已关闭，清理记录
            del _subgraph_tab_by_node[node_id]

        # 获取复合节点的显示名（用画布上的 label，不是子图内部 name）
        item = canvas.find_node_item(node_id)
        sub_name = item._node_label if item else "子图"

        # 加载子图
        from .file_actions import load_document
        from .serializer import document_from_json

        try:
            doc = document_from_json(json.loads(source_graph))
        except Exception:
            QMessageBox.warning(window, "子图编辑", "子图 JSON 解析失败")
            return

        state = tab_manager.new_tab()
        load_document(doc, state.canvas)
        tab_idx = tab_manager.currentIndex()
        tab_manager.setTabText(tab_idx, f"🔧 {sub_name}")

        # 记录关联
        _subgraph_tab_by_node[node_id] = tab_idx
        _subgraph_tabs[tab_idx] = (canvas, node_id)

        # 连接新画布的信号
        _connect_canvas_signals(state.canvas)

    def _save_subgraph_tab() -> bool:
        """保存子图标签页，更新父图中复合节点的 source_graph。"""
        idx = tab_manager.currentIndex()
        if idx not in _subgraph_tabs:
            return False

        parent_canvas, node_id = _subgraph_tabs[idx]
        canvas = _get_current_canvas()
        if not canvas:
            return False

        from .file_actions import collect_document
        from .serializer import document_to_json

        doc = collect_document(canvas)
        new_json = document_to_json(doc)

        # 更新父图中复合节点的 source_graph
        item = parent_canvas.find_node_item(node_id)
        if item is not None:
            item._config.source_graph = new_json
            # 重建端口
            for port in item._ports[:]:
                if port.scene():
                    port.scene().removeItem(port)
            item._ports.clear()
            item._create_ports()
            parent_canvas.node_changed.emit()

        return True

    _connected_canvases: set[int] = set()

    def _connect_canvas_signals(canvas: GraphEditorWidget) -> None:
        """连接画布信号（每个 canvas 只连接一次）。"""
        canvas_id = id(canvas)
        if canvas_id in _connected_canvases:
            return
        _connected_canvases.add(canvas_id)
        canvas.scene().selectionChanged.connect(lambda: _on_selection_changed())
        canvas.node_changed.connect(lambda: _update_preview())
        canvas.subgraph_edit_requested.connect(_open_subgraph_in_tab)

    def _on_selection_changed() -> None:
        canvas = _get_current_canvas()
        prop = _get_current_prop_panel()
        if not canvas or not prop:
            return

        selected = canvas.scene().selectedItems()
        nodes = [it for it in selected if isinstance(it, NodeItem)]
        if nodes:
            prop.show_node(nodes[0].to_graph_node())
        else:
            prop.show_node(None)
        _update_preview()

    def _update_preview() -> None:
        canvas = _get_current_canvas()
        prop = _get_current_prop_panel()
        if not canvas or not prop:
            return

        selected = canvas.scene().selectedItems()
        node_items = [it for it in selected if isinstance(it, NodeItem)]
        if not node_items:
            prop.set_preview_value("—")
            return
        node_id = node_items[0].node_id
        graph_node = node_items[0].to_graph_node()

        # 对于变量引用节点，显示引用路径
        if graph_node.type == "var":
            path = graph_node.config.path
            if path:
                prop.set_preview_value(f"引用: {path}")
            else:
                prop.set_preview_value("(未设置路径)")
            return

        # 对于用户输入节点，显示默认值
        if graph_node.type == "user_input":
            default = graph_node.config.default
            prop.set_preview_value(f"默认值: {default}")
            return

        # 对于常量节点，显示值
        if graph_node.type == "const":
            value = graph_node.config.value
            prop.set_preview_value(f"{value}")
            return

        # 对于输出节点，追踪输入源的值
        if graph_node.type == "output":
            try:
                doc = collect_document(canvas)
                dag = compile_graph(doc)
                if not dag.nodes:
                    prop.set_preview_value("—")
                    return
                res = evaluate_graph(dag, {})
                # 输出节点的值 = 其输入源节点的值
                port_inputs = {}
                for e in doc.edges:
                    port_inputs[(e.to_node, e.to_port)] = e.from_node
                source = port_inputs.get((node_id, 0))
                if source:
                    val = res.node_values.get(source)
                    if val is not None:
                        prop.set_preview_value(f"{val:.6f}" if isinstance(val, float) else str(val))
                    else:
                        # 源可能是复合节点，值在 outputs 中
                        val = res.outputs.get(source)
                        if val is not None:
                            prop.set_preview_value(f"{val:.6f}" if isinstance(val, float) else str(val))
                        else:
                            prop.set_preview_value("—")
                else:
                    prop.set_preview_value("(未连接)")
            except Exception as e:
                prop.set_preview_value(f"错误: {str(e)[:60]}")
            return

        # 对于复合节点，尝试求值显示结果
        if graph_node.type == "composite":
            try:
                doc = collect_document(canvas)
                dag = compile_graph(doc)
                if not dag.nodes:
                    prop.set_preview_value(f"[{graph_node.label or '复合节点'}]")
                    return
                res = evaluate_graph(dag, {})
                # 复合节点展开后，其子图输出节点的值在 node_values 中
                # 键格式为 {node_id}.{子图内节点id}
                # 通过子图 outputs 定位哪个展开节点是输出
                for sub in dag.subgraphs.values():
                    for out_def in sub.outputs.values():
                        expanded_key = f"{node_id}.{out_def.node}"
                        val = res.node_values.get(expanded_key)
                        if val is not None:
                            prop.set_preview_value(f"{val:.6f}" if isinstance(val, float) else str(val))
                            return
                prop.set_preview_value(f"[{graph_node.label or '复合节点'}]")
            except Exception:
                prop.set_preview_value(f"[{graph_node.label or '复合节点'}]")
            return

        # 对于计算节点（binary/unary/condition），尝试求值
        try:
            doc = collect_document(canvas)
            dag = compile_graph(doc)
            if not dag.nodes:
                prop.set_preview_value("—")
                return
            res = evaluate_graph(dag, {})
            val = res.node_values.get(node_id)
            if val is not None:
                formatted = f"{val:.6f}" if isinstance(val, float) else str(val)
                prop.set_preview_value(formatted)
            else:
                val = res.outputs.get(node_id)
                if val is not None:
                    prop.set_preview_value(f"{val:.6f}")
                else:
                    prop.set_preview_value("—")
        except Exception as e:
            err_msg = str(e)
            if len(err_msg) > 60:
                err_msg = err_msg[:57] + "..."
            prop.set_preview_value(f"错误: {err_msg}")

    def _on_node_config_changed(node_id: str) -> None:
        canvas = _get_current_canvas()
        prop = _get_current_prop_panel()
        if not canvas or not prop:
            return

        item = canvas.find_node_item(node_id)
        if item:
            # 同步 label、op、config 修改到画布节点
            if prop._current_node and prop._current_node.id == node_id:
                item.update_label(prop._current_node.label)
                item.update_op(prop._current_node.op)
                item.update_config(prop._current_node.config)
            item.update()
        # 标记标签页为已修改
        tab_manager.mark_modified(tab_manager.currentIndex())
        # 注意：不要在这里调用 show_node()，否则会导致输入框重建并丢失焦点
        _update_preview()

    # 连接初始标签页的信号
    initial_canvas = tab_manager.current_canvas
    if initial_canvas:
        _connect_canvas_signals(initial_canvas)
        prop_panel.node_changed.connect(_on_node_config_changed)

    # 标签页切换时重新连接信号
    def _on_tab_changed() -> None:
        canvas = _get_current_canvas()
        prop = _get_current_prop_panel()
        if canvas and prop:
            _connect_canvas_signals(canvas)
            prop.node_changed.connect(_on_node_config_changed)

    tab_manager.current_tab_changed.connect(_on_tab_changed)

    def _delete_selected() -> None:
        canvas = _get_current_canvas()
        if canvas:
            for item in canvas.scene().selectedItems():
                if isinstance(item, NodeItem):
                    canvas.remove_node(item.node_id)

    # 删除快捷键（绑定到主窗口）
    delete_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Delete), window)
    delete_shortcut.activated.connect(_delete_selected)

    # ── 菜单栏 ──
    menubar = window.menuBar()

    file_menu = menubar.addMenu(tr("common.file"))

    def _new_file() -> None:
        """新建文件（新标签页）。"""
        tab_manager.new_tab()
        # 连接新标签页的信号
        canvas = _get_current_canvas()
        prop = _get_current_prop_panel()
        if canvas and prop:
            _connect_canvas_signals(canvas)
            prop.node_changed.connect(_on_node_config_changed)

    def _open_file() -> None:
        """打开文件（新标签页）。"""
        path_str, _ = QFileDialog.getOpenFileName(
            window, tr("desktop.graphEditor.openGraph"), "", tr("desktop.graphEditor.graphFileFilter")
        )
        if not path_str:
            return
        path = Path(path_str)

        # 检查文件是否已经在某个标签页中打开
        for i in range(tab_manager.count()):
            state = tab_manager._states.get(i)
            if state and state.file_path == path:
                tab_manager.setCurrentIndex(i)
                return

        # 在新标签页中打开文件
        tab_manager.new_tab(file_path=path)
        # 连接新标签页的信号
        canvas = _get_current_canvas()
        prop = _get_current_prop_panel()
        if canvas and prop:
            _connect_canvas_signals(canvas)
            prop.node_changed.connect(_on_node_config_changed)

    def _save_file() -> None:
        """保存当前标签页。子图标签页会更新父图中的复合节点。"""
        idx = tab_manager.currentIndex()
        if _save_subgraph_tab():
            # 子图已更新到父节点，标记父标签页为已修改
            QMessageBox.information(window, "保存", "子图已更新到父图中的复合节点")
            return
        tab_manager.save_tab(idx)

    def _save_as_file() -> None:
        """另存为当前标签页。"""
        idx = tab_manager.currentIndex()
        tab_manager.save_tab_as(idx)

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
        canvas = _get_current_canvas()
        if not canvas:
            return

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

    def _fit_all() -> None:
        canvas = _get_current_canvas()
        if canvas:
            canvas.fit_all()

    def _reset_zoom() -> None:
        canvas = _get_current_canvas()
        if canvas:
            canvas.reset_zoom()

    _tb(tr("desktop.graphEditor.fitViewBtn"), tr("desktop.graphEditor.fitViewTip"), _fit_all)
    _tb(tr("desktop.graphEditor.resetViewBtn"), tr("desktop.graphEditor.resetViewTip"), _reset_zoom)
    toolbar.addSeparator()
    _tb(tr("desktop.graphEditor.evaluateBtn"), tr("desktop.graphEditor.evaluateTip"), _run_evaluate)
    toolbar.addSeparator()

    def _clear_canvas() -> None:
        """清除当前画布的所有节点。"""
        canvas = _get_current_canvas()
        prop = _get_current_prop_panel()
        if canvas:
            canvas.clear_scene()
        if prop:
            prop.show_node(None)

    _tb(tr("desktop.graphEditor.clearBtn"), tr("desktop.graphEditor.clearTip"), _clear_canvas)

    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
