# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""开发者工具箱 — 各工具页面适配器。

每个页面包装一个已有工具的 QWidget 或 QMainWindow，使之可嵌入
DevToolkitWindow 的 QStackedWidget。
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from calc_framework.dag.debugger_gui import StepDebuggerWidget
from calc_framework.logging import get_logger
from calc_framework.ui.i18n import tr

from .main_window import _register_page

logger = get_logger(__name__)


def _find_repo_root() -> Path:
    """从 pages.py 向上查找包含 framework/ 和 tools/ 的仓库根目录。"""
    cur = Path(__file__).resolve().parent
    for _ in range(6):
        if (cur / "framework").is_dir() and (cur / "tools").is_dir():
            return cur
        cur = cur.parent
    # 回退：parents[4]（framework/src/calc_framework/dev_toolkit/pages.py → 根）
    return Path(__file__).resolve().parents[4]


_REPO_ROOT = _find_repo_root()
_REPO_ROOT_STR = str(_REPO_ROOT)

# 确保仓库根目录在 sys.path 最前面（Qt 初始化可能修改 sys.path）
if _REPO_ROOT_STR in sys.path:
    sys.path.remove(_REPO_ROOT_STR)
sys.path.insert(0, _REPO_ROOT_STR)


def _ensure_repo_on_path() -> None:
    """确保仓库根目录在 sys.path 最前面（防止 scripts/tools/ 遮蔽 tools/）。"""
    # 移除所有旧的仓库根目录条目
    while _REPO_ROOT_STR in sys.path:
        sys.path.remove(_REPO_ROOT_STR)
    # 插入到最前面
    sys.path.insert(0, _REPO_ROOT_STR)


# ═══════════════════════════════════════════════════════════════
# 配置 — 新建适配器（从 DAG 文件创建完整适配器）
# ═══════════════════════════════════════════════════════════════


class _NewAdapterPage(QWidget):
    """新建适配器页面 — 从 .dag.json 文件创建完整适配器包。

    生成 meta.json + attr_schema.json + ui/layout.json + functions.py，
    保存到 framework/adapters/<name>/，之后「数据编辑器」「布局编辑器」「导出打包」
    都能识别并使用。
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        from PySide6.QtWidgets import (
            QFormLayout,
            QGroupBox,
            QHBoxLayout,
            QLineEdit,
            QPushButton,
            QTextEdit,
        )

        # ── DAG 文件选择 ──
        dag_group = QGroupBox(tr("desktop.devToolkit.newAdapter.dagFile"))
        dag_layout = QHBoxLayout(dag_group)
        self._dag_path_edit = QLineEdit()
        self._dag_path_edit.setPlaceholderText(tr("desktop.devToolkit.newAdapter.dagFileSelect"))
        self._dag_path_edit.setReadOnly(True)
        dag_layout.addWidget(self._dag_path_edit)
        dag_btn = QPushButton("...")
        dag_btn.setFixedWidth(40)
        dag_btn.clicked.connect(self._select_dag_file)
        dag_layout.addWidget(dag_btn)
        layout.addWidget(dag_group)

        # ── 适配器信息 ──
        info_group = QGroupBox(tr("desktop.devToolkit.newAdapter.title"))
        form = QFormLayout(info_group)
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText(tr("desktop.devToolkit.newAdapter.adapterNamePlaceholder"))
        form.addRow(tr("desktop.devToolkit.newAdapter.adapterName"), self._name_edit)
        self._game_edit = QLineEdit()
        self._game_edit.setPlaceholderText(tr("desktop.devToolkit.newAdapter.gameNamePlaceholder"))
        self._game_edit.setText("通用游戏")
        form.addRow(tr("desktop.devToolkit.newAdapter.gameName"), self._game_edit)
        self._desc_edit = QLineEdit()
        self._desc_edit.setPlaceholderText(tr("desktop.devToolkit.newAdapter.descriptionPlaceholder"))
        form.addRow(tr("desktop.devToolkit.newAdapter.description"), self._desc_edit)
        layout.addWidget(info_group)

        # ── 创建按钮 ──
        self._create_btn = QPushButton(tr("desktop.devToolkit.newAdapter.createBtn"))
        self._create_btn.clicked.connect(self._create_adapter)
        layout.addWidget(self._create_btn)

        # ── 结果 ──
        self._result = QTextEdit()
        self._result.setReadOnly(True)
        self._result.setMaximumHeight(150)
        layout.addWidget(self._result)

        layout.addStretch()

        self._dag_file: Path | None = None

    def _select_dag_file(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            tr("desktop.devToolkit.newAdapter.dagFileSelect"),
            "",
            tr("desktop.devToolkit.newAdapter.dagFileFilter"),
        )
        if path_str:
            self._dag_file = Path(path_str)
            self._dag_path_edit.setText(path_str)
            # 自动填充名称
            if not self._name_edit.text():
                self._name_edit.setText(self._dag_file.stem)

    def _create_adapter(self) -> None:
        """创建适配器包 — GUI 壳层，委托 adapter_creator 纯逻辑。"""
        from .adapter_creator import AdapterScaffoldConfig, scaffold_adapter_directory

        if not self._dag_file:
            QMessageBox.warning(self, tr("desktop.devToolkit.newAdapter.error"), tr("desktop.devToolkit.newAdapter.noDagFile"))
            return

        name = self._name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, tr("desktop.devToolkit.newAdapter.error"), tr("desktop.devToolkit.newAdapter.noName"))
            return

        game = self._game_edit.text().strip() or "通用游戏"
        desc = self._desc_edit.text().strip()

        config = AdapterScaffoldConfig(
            name=name,
            game=game,
            description=desc,
            dag_file=self._dag_file,
            output_root=_REPO_ROOT / "framework" / "adapters",
        )
        result = scaffold_adapter_directory(config)
        if not result.success:
            QMessageBox.critical(self, tr("desktop.devToolkit.newAdapter.error"), result.error)
            return

        # 显示结果
        file_lines = [f"  {f}" for f in result.files]
        self._result.setPlainText(
            tr("desktop.devToolkit.newAdapter.successMsg", path=str(result.adapter_dir)) + "\n\n文件:\n" + "\n".join(file_lines)
        )
        QMessageBox.information(
            self,
            tr("desktop.devToolkit.newAdapter.success"),
            tr("desktop.devToolkit.newAdapter.successMsg", path=str(result.adapter_dir)),
        )


_register_page("new_adapter", _NewAdapterPage)


# ═══════════════════════════════════════════════════════════════
# 配置 — 数据编辑
# ═══════════════════════════════════════════════════════════════


class _DataEditorPage(QWidget):
    """数据编辑页面 — 包装 DataEditorPanel。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        try:
            _ensure_repo_on_path()
            from tools.designer.data_editor.panel import DataEditorPanel

            self._panel = DataEditorPanel()
            layout.addWidget(self._panel)
        except Exception as exc:
            logger.exception("加载数据编辑器失败")
            layout.addWidget(QLabel(tr("desktop.devToolkit.loadPageFailed", error=exc)))


_register_page("data_editor", _DataEditorPage)


# ═══════════════════════════════════════════════════════════════
# 配置 — 布局编辑
# ═══════════════════════════════════════════════════════════════


class _LayoutEditorPage(QWidget):
    """布局编辑页面 — 包装 LayoutCanvasPanel。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        try:
            _ensure_repo_on_path()
            from tools.designer.layout_editor.canvas import LayoutCanvasPanel

            self._panel = LayoutCanvasPanel()
            layout.addWidget(self._panel)

            # 填充适配器下拉菜单
            from calc_framework.config.manager import AdapterManager

            mgr = AdapterManager()
            self._panel.populate_adapters(mgr.names)
        except Exception as exc:
            logger.exception("加载布局编辑器失败")
            layout.addWidget(QLabel(tr("desktop.devToolkit.loadPageFailed", error=exc)))


_register_page("layout_editor", _LayoutEditorPage)


# ═══════════════════════════════════════════════════════════════
# 配置 — 导出打包
# ═══════════════════════════════════════════════════════════════


class _ExportPage(QWidget):
    """导出打包页面 — 包装 ThemePanel。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        try:
            _ensure_repo_on_path()
            from tools.designer.theme_editor.panel import ThemePanel

            self._panel = ThemePanel()
            layout.addWidget(self._panel)
        except Exception as exc:
            logger.exception("加载导出页失败")
            layout.addWidget(QLabel(tr("desktop.devToolkit.loadPageFailed", error=exc)))


_register_page("export_pack", _ExportPage)


# ═══════════════════════════════════════════════════════════════
# 开发 — 图编辑器（复用独立版核心组件）
# ═══════════════════════════════════════════════════════════════


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
            from calc_framework.graph_editor.compiler import compile_graph
            from calc_framework.graph_editor.file_actions import collect_document
            from calc_framework.graph_editor.graph_editor_widget import (
                GraphEditorWidget,
                NodeItem,
            )
            from calc_framework.graph_editor.help_dialog import HelpDialog
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
                node_id = node_items[0].node_id
                graph_node = node_items[0].to_graph_node()

                if graph_node.type == "var":
                    path = graph_node.config.path
                    prop.set_preview_value(f"引用: {path}" if path else "(未设置路径)")
                    return
                if graph_node.type == "user_input":
                    prop.set_preview_value(f"默认值: {graph_node.config.default}")
                    return
                if graph_node.type == "const":
                    prop.set_preview_value(f"{graph_node.config.value}")
                    return

                # 对于 output / composite / binary 等节点，尝试编译求值
                try:
                    doc = collect_document(canvas)
                    dag = compile_graph(doc)
                    if not dag.nodes:
                        prop.set_preview_value("—")
                        return
                    res = evaluate_graph(dag, {})

                    if graph_node.type == "output":
                        port_inputs = {}
                        for e in doc.edges:
                            port_inputs[(e.to_node, e.to_port)] = e.from_node
                        source = port_inputs.get((node_id, 0))
                        if source:
                            val = res.node_values.get(source)
                            if val is not None:
                                prop.set_preview_value(f"{val:.6f}" if isinstance(val, float) else str(val))
                                return
                            val = res.outputs.get(source)
                            if val is not None:
                                prop.set_preview_value(f"{val:.6f}" if isinstance(val, float) else str(val))
                                return
                        prop.set_preview_value("(未连接)" if source is None else "—")
                        return

                    if graph_node.type == "composite":
                        for sub in dag.subgraphs.values():
                            for out_def in sub.outputs.values():
                                expanded_key = f"{node_id}.{out_def.node}"
                                val = res.node_values.get(expanded_key)
                                if val is not None:
                                    prop.set_preview_value(f"{val:.6f}" if isinstance(val, float) else str(val))
                                    return
                        prop.set_preview_value(f"[{graph_node.label or '复合节点'}]")
                        return

                    val = res.node_values.get(node_id)
                    if val is not None:
                        prop.set_preview_value(f"{val:.6f}" if isinstance(val, float) else str(val))
                    else:
                        val = res.outputs.get(node_id)
                        prop.set_preview_value(f"{val:.6f}" if val is not None else "—")
                except Exception as e:
                    prop.set_preview_value(f"错误: {str(e)[:60]}")

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


_register_page("graph_editor", _GraphEditorPage)


# ═══════════════════════════════════════════════════════════════
# 开发 — DAG 调试器
# ═══════════════════════════════════════════════════════════════


class _DebuggerPage(QWidget):
    """DAG 调试器页面 — 包装 StepDebuggerWidget。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        try:
            from calc_framework.dag.serializer import dag_from_dict

            # 创建一个示例 DAG 供调试
            dag_data = {
                "schema_version": "dag-v1",
                "name": tr("desktop.debugger.sampleGraphName"),
                "description": tr("desktop.debugger.sampleGraphDesc"),
                "variables": {
                    "a": {
                        "type": "float",
                        "source": "user_input",
                        "description": tr("desktop.debugger.sampleInputA"),
                        "default": 10.0,
                    },
                    "b": {
                        "type": "float",
                        "source": "user_input",
                        "description": tr("desktop.debugger.sampleInputB"),
                        "default": 20.0,
                    },
                },
                "nodes": {
                    "ref_a": {"type": "var", "path": "a"},
                    "ref_b": {"type": "var", "path": "b"},
                    "add": {"type": "binary", "op": "+", "lhs": "ref_a", "rhs": "ref_b"},
                    "mul": {"type": "binary", "op": "*", "lhs": "ref_a", "rhs": "ref_b"},
                },
                "outputs": {
                    "sum": {"node": "add", "label": "A+B", "format": ".2f", "is_primary": True},
                    "product": {"node": "mul", "label": "A*B", "format": ".2f", "is_primary": False},
                },
            }
            dag = dag_from_dict(dag_data)

            self._debugger = StepDebuggerWidget(
                dag,
                {"a": 10.0, "b": 20.0},
                self,
            )
            layout.addWidget(self._debugger)  # type: ignore[arg-type]
        except Exception as exc:
            logger.exception("加载 DAG 调试器失败")
            layout.addWidget(QLabel(tr("desktop.devToolkit.loadPageFailed", error=exc)))


_register_page("dag_debugger", _DebuggerPage)


# ═══════════════════════════════════════════════════════════════
# 开发 — 计算包查看
# ═══════════════════════════════════════════════════════════════


class _ViewerPage(QWidget):
    """计算包查看页面 — 包装 CalcPackViewer。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        try:
            from calc_framework.ui.viewer import CalcPackViewer

            self._viewer = CalcPackViewer()
            layout.addWidget(self._viewer.centralWidget())

            # 给一个加载按钮
            btn_layout = QHBoxLayout()
            open_btn = QPushButton(tr("desktop.launcher.openCalcpack"))
            open_btn.clicked.connect(self._on_open)
            btn_layout.addWidget(open_btn)
            btn_layout.addStretch()
            layout.addLayout(btn_layout)
        except Exception as exc:
            logger.exception("加载查看器失败")
            layout.addWidget(QLabel(tr("desktop.devToolkit.loadPageFailed", error=exc)))

    def _on_open(self) -> None:
        from PySide6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getOpenFileName(
            self, tr("desktop.launcher.openCalcpack"), "", "CalcPack (*.calcpack);;所有文件 (*.*)"
        )
        if path:
            from calc_framework.ui.viewer import open_calcpack

            open_calcpack(Path(path))


_register_page("calcpack_viewer", _ViewerPage)


# ═══════════════════════════════════════════════════════════════
# 开发 — AI 生成器
# ═══════════════════════════════════════════════════════════════


class _GeneratorPage(QWidget):
    """AI 生成器页面 — 包装 GeneratorWindow。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        try:
            from PySide6.QtWidgets import (
                QGroupBox,
                QHBoxLayout,
                QLineEdit,
                QListWidget,
                QPushButton,
                QSplitter,
                QTextEdit,
            )

            _ensure_repo_on_path()
            from tools.generator import GeneratorEngine

            self._engine = GeneratorEngine()
            self._result_files: dict[str, str] = {}

            container = QWidget()
            root_layout = QHBoxLayout(container)
            root_layout.setContentsMargins(0, 0, 0, 0)

            splitter = QSplitter(Qt.Horizontal)

            # 左侧：模板列表
            left_widget = QWidget()
            left_layout = QVBoxLayout(left_widget)
            left_layout.setContentsMargins(4, 4, 4, 4)
            left_layout.addWidget(QLabel(tr("desktop.devToolkit.generator.categoryTemplates")))
            self._template_list = QListWidget()
            self._template_list.itemClicked.connect(self._on_template_selected)
            left_layout.addWidget(self._template_list)
            splitter.addWidget(left_widget)

            # 中间：游戏信息
            mid_widget = QWidget()
            mid_layout = QVBoxLayout(mid_widget)
            mid_layout.setContentsMargins(4, 4, 4, 4)
            info_group = QGroupBox(tr("desktop.devToolkit.generator.gameInfo"))
            info_layout = QVBoxLayout(info_group)
            self._game_name_input = QLineEdit()
            self._game_name_input.setPlaceholderText(tr("desktop.devToolkit.generator.gameNamePlaceholder"))
            info_layout.addWidget(self._game_name_input)
            mid_layout.addWidget(info_group)

            self._template_info = QTextEdit()
            self._template_info.setReadOnly(True)
            self._template_info.setPlaceholderText(tr("desktop.devToolkit.generator.selectTemplateHint"))
            mid_layout.addWidget(self._template_info)

            self._generate_btn = QPushButton(tr("desktop.devToolkit.generator.generateBtn"))
            self._generate_btn.clicked.connect(self._on_generate)
            self._generate_btn.setEnabled(False)
            mid_layout.addWidget(self._generate_btn)
            splitter.addWidget(mid_widget)

            # 右侧：结果
            right_widget = QWidget()
            right_layout = QVBoxLayout(right_widget)
            right_layout.setContentsMargins(4, 4, 4, 4)
            right_layout.addWidget(QLabel(tr("desktop.devToolkit.generator.resultLabel")))
            self._result_view = QTextEdit()
            self._result_view.setReadOnly(True)
            right_layout.addWidget(self._result_view)
            self._export_btn = QPushButton(tr("desktop.devToolkit.generator.exportBtn"))
            self._export_btn.clicked.connect(self._on_export)
            self._export_btn.setEnabled(False)
            right_layout.addWidget(self._export_btn)
            splitter.addWidget(right_widget)

            splitter.setSizes([200, 350, 350])
            root_layout.addWidget(splitter)
            layout.addWidget(container)

            self._load_templates()

        except Exception as exc:
            logger.exception("加载 AI 生成器失败")
            layout.addWidget(QLabel(tr("desktop.devToolkit.loadPageFailed", error=exc)))

    def _load_templates(self) -> None:
        try:
            templates = self._engine.list_templates()
            for tpl in templates:
                from PySide6.QtWidgets import QListWidgetItem

                self._template_list.addItem(QListWidgetItem(str(tpl)))
        except Exception as exc:
            self._template_info.setPlainText(tr("desktop.devToolkit.generator.loadTemplatesFailed", error=exc))

    def _on_template_selected(self, item) -> None:
        self._generate_btn.setEnabled(True)
        tpl_name = item.text()
        try:
            from tools.generator.templates import load_template

            tpl = load_template(tpl_name)
            self._template_info.setPlainText(
                tr(
                    "desktop.devToolkit.generator.templateInfo",
                    name=tpl_name,
                    node_count=len(getattr(tpl, "nodes", []) or []),
                    edge_count=len(getattr(tpl, "edges", []) or []),
                )
            )
        except Exception as exc:
            self._template_info.setPlainText(str(exc))

    def _on_generate(self) -> None:
        game = self._game_name_input.text().strip()
        if not game:
            QMessageBox.warning(self, tr("common.info"), tr("desktop.devToolkit.generator.gameNameRequired"))
            return
        item = self._template_list.currentItem()
        if not item:
            return
        try:
            result = self._engine.generate(item.text(), game)
            lines = []
            self._result_files.clear()
            for path, content in result.items():
                self._result_files[path] = content
                line_count = len(content.splitlines())
                lines.append(f"\U0001f4c4 {path}  ({line_count} lines)")
            self._result_view.setPlainText("\n".join(lines) if lines else tr("desktop.devToolkit.generator.emptyResult"))
            self._export_btn.setEnabled(bool(self._result_files))
        except Exception as exc:
            QMessageBox.critical(self, tr("desktop.devToolkit.generator.generateFailed"), str(exc))

    def _on_export(self) -> None:
        from PySide6.QtWidgets import QFileDialog

        path = QFileDialog.getExistingDirectory(self, tr("desktop.devToolkit.generator.selectExportDir"))
        if not path:
            return
        out = Path(path)
        for rel, content in self._result_files.items():
            fp = out / rel
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_text(content, encoding="utf-8")
        QMessageBox.information(
            self,
            tr("desktop.devToolkit.generator.exportDone"),
            tr("desktop.devToolkit.generator.exportDoneMsg", n=len(self._result_files), out=out),
        )


_register_page("ai_generator", _GeneratorPage)


# ═══════════════════════════════════════════════════════════════
# 开发 — OCR 标注
# ═══════════════════════════════════════════════════════════════


class _OcrPage(QWidget):
    """OCR 标注页面 — 包装 LabelTool。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        try:
            _ensure_repo_on_path()
            from tools.ocr.label import LabelTool

            self._tool = LabelTool()
            layout.addWidget(self._tool)
        except Exception as exc:
            logger.exception("加载 OCR 标注失败")
            layout.addWidget(QLabel(tr("desktop.devToolkit.loadPageFailed", error=exc)))


_register_page("ocr_label", _OcrPage)
