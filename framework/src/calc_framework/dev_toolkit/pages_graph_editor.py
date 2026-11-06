# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""开发者工具箱 — 图编辑器页面适配器。

复用独立版 ``calc_framework.graph_editor`` 的核心组件，嵌入工具箱
的 QStackedWidget。
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from calc_framework.ui.i18n import tr

from .pages_common import logger
from .pages_graph_preview import preview_text_for_node


class _GraphEditorPage(QWidget):
    """图编辑器页面 — 复用独立版 graph_editor 的全部核心组件。

    与 ``python -m calc_framework.graph_editor`` 功能一致，
    包含标签页管理、复合节点、包管理器、导出 DAG 等全部特性。
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        try:
            import json

            from PySide6.QtCore import Qt as _Qt
            from PySide6.QtGui import QKeySequence, QShortcut
            from PySide6.QtWidgets import (
                QFileDialog,
                QMessageBox,
                QSplitter,
                QToolButton,
            )

            from calc_framework.dag.engine import evaluate_graph
            from calc_framework.graph_editor.app.help_dialog import HelpDialog
            from calc_framework.graph_editor.compiler import compile_graph
            from calc_framework.graph_editor.file_actions import collect_document
            from calc_framework.graph_editor.graph_editor_widget import (
                GraphEditorWidget,
                NodeItem,
            )
            from calc_framework.graph_editor.node_panel import NodePanel
            from calc_framework.graph_editor.package_manager import PackageManager
            from calc_framework.graph_editor.prop_panel import PropPanel
            from calc_framework.graph_editor.registry import (
                create_default_node,
                register_composite_type,
                set_package_manager,
            )
            from calc_framework.graph_editor.tab_manager import TabManager

            # ── 初始化包管理器（与独立版一致）──
            pm = PackageManager(auto_discover=True)
            set_package_manager(pm)
            for tdefs in pm.loaded_packages().values():
                for tdef in tdefs:
                    register_composite_type(tdef)

            # ── 主内容区（左侧面板 + 标签页 + 右侧属性）──
            mid_splitter = QSplitter(_Qt.Horizontal)

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

            layout.addWidget(mid_splitter)

            # 创建初始标签页
            tab_manager.new_tab()

            # ── 辅助函数（与独立版一致）──
            def _get_current_canvas() -> GraphEditorWidget | None:
                try:
                    return tab_manager.current_canvas
                except RuntimeError:
                    return None

            def _get_current_prop_panel() -> PropPanel | None:
                return prop_panel

            # ── 子图标签页追踪 ──
            _subgraph_tab_by_node: dict[str, int] = {}
            _subgraph_tabs: dict[int, tuple[GraphEditorWidget, str]] = {}

            def _on_subgraph_tab_closed(index: int) -> None:
                if index in _subgraph_tabs:
                    _, node_id = _subgraph_tabs.pop(index)
                    _subgraph_tab_by_node.pop(node_id, None)

            tab_manager.tabCloseRequested.connect(_on_subgraph_tab_closed)

            def _open_subgraph_in_tab(node_id: str, source_graph: str) -> None:
                canvas = _get_current_canvas()
                if not canvas:
                    return
                if node_id in _subgraph_tab_by_node:
                    existing_idx = _subgraph_tab_by_node[node_id]
                    if existing_idx < tab_manager.count():
                        tab_manager.setCurrentIndex(existing_idx)
                        return
                    del _subgraph_tab_by_node[node_id]

                item = canvas.find_node_item(node_id)
                sub_name = item._node_label if item else "子图"

                from calc_framework.graph_editor.file_actions import load_document
                from calc_framework.graph_editor.serializer import document_from_json

                try:
                    doc = document_from_json(json.loads(source_graph))
                except Exception:
                    QMessageBox.warning(self, "子图编辑", "子图 JSON 解析失败")
                    return

                state = tab_manager.new_tab()
                load_document(doc, state.canvas)
                tab_idx = tab_manager.currentIndex()
                tab_manager.setTabText(tab_idx, f"🔧 {sub_name}")

                _subgraph_tab_by_node[node_id] = tab_idx
                _subgraph_tabs[tab_idx] = (canvas, node_id)
                _connect_canvas_signals(state.canvas)

            def _save_subgraph_tab() -> bool:
                idx = tab_manager.currentIndex()
                if idx not in _subgraph_tabs:
                    return False
                parent_canvas, node_id = _subgraph_tabs[idx]
                canvas = _get_current_canvas()
                if not canvas:
                    return False

                from calc_framework.graph_editor.serializer import document_to_json

                doc = collect_document(canvas)
                new_json = document_to_json(doc)

                item = parent_canvas.find_node_item(node_id)
                if item is not None:
                    item._config.source_graph = new_json
                    for port in item._ports[:]:
                        if port.scene():
                            port.scene().removeItem(port)
                    item._ports.clear()
                    item._create_ports()
                    parent_canvas.node_changed.emit()
                return True

            _connected_canvases: set[int] = set()

            def _connect_canvas_signals(canvas: GraphEditorWidget) -> None:
                canvas_id = id(canvas)
                if canvas_id in _connected_canvases:
                    return
                _connected_canvases.add(canvas_id)
                canvas.scene().selectionChanged.connect(lambda: _on_selection_changed())
                canvas.node_changed.connect(lambda: _update_preview())
                canvas.subgraph_edit_requested.connect(_open_subgraph_in_tab)

            # ── 信号（与独立版一致）──
            def _on_node_created(type_id: str) -> None:
                canvas = _get_current_canvas()
                if canvas:
                    canvas.add_graph_node(create_default_node(type_id))

            node_panel.node_created.connect(_on_node_created)

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
                    if prop._current_node and prop._current_node.id == node_id:
                        item.update_label(prop._current_node.label)
                        item.update_op(prop._current_node.op)
                        item.update_config(prop._current_node.config)
                    item.update()
                tab_manager.mark_modified(tab_manager.currentIndex())
                _update_preview()

            # 连接初始标签页的信号
            initial_canvas = tab_manager.current_canvas
            if initial_canvas:
                _connect_canvas_signals(initial_canvas)
                prop_panel.node_changed.connect(_on_node_config_changed)

            def _on_tab_changed() -> None:
                canvas = _get_current_canvas()
                prop = _get_current_prop_panel()
                if canvas and prop:
                    _connect_canvas_signals(canvas)
                    prop.node_changed.connect(_on_node_config_changed)

            tab_manager.current_tab_changed.connect(_on_tab_changed)

            # ── 删除 ──
            def _delete_selected() -> None:
                canvas = _get_current_canvas()
                if canvas:
                    for item in canvas.scene().selectedItems():
                        if isinstance(item, NodeItem):
                            canvas.remove_node(item.node_id)

            delete_shortcut = QShortcut(QKeySequence(_Qt.Key.Key_Delete), self)
            delete_shortcut.activated.connect(_delete_selected)

            # ── 工具栏（与独立版一致）──
            toolbar = QWidget()
            toolbar.setStyleSheet("""
                QToolButton {
                    color: #cccccc; background: transparent;
                    border: 1px solid transparent; border-radius: 4px;
                    padding: 6px 12px; font-family: "Microsoft YaHei"; font-size: 13px;
                }
                QToolButton:hover { background: #2a2d2e; border-color: #094771; color: white; }
                QToolButton:pressed { background: #094771; color: white; }
            """)
            from PySide6.QtWidgets import QHBoxLayout as _HBox

            tb_layout = _HBox(toolbar)
            tb_layout.setContentsMargins(2, 2, 2, 2)
            tb_layout.setSpacing(4)

            def _tb(text: str, tip: str, cb) -> None:
                btn = QToolButton()
                btn.setText(text)
                btn.setToolTip(tip)
                btn.clicked.connect(cb)
                tb_layout.addWidget(btn)

            def _tb_sep() -> None:
                sep = QWidget()
                sep.setFixedWidth(1)
                sep.setStyleSheet("background: #3c3c3c;")
                tb_layout.addWidget(sep)

            # ── 文件操作 ──
            def _new_file() -> None:
                tab_manager.new_tab()
                canvas = _get_current_canvas()
                prop = _get_current_prop_panel()
                if canvas and prop:
                    _connect_canvas_signals(canvas)
                    prop.node_changed.connect(_on_node_config_changed)

            def _open_file() -> None:
                path_str, _ = QFileDialog.getOpenFileName(
                    self, tr("desktop.graphEditor.openGraph"), "", tr("desktop.graphEditor.graphFileFilter")
                )
                if not path_str:
                    return
                path = Path(path_str)
                for i in range(tab_manager.count()):
                    state = tab_manager._states.get(i)
                    if state and state.file_path == path:
                        tab_manager.setCurrentIndex(i)
                        return
                tab_manager.new_tab(file_path=path)
                canvas = _get_current_canvas()
                prop = _get_current_prop_panel()
                if canvas and prop:
                    _connect_canvas_signals(canvas)
                    prop.node_changed.connect(_on_node_config_changed)

            def _save_file() -> None:
                idx = tab_manager.currentIndex()
                if _save_subgraph_tab():
                    QMessageBox.information(self, "保存", "子图已更新到父图中的复合节点")
                    return
                tab_manager.save_tab(idx)

            def _save_as_file() -> None:
                idx = tab_manager.currentIndex()
                tab_manager.save_tab_as(idx)

            def _export_dag() -> None:
                canvas = _get_current_canvas()
                if not canvas:
                    return
                try:
                    doc = collect_document(canvas)
                    dag = compile_graph(doc)
                except Exception as e:
                    QMessageBox.critical(self, tr("desktop.graphEditor.exportDagFailed"), str(e))
                    return
                tab_text = tab_manager.tabText(tab_manager.currentIndex()).replace("*", "").strip()
                untitled = tr("desktop.graphEditor.untitled")
                default_name = tab_text if tab_text and tab_text != untitled else "untitled"
                default_path = f"{default_name}.dag.json"
                path_str, _ = QFileDialog.getSaveFileName(
                    self,
                    tr("desktop.graphEditor.exportDag"),
                    default_path,
                    tr("desktop.graphEditor.exportDagFileFilter"),
                )
                if not path_str:
                    return
                try:
                    from calc_framework.dag.serializer import save_dag

                    save_dag(dag, Path(path_str))
                    QMessageBox.information(
                        self,
                        tr("desktop.graphEditor.exportDagSuccess"),
                        tr("desktop.graphEditor.exportDagSuccessDetail", path=path_str),
                    )
                except Exception as e:
                    QMessageBox.critical(self, tr("desktop.graphEditor.exportDagFailed"), str(e))

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
                    QMessageBox.information(self, tr("desktop.graphEditor.evalResult"), msg)
                except Exception as e:
                    QMessageBox.critical(self, tr("desktop.graphEditor.evalFailed"), str(e))

            def _show_help() -> None:
                dialog = HelpDialog(self)
                dialog.exec()

            # ── 工具栏按钮 ──
            _tb(tr("desktop.graphEditor.newBtn"), tr("desktop.graphEditor.newTip"), _new_file)
            _tb(tr("desktop.graphEditor.openBtn"), tr("desktop.graphEditor.openTip"), _open_file)
            _tb(tr("desktop.graphEditor.saveBtn"), tr("desktop.graphEditor.saveTip"), _save_file)
            _tb_sep()
            _tb(
                tr("desktop.graphEditor.importPackageBtn"),
                tr("desktop.graphEditor.importPackageTip"),
                lambda: node_panel._on_import_package(),
            )
            _tb_sep()
            _tb(tr("common.delete"), tr("desktop.graphEditor.deleteTip"), _delete_selected)
            _tb_sep()

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
            _tb_sep()
            _tb(tr("desktop.graphEditor.evaluateBtn"), tr("desktop.graphEditor.evaluateTip"), _run_evaluate)
            _tb(tr("desktop.graphEditor.exportDagBtn"), tr("desktop.graphEditor.exportDagTip"), _export_dag)
            _tb_sep()

            def _clear_canvas() -> None:
                canvas = _get_current_canvas()
                prop = _get_current_prop_panel()
                if canvas:
                    canvas.clear_scene()
                if prop:
                    prop.show_node(None)

            _tb(tr("desktop.graphEditor.clearBtn"), tr("desktop.graphEditor.clearTip"), _clear_canvas)
            _tb_sep()
            _tb(tr("desktop.graphEditor.usageGuide"), tr("desktop.graphEditor.usageGuide"), _show_help)
            tb_layout.addStretch()

            # ── 组装布局 ──
            inner = QWidget()
            inner_layout = QVBoxLayout(inner)
            inner_layout.setContentsMargins(0, 0, 0, 0)
            inner_layout.setSpacing(0)
            inner_layout.addWidget(toolbar)
            inner_layout.addWidget(mid_splitter, stretch=1)
            layout.addWidget(inner)

        except Exception as exc:
            logger.exception("加载图编辑器失败")
            layout.addWidget(QLabel(tr("desktop.devToolkit.loadPageFailed", error=exc)))
