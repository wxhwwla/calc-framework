# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""开发者工具箱 — 开发辅助类页面适配器。

包含 DAG 调试器、计算包查看、AI 生成器、OCR 标注四个页面。
"""

from __future__ import annotations

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
from calc_framework.ui.i18n import tr

from .pages_common import _ensure_repo_on_path, logger


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


class _ViewerPage(QWidget):
    """计算包查看页面 — 包装 CalcPackViewer。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        try:
            from calc_framework.ui.viewer import CalcPackViewer

            self._viewer = CalcPackViewer()
            # centralWidget() 在尚未 setCentralWidget 时可为 None（pyright reportArgumentType）
            central = self._viewer.centralWidget()
            if central is not None:
                layout.addWidget(central)

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
