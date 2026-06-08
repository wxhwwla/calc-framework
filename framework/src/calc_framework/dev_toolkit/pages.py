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
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from calc_framework.dag.debugger_gui import StepDebuggerWidget
from calc_framework.logging import get_logger

from .main_window import _register_page

logger = get_logger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


# ═══════════════════════════════════════════════════════════════
# 📦 配置 — 数据编辑
# ═══════════════════════════════════════════════════════════════


class _DataEditorPage(QWidget):
    """数据编辑页面 — 包装 DataEditorPanel。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        try:
            from tools.designer.data_editor.panel import DataEditorPanel

            self._panel = DataEditorPanel()
            layout.addWidget(self._panel)
        except Exception as exc:
            logger.exception("加载数据编辑器失败")
            layout.addWidget(QLabel(f"加载失败: {exc}"))


_register_page("data_editor", _DataEditorPage)


# ═══════════════════════════════════════════════════════════════
# 📦 配置 — 布局编辑
# ═══════════════════════════════════════════════════════════════


class _LayoutEditorPage(QWidget):
    """布局编辑页面 — 包装 LayoutCanvasPanel。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        try:
            from tools.designer.layout_editor.canvas import LayoutCanvasPanel

            self._panel = LayoutCanvasPanel()
            layout.addWidget(self._panel)
        except Exception as exc:
            logger.exception("加载布局编辑器失败")
            layout.addWidget(QLabel(f"加载失败: {exc}"))


_register_page("layout_editor", _LayoutEditorPage)


# ═══════════════════════════════════════════════════════════════
# 📦 配置 — 导出打包
# ═══════════════════════════════════════════════════════════════


class _ExportPage(QWidget):
    """导出打包页面 — 包装 ThemePanel。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        try:
            from tools.designer.theme_editor.panel import ThemePanel

            self._panel = ThemePanel()
            layout.addWidget(self._panel)
        except Exception as exc:
            logger.exception("加载导出页失败")
            layout.addWidget(QLabel(f"加载失败: {exc}"))


_register_page("export_pack", _ExportPage)


# ═══════════════════════════════════════════════════════════════
# 🔧 开发 — 图编辑器
# ═══════════════════════════════════════════════════════════════


class _GraphEditorPage(QWidget):
    """图编辑器页面 — 包装 graph_editor（简化版，无循环导入）。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        try:
            from PySide6.QtCore import Qt as _Qt
            from PySide6.QtGui import QShortcut

            # ── 顶部工具栏 ──
            from PySide6.QtWidgets import (
                QFileDialog,
                QMessageBox,
                QSplitter,
                QToolBar,
                QToolButton,
            )

            from calc_framework.dag.engine import evaluate_graph
            from calc_framework.graph_editor.compiler import compile_graph
            from calc_framework.graph_editor.file_actions import (
                collect_document,
                load_document,
                open_graph_file,
                save_graph_file,
            )
            from calc_framework.graph_editor.graph_editor_widget import (
                GraphEditorWidget,
                NodeItem,
            )
            from calc_framework.graph_editor.node_panel import NodePanel
            from calc_framework.graph_editor.prop_panel import PropPanel
            from calc_framework.graph_editor.registry import create_default_node

            toolbar = QToolBar("常用操作")
            toolbar.setMovable(False)

            def _tb(text: str, cb):
                btn = QToolButton()
                btn.setText(text)
                btn.clicked.connect(cb)
                toolbar.addWidget(btn)

            # ── 主内容区 ──
            splitter = QSplitter(_Qt.Horizontal)
            self._node_panel = NodePanel()
            self._canvas = GraphEditorWidget()
            self._prop_panel = PropPanel()

            splitter.addWidget(self._node_panel)
            splitter.addWidget(self._canvas)
            splitter.addWidget(self._prop_panel)
            splitter.setStretchFactor(0, 0)
            splitter.setStretchFactor(1, 3)
            splitter.setStretchFactor(2, 1)

            # ── 文件操作 ──
            current_file: list[Path | None] = [None]

            def _new_file():
                self._canvas.clear_scene()
                self._prop_panel.show_node(None)
                current_file[0] = None

            def _open_file():
                path_str, _ = QFileDialog.getOpenFileName(self, "打开计算图", "", "计算图文件 (*.json);;所有文件 (*)")
                if not path_str:
                    return
                path = Path(path_str)
                try:
                    doc = open_graph_file(path)
                    load_document(doc, self._canvas)
                    current_file[0] = path
                except Exception as e:
                    QMessageBox.critical(self, "打开失败", str(e))

            def _save_file():
                if current_file[0] is None:
                    path_str, _ = QFileDialog.getSaveFileName(self, "保存", "", "计算图文件 (*.json)")
                    if not path_str:
                        return
                    current_file[0] = Path(path_str)
                doc = collect_document(self._canvas)
                try:
                    save_graph_file(doc, current_file[0])
                except Exception as e:
                    QMessageBox.critical(self, "保存失败", str(e))

            def _delete_selected():
                for item in self._canvas.scene().selectedItems():
                    if isinstance(item, NodeItem):
                        self._canvas.remove_node(item.node_id)

            def _run_evaluate():
                try:
                    doc = collect_document(self._canvas)
                    dag = compile_graph(doc)
                    res = evaluate_graph(dag, {})
                    lines = [f"{k}: {v}" for k, v in res.outputs.items()]
                    msg = "\n".join(lines) if lines else "(无输出)"
                    QMessageBox.information(self, "运算结果", msg)
                except Exception as e:
                    QMessageBox.critical(self, "运算失败", str(e))

            _tb("[新建]", lambda: _new_file())
            _tb("[打开]", lambda: _open_file())
            _tb("[保存]", lambda: _save_file())
            _tb("[删除]", lambda: _delete_selected())
            _tb("[运算]", lambda: _run_evaluate())
            _tb("[清除]", lambda: _new_file())

            # ── 信号 ──
            self._node_panel.node_created.connect(
                lambda type_id: self._canvas.add_graph_node(create_default_node(type_id))
            )

            def _on_selection():
                selected = self._canvas.scene().selectedItems()
                nodes = [it for it in selected if isinstance(it, NodeItem)]
                if nodes:
                    self._prop_panel.show_node(nodes[0].to_graph_node())
                else:
                    self._prop_panel.show_node(None)

            self._canvas.scene().selectionChanged.connect(_on_selection)

            delete_shortcut = QShortcut(_Qt.Key.Key_Delete, self._canvas)
            delete_shortcut.activated.connect(_delete_selected)

            # ── 组装布局 ──
            inner = QWidget()
            inner_layout = QVBoxLayout(inner)
            inner_layout.setContentsMargins(0, 0, 0, 0)
            inner_layout.setSpacing(0)
            inner_layout.addWidget(toolbar)
            inner_layout.addWidget(splitter, stretch=1)
            layout.addWidget(inner)

        except Exception as exc:
            logger.exception("加载图编辑器失败")
            layout.addWidget(QLabel(f"加载失败: {exc}"))


_register_page("graph_editor", _GraphEditorPage)


# ═══════════════════════════════════════════════════════════════
# 🔧 开发 — DAG 调试器
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
                "name": "示例调试图",
                "description": "简单的乘法和加法示例",
                "variables": {
                    "a": {"type": "float", "source": "user_input", "description": "输入值 A", "default": 10.0},
                    "b": {"type": "float", "source": "user_input", "description": "输入值 B", "default": 20.0},
                },
                "nodes": {
                    "add": {"type": "binary", "op": "+", "left": {"var": "a"}, "right": {"var": "b"}},
                    "mul": {"type": "binary", "op": "*", "left": {"var": "a"}, "right": {"var": "b"}},
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
            layout.addWidget(QLabel(f"加载失败: {exc}"))


_register_page("dag_debugger", _DebuggerPage)


# ═══════════════════════════════════════════════════════════════
# 🔧 开发 — 计算包查看
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
            open_btn = QPushButton("打开 .calcpack…")
            open_btn.clicked.connect(self._on_open)
            btn_layout.addWidget(open_btn)
            btn_layout.addStretch()
            layout.addLayout(btn_layout)
        except Exception as exc:
            logger.exception("加载查看器失败")
            layout.addWidget(QLabel(f"加载失败: {exc}"))

    def _on_open(self) -> None:
        from PySide6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getOpenFileName(self, "打开 .calcpack", "", "CalcPack (*.calcpack);;所有文件 (*.*)")
        if path:
            from calc_framework.ui.viewer import open_calcpack

            open_calcpack(Path(path))


_register_page("calcpack_viewer", _ViewerPage)


# ═══════════════════════════════════════════════════════════════
# 🔧 开发 — AI 生成器
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
            left_layout.addWidget(QLabel("品类模板"))
            self._template_list = QListWidget()
            self._template_list.itemClicked.connect(self._on_template_selected)
            left_layout.addWidget(self._template_list)
            splitter.addWidget(left_widget)

            # 中间：游戏信息
            mid_widget = QWidget()
            mid_layout = QVBoxLayout(mid_widget)
            mid_layout.setContentsMargins(4, 4, 4, 4)
            info_group = QGroupBox("游戏信息")
            info_layout = QVBoxLayout(info_group)
            self._game_name_input = QLineEdit()
            self._game_name_input.setPlaceholderText("输入游戏名称")
            info_layout.addWidget(self._game_name_input)
            mid_layout.addWidget(info_group)

            self._template_info = QTextEdit()
            self._template_info.setReadOnly(True)
            self._template_info.setPlaceholderText("选择模板后显示详情")
            mid_layout.addWidget(self._template_info)

            self._generate_btn = QPushButton("生成计算器")
            self._generate_btn.clicked.connect(self._on_generate)
            self._generate_btn.setEnabled(False)
            mid_layout.addWidget(self._generate_btn)
            splitter.addWidget(mid_widget)

            # 右侧：结果
            right_widget = QWidget()
            right_layout = QVBoxLayout(right_widget)
            right_layout.setContentsMargins(4, 4, 4, 4)
            right_layout.addWidget(QLabel("生成结果"))
            self._result_view = QTextEdit()
            self._result_view.setReadOnly(True)
            right_layout.addWidget(self._result_view)
            self._export_btn = QPushButton("导出到目录…")
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
            layout.addWidget(QLabel(f"加载失败: {exc}"))

    def _load_templates(self) -> None:
        try:
            templates = self._engine.list_templates()
            for tpl in templates:
                from PySide6.QtWidgets import QListWidgetItem

                self._template_list.addItem(QListWidgetItem(str(tpl)))
        except Exception as exc:
            self._template_info.setPlainText(f"加载模板失败: {exc}")

    def _on_template_selected(self, item) -> None:
        self._generate_btn.setEnabled(True)
        tpl_name = item.text()
        try:
            from tools.generator.templates import load_template

            tpl = load_template(tpl_name)
            self._template_info.setPlainText(
                f"模板: {tpl_name}\n\n"
                f"节点: {len(getattr(tpl, 'nodes', []) or [])}\n"
                f"边: {len(getattr(tpl, 'edges', []) or [])}"
            )
        except Exception as exc:
            self._template_info.setPlainText(str(exc))

    def _on_generate(self) -> None:
        game = self._game_name_input.text().strip()
        if not game:
            QMessageBox.warning(self, "提示", "请输入游戏名称")
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
                lines.append(f"📄 {path}  ({line_count} 行)")
            self._result_view.setPlainText("\n".join(lines) if lines else "生成结果为空")
            self._export_btn.setEnabled(bool(self._result_files))
        except Exception as exc:
            QMessageBox.critical(self, "生成失败", str(exc))

    def _on_export(self) -> None:
        from PySide6.QtWidgets import QFileDialog

        path = QFileDialog.getExistingDirectory(self, "选择导出目录")
        if not path:
            return
        out = Path(path)
        for rel, content in self._result_files.items():
            fp = out / rel
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_text(content, encoding="utf-8")
        QMessageBox.information(self, "导出完成", f"已导出 {len(self._result_files)} 个文件到:\n{out}")


_register_page("ai_generator", _GeneratorPage)


# ═══════════════════════════════════════════════════════════════
# 🔧 开发 — OCR 标注
# ═══════════════════════════════════════════════════════════════


class _OcrPage(QWidget):
    """OCR 标注页面 — 包装 LabelTool。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        try:
            from tools.ocr.label import LabelTool

            self._tool = LabelTool()
            layout.addWidget(self._tool)
        except Exception as exc:
            logger.exception("加载 OCR 标注失败")
            layout.addWidget(QLabel(f"加载失败: {exc}"))


_register_page("ocr_label", _OcrPage)
