# SPDX-License-Identifier: AGPL-3.0
"""CalcPackViewer — 通用用户展示层。

加载 .calcpack 文件并渲染完整的交互式计算界面。

支持实体选择（角色/武器/装备）、自定义输入、实时 DAG 求值。

用法::

    python -m calc_framework.ui.viewer path/to/game.calcpack

"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QMainWindow,
    QProgressBar,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from ..dag.schema import DAGVariable
from ..dag.service import DAGService
from .compute_sheet import ComputeSheet
from .layout import Layout
from .theme import ThemeManager
from .viewer_events import CalcPackViewerEventMixin
from .viewer_render import CalcPackViewerRenderMixin


class CalcPackViewer(CalcPackViewerRenderMixin, CalcPackViewerEventMixin, QMainWindow):

    """通用 .calcpack 查看器 — 加载计算包并渲染交互界面。"""

    def __init__(self, calcpack_path: str | None = None):

        super().__init__()

        self.setWindowTitle("计算包查看器")

        self.resize(1100, 750)

        self._loaded_data: dict[str, Any] = {}

        self._dag_service: DAGService | None = None

        self._layout: Layout | None = None

        self._variables: dict[str, DAGVariable] = {}

        self._theme_manager = ThemeManager()

        self._data_files: dict[str, list[dict[str, Any]]] = {}

        self._compute_sheet: ComputeSheet | None = None

        self._entity_selectors: dict[str, QComboBox] = {}

        self._level_spin: QSpinBox | None = None

        self._current_level: int = 90

        self._entity_data: dict[str, dict[str, Any]] = {}

        self._splitter: QSplitter | None = None

        self._entity_group: QGroupBox | None = None

        self._right_panel: QWidget | None = None

        self._asset_temp_dir: tempfile.TemporaryDirectory | None = None

        self._calcpack_path: str | None = calcpack_path

        central = QWidget()

        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)

        main_layout.setContentsMargins(0, 0, 0, 0)

        self._build_menu()

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left = QWidget()

        self._left_layout = QVBoxLayout(left)

        self._left_layout.setContentsMargins(4, 4, 4, 4)

        self._entity_group = QGroupBox("选择实体")

        self._entity_form = QFormLayout(self._entity_group)

        self._left_layout.addWidget(self._entity_group)

        self._left_layout.addStretch()

        splitter.addWidget(left)

        self._scroll = QScrollArea()

        self._scroll.setWidgetResizable(True)

        self._sheet_container = QWidget()

        self._sheet_layout = QVBoxLayout(self._sheet_container)

        self._scroll.setWidget(self._sheet_container)

        splitter.addWidget(self._scroll)

        right = QWidget()

        self._right_layout = QVBoxLayout(right)

        self._right_layout.setContentsMargins(4, 4, 4, 4)

        self._info_group = QGroupBox("包信息")

        info_form = QFormLayout(self._info_group)

        self._info_name = QLabel("—")

        info_form.addRow("名称:", self._info_name)

        self._info_game = QLabel("—")

        info_form.addRow("游戏:", self._info_game)

        self._info_version = QLabel("—")

        info_form.addRow("版本:", self._info_version)

        self._info_vars = QLabel("—")

        info_form.addRow("变量:", self._info_vars)

        self._info_outputs = QLabel("—")

        info_form.addRow("输出:", self._info_outputs)

        self._right_layout.addWidget(self._info_group)

        self._right_layout.addStretch()

        splitter.addWidget(right)

        splitter.setSizes([220, 580, 200])

        self._splitter = splitter

        main_layout.addWidget(splitter, stretch=1)

        bar = QStatusBar()

        self._status_label = QLabel("就绪 — 打开一个 .calcpack 文件开始使用")

        bar.addWidget(self._status_label)

        self._progress = QProgressBar()

        self._progress.setMaximumWidth(160)

        self._progress.setVisible(False)

        bar.addPermanentWidget(self._progress)

        self.setStatusBar(bar)

        if calcpack_path:

            path_copy = calcpack_path

            QTimer.singleShot(100, lambda p=path_copy: self.load_calcpack(p))

    def _build_menu(self) -> None:

        mb = self.menuBar()

        file_menu = mb.addMenu("文件")

        open_action = QAction("打开 .calcpack...", self)

        open_action.setShortcut("Ctrl+O")

        open_action.triggered.connect(self._open_file)

        file_menu.addAction(open_action)

        file_menu.addSeparator()

        exit_action = QAction("退出", self)

        exit_action.setShortcut("Ctrl+Q")

        exit_action.triggered.connect(self.close)

        file_menu.addAction(exit_action)

        tools_menu = mb.addMenu("工具")

        plugin_action = QAction("插件管理器...", self)

        plugin_action.triggered.connect(self._show_plugin_manager_dialog)

        tools_menu.addAction(plugin_action)

        theme_menu = mb.addMenu("主题")

        self._theme_actions: dict[str, QAction] = {}

        theme_group = QActionGroup(self)

        theme_group.setExclusive(True)

        theme_group.triggered.connect(self._on_theme_switched)

        for key in self._theme_manager.theme_names:

            display = self._theme_manager.get_theme(key).get("name", key)

            action = QAction(display, self, checkable=True)

            action.setData(key)

            if key == self._theme_manager.current_name:

                action.setChecked(True)

            theme_group.addAction(action)

            theme_menu.addAction(action)

            self._theme_actions[key] = action

        file_menu.addSeparator()

        layout_menu = mb.addMenu("布局")

        toggle_left_action = QAction("切换左侧面板", self)

        toggle_left_action.setShortcut("Ctrl+B")

        toggle_left_action.triggered.connect(self._toggle_left_panel)

        layout_menu.addAction(toggle_left_action)

        toggle_right_action = QAction("切换右侧面板", self)

        toggle_right_action.setShortcut("Ctrl+R")

        toggle_right_action.triggered.connect(self._toggle_right_panel)

        layout_menu.addAction(toggle_right_action)

        help_menu = mb.addMenu("帮助")

        help_action = QAction("使用说明", self)

        help_action.setShortcut("F1")

        help_action.triggered.connect(self._show_help)

        help_menu.addAction(help_action)

        from utils.gui.donation import append_donation_help_menu_action

        append_donation_help_menu_action(help_menu, self)


def open_calcpack(path: str | Path) -> None:

    """便捷函数：加载并显示 .calcpack 文件。"""

    QApplication.instance() or QApplication([])
    viewer = CalcPackViewer()

    viewer.load_calcpack(path)

    viewer.show()


def main() -> None:

    """CLI 入口。

    用法::

        python -m calc_framework.ui.viewer [path/游戏名.calcpack]

    """

    import sys

    app = QApplication(sys.argv)

    app.setApplicationName("计算包查看器")

    path = sys.argv[1] if len(sys.argv) > 1 else None

    viewer = CalcPackViewer(path)

    if path:

        viewer.load_calcpack(path)

    viewer.show()

    sys.exit(app.exec())


if __name__ == "__main__":

    main()
