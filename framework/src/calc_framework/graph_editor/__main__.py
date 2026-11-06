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
    from PySide6.QtGui import QKeySequence, QShortcut
    from PySide6.QtWidgets import (
        QApplication,
        QFileDialog,
        QMainWindow,
        QMessageBox,
        QSplitter,
        QVBoxLayout,
        QWidget,
    )

    from .app.actions import export_dag_interactive, show_evaluation_report
    from .app.help_dialog import HelpDialog
    from .app.menu import MenuActions, build_menu
    from .app.preview import preview_text_for_node
    from .app.toolbar import ToolbarActions, build_toolbar
    from .file_actions import collect_document
    from .graph_editor_widget import (
        GraphEditorWidget,
        NodeItem,
    )
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
        prop.set_preview_value(preview_text_for_node(canvas, node_items[0]))

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

    def _export_dag() -> None:
        """编译当前画布并导出为 .dag.json 文件。"""
        canvas = _get_current_canvas()
        if not canvas:
            return
        export_dag_interactive(window, canvas, tab_manager)

    def _show_help() -> None:
        dialog = HelpDialog(window)
        dialog.exec()

    def _run_evaluate() -> None:
        canvas = _get_current_canvas()
        if not canvas:
            return
        show_evaluation_report(window, canvas)

    def _fit_all() -> None:
        canvas = _get_current_canvas()
        if canvas:
            canvas.fit_all()

    def _reset_zoom() -> None:
        canvas = _get_current_canvas()
        if canvas:
            canvas.reset_zoom()

    def _clear_canvas() -> None:
        """清除当前画布的所有节点。"""
        canvas = _get_current_canvas()
        prop = _get_current_prop_panel()
        if canvas:
            canvas.clear_scene()
        if prop:
            prop.show_node(None)

    build_menu(
        window,
        MenuActions(
            new_file=_new_file,
            open_file=_open_file,
            save_file=_save_file,
            save_as_file=_save_as_file,
            export_dag=_export_dag,
            show_help=_show_help,
        ),
    )
    build_toolbar(
        window,
        ToolbarActions(
            new_file=_new_file,
            open_file=_open_file,
            save_file=_save_file,
            import_package=node_panel._on_import_package,
            delete_selected=_delete_selected,
            fit_all=_fit_all,
            reset_zoom=_reset_zoom,
            run_evaluate=_run_evaluate,
            export_dag=_export_dag,
            clear_canvas=_clear_canvas,
        ),
    )

    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
