# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""开发者工具主窗口 — 三页签：数据录入 / 布局编辑 / 主题与导出。



三页签数据共享：

- 数据录入 → 主题与导出：标准格式数据自动传递

- 布局编辑 → 主题与导出：DAG + layout 自动传递

- 切换到导出页签时自动同步

"""

from __future__ import annotations

import os
import sys

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

if _project_root not in sys.path:
    sys.path.insert(0, _project_root)


from calc_framework.config.manager import AdapterManager
from calc_framework.logging import get_logger
from calc_framework.ui.i18n import tr
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QStatusBar,
    QTabWidget,
)

from utils.gui.donation import open_donation_dialog
from utils.gui.help_dialog import HelpDialog, HelpSection
from utils.gui.help_loader import load_multi_category

_logger = get_logger(__name__)


from tools.designer.data_editor.panel import DataEditorPanel
from tools.designer.layout_editor.canvas import LayoutCanvasPanel
from tools.designer.theme_editor.panel import ThemePanel


class DesignerWindow(QMainWindow):
    """DesignerWindow 类。"""

    def __init__(self):
        super().__init__()

        self.setWindowTitle(tr("desktop.packDesigner.windowTitle"))

        self.resize(1200, 800)

        self._adapter_mgr = AdapterManager()

        self._tabs = QTabWidget()

        self.setCentralWidget(self._tabs)

        self._data_panel = DataEditorPanel()

        self._layout_panel = LayoutCanvasPanel()

        self._theme_panel = ThemePanel()

        self._theme_panel.export_requested.connect(self._on_export)

        self._tabs.addTab(self._data_panel, tr("desktop.packDesigner.tabData"))

        self._tabs.addTab(self._layout_panel, tr("desktop.packDesigner.tabLayout"))

        self._tabs.addTab(self._theme_panel, tr("desktop.packDesigner.tabTheme"))

        self._status = QStatusBar()

        self._status_label = QLabel(tr("common.ready"))

        self._status.addWidget(self._status_label)

        self.setStatusBar(self._status)

        self._setup_menu()

        self._tabs.currentChanged.connect(self._on_tab_changed)

        self._layout_panel.layout_changed.connect(self._on_layout_changed)

        self._update_status()

    def _setup_menu(self) -> None:
        """_setup_menu 实现。"""
        menubar = self.menuBar()

        help_menu = menubar.addMenu(tr("desktop.packDesigner.menuHelp"))

        help_action = QAction(tr("desktop.packDesigner.menuUsage"), self)

        help_action.setShortcut(QKeySequence("F1"))

        help_action.triggered.connect(self._show_help)

        help_menu.addAction(help_action)

        help_menu.addSeparator()

        donation_action = QAction(tr("desktop.packDesigner.menuDonate"), self)

        donation_action.triggered.connect(lambda: open_donation_dialog(self))

        help_menu.addAction(donation_action)

    def _show_help(self) -> None:
        """_show_help 实现。"""
        dialog = HelpDialog(
            self._build_designer_help,
            self,
            title=tr("desktop.packDesigner.helpTitle"),
        )

        dialog.exec()

    @staticmethod
    def _build_designer_help() -> list[HelpSection]:
        """_build_designer_help 实现。"""
        docs = load_multi_category(
            {
                tr("desktop.packDesigner.helpCatManual"): [
                    "GUI ③：配置包设计器",
                    "数据结构与文件格式",
                ],
            }
        )
        static_help = [
            HelpSection(
                category=tr("desktop.packDesigner.helpCatIntro"),
                title=tr("desktop.packDesigner.helpTitleOverview"),
                content=tr("desktop.packDesigner.helpBodyOverview"),
            ),
            HelpSection(
                category=tr("desktop.packDesigner.helpCatData"),
                title=tr("desktop.packDesigner.helpTitleDataTab"),
                content=tr("desktop.packDesigner.helpBodyDataTab"),
            ),
            HelpSection(
                category=tr("desktop.packDesigner.helpCatLayout"),
                title=tr("desktop.packDesigner.helpTitleLayoutTab"),
                content=tr("desktop.packDesigner.helpBodyLayoutTab"),
            ),
            HelpSection(
                category=tr("desktop.packDesigner.helpCatTheme"),
                title=tr("desktop.packDesigner.helpTitleThemeTab"),
                content=tr("desktop.packDesigner.helpBodyThemeTab"),
            ),
            HelpSection(
                category=tr("desktop.packDesigner.helpCatFaq"),
                title=tr("desktop.packDesigner.helpTitleFaq"),
                content=tr("desktop.packDesigner.helpBodyFaq"),
            ),
        ]
        return static_help + docs

    def _on_tab_changed(self, index: int) -> None:
        """_on_tab_changed 实现。"""
        if index == 0:
            adapter_name = self._layout_panel.get_adapter_name()

            if adapter_name:
                self._data_panel.sync_profile_from_adapter(adapter_name)

        elif index == 1:
            self._layout_panel.populate_adapters(self._adapter_mgr.names)

        elif index == 2:
            self._auto_sync_to_theme()

        self._update_status()

    def _on_layout_changed(self, layout_data: dict | None) -> None:
        """_on_layout_changed 实现。"""
        if layout_data:
            self._status_label.setText(tr("desktop.packDesigner.statusLayoutUpdated"))

    def _auto_sync_to_theme(self) -> None:
        """切到导出页签时自动同步其他面板的数据。"""

        data_files = self._data_panel.get_data_files()

        layout_data = self._layout_panel.get_layout_data()

        dag_service = self._layout_panel.get_dag_service()

        dag_dict = None

        if dag_service:
            try:
                from calc_framework.dag.serializer import dag_to_dict

                dag_dict = dag_to_dict(dag_service.dag)

            except Exception:
                _logger.warning("DAG 序列化失败，回退到适配器名")
                dag_dict = {"name": self._layout_panel.get_adapter_name(), "from_adapter": True}

        if any(data_files.values()):
            count_parts = [f"{k}={len(v)}" for k, v in data_files.items()]

            self._status_label.setText(
                tr(
                    "desktop.packDesigner.statusSynced",
                    counts=", ".join(count_parts),
                    layout=tr("desktop.packDesigner.hasLayout") if layout_data else tr("desktop.packDesigner.noLayout"),
                    dag=tr("desktop.packDesigner.hasDag") if dag_dict else tr("desktop.packDesigner.noDag"),
                )
            )

        self._theme_panel.set_shared_data(
            data_files=data_files,
            dag_data=dag_dict,
            layout_data=layout_data,
        )

        adapter_name = self._layout_panel.get_adapter_name()
        if adapter_name:
            try:
                pkg = self._adapter_mgr.load(adapter_name)
                self._theme_panel.set_adapter_meta(pkg.meta)
            except Exception:
                _logger.warning("加载适配器 %s 元数据失败", adapter_name)
                self._theme_panel.set_adapter_meta({})

        self._theme_panel._sync_from_shared()

    def _update_status(self) -> None:
        """_update_status 实现。"""
        tab_name = self._tabs.tabText(self._tabs.currentIndex())

        self._status_label.setText(tr("desktop.packDesigner.statusCurrentTab", tab=tab_name))

    def _on_export(self, path: str) -> None:
        """_on_export 实现。"""
        self._status_label.setText(tr("desktop.packDesigner.statusExported", path=path))


def main() -> None:
    """CLI 入口。"""
    app = QApplication(sys.argv)

    app.setApplicationName(tr("desktop.packDesigner.windowTitle"))

    win = DesignerWindow()

    win.showMaximized()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
