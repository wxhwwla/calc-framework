# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""开发者工具箱 — 配置类页面适配器。

包含新建适配器、数据编辑、布局编辑、导出打包四个页面。
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from calc_framework.ui.i18n import tr

from .pages_common import _REPO_ROOT, _ensure_repo_on_path, logger


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
